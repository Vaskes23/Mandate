# Repository Guidelines

## Project Structure & Module Organization
`src/main.ts` owns window lifecycle logic, while `src/preload.ts` is the sole bridge that should expose Node APIs to the renderer. UI work lives in `src/renderer/`, with `index.tsx` mounting `App.tsx`, feature components under `components/`, and shared styles in `styles/`. Build artifacts land in `dist/` and are the only files shipped by `electron-builder`.

## Build, Test, and Development Commands
- `npm run dev`: concurrently watches the main and renderer bundles, then boots Electron for live editing.
- `npm run watch:main` / `npm run watch:renderer`: isolate rebuilds when debugging compiler output.
- `npm run build`: runs `tsc -p tsconfig.main.json` and webpack production mode; treat passing this command as a gating check.
- `npm start`: executes a clean build and launches the packaged bits from `dist/`.
- `npm run package`: invokes `electron-builder` to produce dmg/zip installers (update `package.json#build` before adding new targets).

## Coding Style & Naming Conventions
Write strictly in TypeScript, return React functional components, and type every public prop. Follow the existing 2-space indentation, single quotes, and trailing semicolons. Components and hooks use `PascalCase`/`camelCase`; CSS classes stay kebab-case inside `src/renderer/styles/`.

## Testing Guidelines
There is no automated harness yet, so rely on manual QA: run `npm run dev`, verify both Agents and Editor tabs, drag the window, and resize down to tablet widths to hit the defined media queries. Before merging sizable changes, execute `npm run build` and launch the generated binary to confirm preload messaging and asset loading survive tree-shaking. Add future automated specs under `src/__tests__/` using the `ComponentName.spec.tsx` naming pattern.

## Commit & Pull Request Guidelines
Use short, imperative commit subjects similar to `git log` ("Add dedicated opacity slider"). Keep related changes in the same commit and document the rationale in the body when behavior shifts. PRs should link the relevant issue, summarize UI-facing updates, and include screenshots or recordings for visual adjustments. Note any manual test coverage in the description and ensure `npm run build` succeeds before requesting review.

## Security & Configuration Tips
Expose new IPC handlers only through `src/preload.ts`, validate channel names, and avoid enabling `nodeIntegration` in the renderer. Secrets or API keys must come from env vars consumed in the main process, never hard-coded in React. When adding native dependencies, confirm they are code-sign friendly before running `npm run package`.
