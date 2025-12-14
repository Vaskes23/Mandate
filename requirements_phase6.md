# Phase 6: Speed Improvements - Requirements

## Status: Complete

## Tasks

### Build Speed Improvements
- [x] Setup Webpack DevServer with hot reload
  - Added `devServer` configuration to webpack.renderer.config.js
  - New `dev:renderer` script using `webpack serve`
- [x] Add electron-reload for main process
  - Added electron-reload package
  - Main process auto-restarts when code changes (via ELECTRON_DEV env var)
- [x] Enable transpileOnly for faster TypeScript compilation
  - Added `transpileOnly: true` in development mode
  - Skips type checking during builds (use `npm run typecheck` separately)
  - Uses `eval-source-map` for faster dev builds

### Runtime Speed Improvements
- [x] Add frame downscaling config option
  - New `performance.frame_downscale` setting (0.0-1.0)
  - Scales down frames for faster detection, results scaled back up
- [x] Add frame skipping config option
  - New `performance.skip_frames` setting
  - Process every N+1 frames for faster throughput
- [x] Add ROI (Region of Interest) config option
  - New `performance.use_roi` and `performance.roi` settings
  - Only process specified region for faster detection
- [x] cv2.imshow already disabled in Electron mode
  - IPC mode (process_video_stream) never calls cv2.imshow
  - CLI mode controlled via `output.show_display` config

## Files Modified

| File | Changes |
|------|---------|
| `webpack.renderer.config.js` | Added devServer config, transpileOnly, env-based mode |
| `package.json` | Added webpack-dev-server, electron-reload, new scripts |
| `src/main.ts` | Added electron-reload for development hot reload |
| `scripts/config.json` | Added performance section with downscale/skip/ROI |
| `scripts/bird_tracker.py` | Implemented performance optimizations in _process_frames() |
| `scripts/tests/conftest.py` | Updated fixtures with performance config |

## New Config Options

```json
"performance": {
    "frame_downscale": 1.0,    // 0.5 = half resolution detection
    "skip_frames": 0,          // 1 = process every other frame
    "use_roi": false,          // Enable region of interest
    "roi": {
        "x": 0,
        "y": 0,
        "width": 0,
        "height": 0
    }
}
```

## New NPM Scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Full dev mode with hot reload |
| `npm run dev:renderer` | Webpack dev server only |
| `npm run dev:electron` | Electron with hot reload enabled |

## Performance Impact

| Optimization | Expected Impact |
|--------------|-----------------|
| transpileOnly | ~50% faster TypeScript compilation |
| webpack-dev-server | Incremental builds <1s |
| electron-reload | Auto-restart on main process changes |
| frame_downscale=0.5 | ~2x faster CV pipeline |
| skip_frames=1 | ~2x faster (half frame processing) |

## Run Tests

```bash
cd scripts
./venv/bin/python -m pytest tests/ -v
```

All 43 tests pass.
