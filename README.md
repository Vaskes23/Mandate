# CompVision - Flying Object Tracker

A desktop application for tracking flying objects (birds, drones, etc.) in video footage using computer vision. Built with Electron for the GUI and Python/OpenCV for real-time tracking algorithms.

## Overview

CompVision provides an intuitive interface for analyzing videos of flying objects, automatically detecting and tracking individual objects across frames. It's designed for computer vision students, researchers, and anyone studying flying object behavior.

**Key Capabilities:**
- Real-time object detection using background subtraction (MOG2)
- Multi-object tracking with Hungarian algorithm matching
- Temporal filtering to reduce false positives
- Exclusion zones for static obstacles
- Visual playback with tracking overlays
- Export tracking statistics and annotated videos

## Tech Stack

**Frontend:**
- **Electron** - Cross-platform desktop framework
- **TypeScript** - Type-safe JavaScript
- **React** - UI component library
- **Webpack** - Module bundler

**Backend:**
- **Python 3** - Processing engine
- **OpenCV (cv2)** - Computer vision library
- **NumPy** - Numerical computations
- **SciPy** - Hungarian algorithm for object matching

## Installation

### Prerequisites

- **Node.js** v16 or higher
- **Python 3.8+** with pip
- **npm** or **yarn**

### Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd CompVision
   ```

2. **Install Node dependencies:**
   ```bash
   npm install
   ```

3. **Create Python virtual environment:**
   ```bash
   cd scripts
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Verify installation:**
   ```bash
   python test_installation.py
   ```

## Usage

### GUI Mode (Recommended)

Run the Electron application:

```bash
npm run dev
```

**Features:**
- Load video files through the interface
- Real-time tracking visualization
- Scrub through frames to review tracking
- View statistics (total birds, max simultaneous, etc.)
- Visual highlighting of tracked objects

### CLI Mode

Process videos from the command line:

```bash
cd scripts
source venv/bin/activate  # Activate venv first
python bird_tracker.py input_video.mp4 [output_video.mp4]
```

**Options:**
- Provide only input path for analysis without output
- Provide both paths to generate annotated output video
- Tracking statistics printed to console

### Configuration

Edit `scripts/config.json` to customize tracking parameters:

```json
{
  "detection": {
    "min_area": 100,          // Minimum object area (pixels)
    "max_area": 5000,         // Maximum object area
    "history": 500,           // Background subtraction history
    "var_threshold": 16       // MOG2 variance threshold
  },
  "tracking": {
    "max_disappeared": 30,    // Frames before object considered lost
    "max_distance": 100       // Maximum matching distance
  }
}
```

## Project Structure

```
CompVision/
├── src/                      # Electron frontend
│   ├── main.ts              # Main process (IPC, window management)
│   ├── preload.ts           # Secure IPC bridge
│   ├── config/              # Application configuration
│   │   └── app.config.ts    # Platform-specific paths
│   └── renderer/            # React UI
│       ├── components/      # React components
│       │   ├── TitleBar.tsx
│       │   ├── Navigation.tsx
│       │   └── ArtPlaceholder.tsx  # Main tracking UI
│       └── styles/
│           └── global.css
├── scripts/                  # Python backend
│   ├── bird_tracker.py      # Main tracking system
│   ├── detector.py          # Object detection (MOG2)
│   ├── tracker.py           # Multi-object tracker
│   ├── config.json          # Tracking parameters
│   ├── requirements.txt     # Python dependencies
│   └── venv/                # Python virtual environment
├── dist/                     # Build output
└── package.json
```

## How It Works

1. **Background Subtraction:** MOG2 algorithm identifies moving objects against static background
2. **Morphological Operations:** Noise reduction through erosion/dilation
3. **Contour Detection:** Extract object boundaries and calculate centroids
4. **Multi-Object Tracking:** Hungarian algorithm matches detections across frames
5. **Temporal Filtering:** Probationary period reduces false positives
6. **Exclusion Zones:** Mask static obstacles (trees, buildings, etc.)

## Development

### Build for Production

```bash
npm run build
```

### Package Application

Create distributable packages (DMG for macOS, installer for Windows):

```bash
npm run package
```

Packaged apps include the Python scripts and will use the system Python or bundled interpreter.

### Linting & Type Checking

```bash
# TypeScript linting
npm run lint:ts

# Python linting
npm run lint:py

# Type checking
npm run typecheck
```

## Use Cases

- **Bird Behavior Analysis:** Study flight patterns and flock dynamics
- **Drone Monitoring:** Track multiple drones in airspace
- **Research:** Gather data on flying object trajectories
- **Computer Vision Education:** Learn tracking algorithms hands-on

## Troubleshooting

**Python process not starting:**
- Verify Python virtual environment is created: `scripts/venv/`
- Check Python dependencies: `cd scripts && pip install -r requirements.txt`
- Run test script: `python scripts/test_installation.py`

**Tracking quality issues:**
- Adjust detection parameters in `scripts/config.json`
- Use exclusion zones for static obstacles
- Ensure good video contrast (birds vs sky)

**Performance issues:**
- Reduce video resolution before processing
- Adjust `history` parameter in config
- Process in CLI mode for faster results

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes with clear commit messages
4. Submit a pull request

## License

MIT

## Credits

Built with Electron, React, TypeScript, Python, and OpenCV.