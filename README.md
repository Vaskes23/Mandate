# Glass-Morphic macOS App

A Python desktop application demonstrating authentic glass-morphic (translucent blur) effects on macOS using NSVisualEffectView.

## Features

- **Native macOS Blur**: Uses NSVisualEffectView for system-level glass effects
- **Interactive Controls**: Adjust material type and transparency in real-time
- **Clean Architecture**: Modular design that's easy to understand and extend
- **Fully Documented**: Clear docstrings and comments throughout

## Requirements

- macOS 10.14 (Mojave) or later
- Python 3.7+

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

   Dependencies:
   - PyQt5: GUI framework
   - pyobjc: Python-to-macOS bridge
   - pyobjc-framework-Cocoa: AppKit/NSVisualEffectView access

## Usage

### Running the Demo

```bash
python main.py
```

### Interacting with the Window

- **Drag to move**: Click and drag anywhere
- **Material selector**: Change blur style
- **Transparency slider**: Adjust window opacity
- **Close button**: Exit the application

### Creating Your Own Glass Window

```python
from PyQt5.QtWidgets import QApplication
from app.core.window import GlassMorphicWindow
from app.config import GlassConfig, MaterialType, AppearanceMode

# Create custom configuration
config = GlassConfig(
    material=MaterialType.SIDEBAR,
    window_alpha=0.95,
    appearance=AppearanceMode.VIBRANT_DARK,
)

# Create and show window
app = QApplication([])
window = GlassMorphicWindow(config)
window.resize(800, 600)
window.show()
app.exec_()
```

## Project Structure

```
CompVision/
├── main.py                      # Application entry point
├── requirements.txt             # Python dependencies
│
└── app/
    ├── config.py                # Glass effect configuration
    │
    ├── core/                    # Core functionality
    │   ├── window.py            # GlassMorphicWindow base class
    │   └── vibrancy.py          # NSVisualEffectView wrapper
    │
    ├── ui/                      # User interface
    │   └── main_window.py       # Demo window
    │
    └── utils/                   # Utilities
        └── macos_helpers.py     # Platform compatibility checks
```

## Architecture

### Core Components

1. **GlassMorphicWindow** (`app/core/window.py`)
   - Reusable base class for glass-morphic windows
   - Handles NSVisualEffectView setup and lifecycle
   - Provides drag-to-move functionality

2. **VibrancyHelper** (`app/core/vibrancy.py`)
   - Python wrapper around NSVisualEffectView
   - Manages PyObjC bridge to macOS APIs
   - Type-safe interface to AppKit

3. **GlassConfig** (`app/config.py`)
   - Configuration class for glass effects
   - Enums for material types, blending modes, appearance
   - Easy to modify and extend

### How It Works

1. PyQt5 creates a frameless, transparent Qt window
2. VibrancyHelper creates an NSVisualEffectView (native macOS blur)
3. The blur view is positioned below all Qt widgets
4. Qt's transparent background allows the blur to show through
5. The result: authentic glass-morphic effects!

## Configuration Options

### Material Types

```python
MaterialType.SIDEBAR           # Standard sidebar (default)
MaterialType.MENU              # Menu background
MaterialType.POPOVER           # Popover style
MaterialType.HUD_WINDOW        # Heads-up display
MaterialType.CONTENT_BACKGROUND # Content area
# ... and more
```

### Blending Modes

```python
BlendingMode.BEHIND_WINDOW  # Blur desktop behind window
BlendingMode.WITHIN_WINDOW  # Blur window contents
```

### Appearance Modes

```python
AppearanceMode.VIBRANT_DARK  # Dark mode (recommended)
AppearanceMode.VIBRANT_LIGHT # Light mode
```

### Example Configuration

```python
from app.config import GlassConfig, MaterialType, AppearanceMode

config = GlassConfig(
    material=MaterialType.HUD_WINDOW,
    window_alpha=0.9,
    appearance=AppearanceMode.VIBRANT_DARK,
    emphasized=False
)
```

## Extending the Application

### Creating Custom Windows

Subclass `GlassMorphicWindow` to create your own glass-morphic windows:

```python
from app.core.window import GlassMorphicWindow

class MyWindow(GlassMorphicWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My Glass Window")
        # Add your UI components here
```

### Changing Glass Effect at Runtime

```python
from app.config import GlassConfig, MaterialType

new_config = GlassConfig(material=MaterialType.MENU)
window.update_glass_config(new_config)
```

## Troubleshooting

**"AppKit is not available"**
- Install pyobjc-framework-Cocoa: `pip install pyobjc-framework-Cocoa`

**"This application requires macOS 10.14 or later"**
- Upgrade macOS to Mojave (10.14) or newer

**Window appears but no blur effect**
- Ensure window is visible (not minimized)
- Check that you're running on macOS 10.14+

## License

This project is provided as-is for educational purposes.

## Technical Details

- **PyQt5**: Cross-platform GUI framework
- **PyObjC**: Python-to-Objective-C bridge
- **NSVisualEffectView**: macOS native blur component
- **AppKit**: macOS application framework

The blur effect is created entirely by macOS using NSVisualEffectView, ensuring authentic system-level appearance that matches other macOS applications.
