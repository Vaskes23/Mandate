# Bird Tracking System

A CPU-optimized, real-time bird detection and tracking system using classical computer vision techniques.

## Overview

This system detects and tracks small birds flying against a blue sky background using:
- **MOG2 Background Subtraction** for motion detection
- **Morphological Operations** for noise reduction
- **Centroid Tracking** with Hungarian algorithm for optimal ID assignment
- **Occlusion Handling** via disappeared counter mechanism

## Installation

### 1. Install Python Dependencies

```bash
cd scripts
pip install -r requirements.txt
```

Required packages:
- `opencv-python>=4.8.0` - Computer vision library
- `numpy>=1.24.0` - Numerical operations
- `scipy>=1.11.0` - Hungarian algorithm implementation

### 2. Make Script Executable (Optional)

```bash
chmod +x bird_tracker.py
```

## Usage

### CLI Mode (Standalone)

Run the tracker directly from the command line:

```bash
# Basic usage
python bird_tracker.py --input ../birdsExample.mp4 --output output_tracked.mp4

# With custom config
python bird_tracker.py --input video.mp4 --output tracked.mp4 --config my_config.json
```

**Arguments:**
- `--input, -i`: Input video file path (required)
- `--output, -o`: Output video file path (optional, defaults to display only)
- `--config, -c`: Configuration file path (optional, defaults to config.json)

**Controls:**
- Press `q` to quit the tracking window

### IPC Mode (Electron Integration)

The system can be controlled from the Electron UI:

1. Start the Electron app:
   ```bash
   cd ..
   npm run dev
   ```

2. Use the BirdTracker component to control tracking
3. Python process runs in background, communicating via JSON over stdin/stdout

### Programmatic Usage

You can also import and use the modules in your own Python scripts:

```python
from detector import BirdDetector
from tracker import CentroidTracker
import cv2
import json

# Load config
with open('config.json') as f:
    config = json.load(f)

# Initialize detector and tracker
detector = BirdDetector(config)
tracker = CentroidTracker(
    max_disappeared=config['tracking']['max_disappeared'],
    max_distance=config['tracking']['max_distance']
)

# Process frames
cap = cv2.VideoCapture('video.mp4')
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Detect
    bounding_boxes, mask = detector.detect(frame)
    centroids = detector.get_centroids(bounding_boxes)

    # Track
    objects = tracker.update(centroids)

    # Use objects dict...
```

## Configuration

All tunable parameters are in `config.json`:

### Detection Parameters

```json
{
  "detection": {
    "min_contour_area": 20,        // Minimum bird size in pixels
    "max_contour_area": 500,       // Maximum bird size in pixels
    "mog2_history": 500,           // Background model history
    "mog2_var_threshold": 16,      // Detection sensitivity
    "blur_kernel_size": 5,         // Gaussian blur kernel
    "morph_kernel_size": 3,        // Morphology kernel size
    "morph_iterations": 2          // Morphology iterations
  }
}
```

### Tracking Parameters

```json
{
  "tracking": {
    "max_disappeared": 30,         // Frames before deregistration
    "max_distance": 100            // Max pixel distance for matching
  }
}
```

### Visualization Parameters

```json
{
  "visualization": {
    "show_trails": false,          // Show bird trajectories
    "trail_length": 30,            // Trail history length
    "box_color": [0, 255, 0],      // Bounding box color (BGR)
    "text_color": [255, 255, 255], // Text color (BGR)
    "font_scale": 0.6,             // Font size
    "box_thickness": 2             // Box line thickness
  }
}
```

## Parameter Tuning Guide

### For Small Birds (Distant)

**Problem:** Birds are too small and not being detected

**Solution:**
```json
{
  "detection": {
    "min_contour_area": 10,        // Decrease minimum area
    "mog2_var_threshold": 12,      // Increase sensitivity
    "morph_kernel_size": 2         // Smaller morphology kernel
  }
}
```

### For Large Birds (Close)

**Problem:** Bird detection boxes are fragmented

**Solution:**
```json
{
  "detection": {
    "max_contour_area": 1000,      // Increase maximum area
    "morph_kernel_size": 5,        // Larger kernel for merging
    "morph_iterations": 3          // More iterations
  }
}
```

### For Noisy Background

**Problem:** Too many false detections from noise

**Solution:**
```json
{
  "detection": {
    "min_contour_area": 30,        // Increase minimum area
    "mog2_var_threshold": 20,      // Decrease sensitivity
    "blur_kernel_size": 7,         // Stronger blur
    "morph_iterations": 3          // More cleanup
  }
}
```

### For Fast-Moving Birds

**Problem:** Birds lose their IDs frequently

**Solution:**
```json
{
  "tracking": {
    "max_disappeared": 50,         // Longer grace period
    "max_distance": 150            // Larger matching distance
  }
}
```

### For Slow-Moving Birds

**Problem:** Too many IDs being kept alive

**Solution:**
```json
{
  "tracking": {
    "max_disappeared": 20,         // Shorter grace period
    "max_distance": 75             // Stricter matching
  }
}
```

### For Overlapping Birds (Occlusion)

**Problem:** Birds crossing paths cause ID swaps

**Current Handling:**
- Disappeared counter prevents immediate deregistration
- Hungarian algorithm finds optimal assignment
- Max distance threshold prevents cross-screen jumps

**Limitations:**
When two birds completely overlap:
1. Detector sees single contour
2. Tracker marks one bird as disappeared
3. After separation, closest bird gets reused ID
4. Other bird may get new ID

**Improvement Options:**
1. **Kalman Filtering**: Predict bird positions during occlusion
2. **Appearance Features**: Use color histograms or HOG features
3. **Deep SORT**: Use deep learning features (requires GPU)

**Practical Tuning:**
```json
{
  "tracking": {
    "max_disappeared": 40,         // Higher tolerance for occlusion
    "max_distance": 120            // Allow larger jumps
  }
}
```

## Architecture

### Module Structure

```
scripts/
├── bird_tracker.py    # Main entry point, video processing
├── detector.py        # Detection pipeline (MOG2, morphology)
├── tracker.py         # Centroid tracking with Hungarian algorithm
└── config.json        # Tunable parameters
```

### Detection Pipeline

1. **Preprocessing**: Gaussian blur (5×5) for noise reduction
2. **Background Subtraction**: MOG2 algorithm isolates moving objects
3. **Morphological Operations**:
   - Opening (erosion → dilation): Removes small noise
   - Closing (dilation → erosion): Fills small gaps
4. **Contour Detection**: Find connected components
5. **Area Filtering**: Keep only bird-sized contours (20-500 px²)

### Tracking Algorithm

1. **Centroid Calculation**: Extract (cx, cy) from bounding boxes
2. **Distance Matrix**: Compute Euclidean distances between existing IDs and new detections
3. **Hungarian Algorithm**: Optimal bipartite matching via `scipy.optimize.linear_sum_assignment`
4. **ID Assignment**:
   - Matched (distance < threshold): Update position
   - Unmatched existing: Increment disappeared counter
   - Unmatched new: Register new ID
5. **Deregistration**: Remove IDs after max_disappeared frames

### Performance Characteristics

**Speed:**
- ~30-60 FPS on modern CPU (depends on resolution and bird count)
- MOG2 is highly optimized in OpenCV
- No GPU required

**Accuracy:**
- High precision for isolated birds
- Good recall for birds >20 pixels
- Handles temporary occlusion well
- May struggle with prolonged overlap

**Memory:**
- Minimal overhead (~50 MB typical)
- Scales linearly with bird count
- History-based background model

## Troubleshooting

### Issue: No birds detected

**Possible Causes:**
1. Birds too small → Decrease `min_contour_area`
2. Low contrast → Adjust `mog2_var_threshold`
3. Wrong video path → Check file exists

**Debug:**
```python
# Add visualization of intermediate steps
cv2.imshow('Foreground Mask', mask)
cv2.imshow('Cleaned Mask', cleaned_mask)
```

### Issue: Too many false detections

**Possible Causes:**
1. Noise in video → Increase `blur_kernel_size`
2. Camera shake → Increase `min_contour_area`
3. Clouds moving → Adjust `mog2_history`

**Solution:** Increase minimum area threshold

### Issue: Birds lose IDs frequently

**Possible Causes:**
1. Fast movement → Increase `max_distance`
2. Brief occlusion → Increase `max_disappeared`
3. Detection gaps → Tune detection parameters

**Solution:** Increase tracking tolerances

### Issue: Python script not found

**Error:** `FileNotFoundError: bird_tracker.py`

**Solution:**
```bash
# Ensure correct working directory
cd scripts
python bird_tracker.py --input ../birdsExample.mp4
```

### Issue: Module import errors

**Error:** `ModuleNotFoundError: No module named 'cv2'`

**Solution:**
```bash
pip install opencv-python numpy scipy
```

### Issue: IPC mode hangs

**Possible Causes:**
1. Python not in PATH
2. JSON parsing errors
3. Process communication issues

**Debug:**
```bash
# Test Python script directly first
python bird_tracker.py --input ../birdsExample.mp4
```

## Performance Optimization

### For Real-Time Processing

1. **Reduce Resolution:**
   ```python
   frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
   ```

2. **Disable Visualization:**
   ```json
   {
     "output": {
       "show_display": false,
       "save_video": false
     }
   }
   ```

3. **Reduce Morphology Iterations:**
   ```json
   {
     "detection": {
       "morph_iterations": 1
     }
   }
   ```

### For Accuracy

1. **Increase MOG2 History:**
   ```json
   {
     "detection": {
       "mog2_history": 1000
     }
   }
   ```

2. **Finer Morphology:**
   ```json
   {
     "detection": {
       "morph_iterations": 3,
       "morph_kernel_size": 5
     }
   }
   ```

3. **Enable Trails:**
   ```json
   {
     "visualization": {
       "show_trails": true,
       "trail_length": 50
     }
   }
   ```

## Limitations

1. **Single-Class Detection**: Only detects moving objects (assumes birds)
2. **Background Dependency**: Requires relatively static background
3. **Occlusion Handling**: Limited during prolonged overlap
4. **Color-Agnostic**: Doesn't use color information
5. **2D Tracking**: No depth estimation

## Future Enhancements

1. **Kalman Filtering**: Predict positions during occlusion
2. **Appearance Modeling**: Use color histograms or texture features
3. **Multi-Scale Detection**: Handle varying bird sizes better
4. **Adaptive Thresholding**: Auto-tune parameters per video
5. **3D Trajectory Estimation**: Stereo vision or depth from motion

## Technical Details

### Hungarian Algorithm

The Hungarian algorithm solves the assignment problem in O(n³) time:
- Given: Distance matrix D[i,j] between existing objects and new detections
- Find: Optimal assignment minimizing total distance
- Implementation: `scipy.optimize.linear_sum_assignment(D)`

### MOG2 Background Subtraction

Gaussian Mixture Model (GMM) approach:
- Each pixel modeled as mixture of Gaussians
- Background: Persistent, low-variance Gaussians
- Foreground: Newly appearing or high-variance
- Adaptive: Updates model over time

### Morphological Operations

- **Opening**: Removes small bright spots (noise)
- **Closing**: Fills small dark holes (gaps in birds)
- **Kernel**: Structuring element (ellipse for birds)

## Citation

If you use this system in research, please cite:

```
@software{bird_tracking_system,
  title={Bird Tracking System: CPU-Optimized Real-Time Detection},
  author={Your Name},
  year={2025},
  url={https://github.com/yourusername/bird-tracker}
}
```

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
1. Check this README first
2. Review config.json parameters
3. Test with sample video
4. Open GitHub issue with:
   - Video characteristics (resolution, FPS, bird size)
   - Config parameters used
   - Error messages or unexpected behavior
   - System info (OS, Python version, OpenCV version)
