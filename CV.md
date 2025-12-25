# Computer Vision Enhancement Analysis
## Small Bird Detection & Multi-Object Tracking Optimization

**Document Version:** 1.0
**Date:** December 15, 2025
**Subject:** Improving detection and tracking of small birds without GPU acceleration
**Reference Video:** `birdsExample.mp4`

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current System Analysis](#current-system-analysis)
3. [Identified Challenges](#identified-challenges)
4. [Proposed Improvements](#proposed-improvements)
5. [Static Object Filtering Strategies](#static-object-filtering-strategies)
6. [Implementation Priority Matrix](#implementation-priority-matrix)
7. [Configuration Recommendations](#configuration-recommendations)
8. [Appendix: Technical References](#appendix-technical-references)

---

## Executive Summary

This document analyzes the current CompVision bird detection and tracking system and proposes CPU-optimized enhancements for improving detection of small, fast-moving birds while eliminating false positives from static objects (lamp posts, trees, buildings).

**Key Findings:**
- Current MOG2 background subtraction is well-suited for CPU processing but needs parameter tuning for small objects
- Temporal filtering effectively reduces false positives but may filter out legitimate fast-moving birds
- Static object filtering via exclusion zones is manual and requires per-video configuration
- Several CPU-efficient algorithmic improvements can significantly enhance detection accuracy

---

## Current System Analysis

### Detection Pipeline
**File:** `scripts/detector.py`

| Stage | Current Implementation | Notes |
|-------|----------------------|-------|
| Preprocessing | Gaussian blur (5x5 kernel) | Good for noise reduction |
| Background Subtraction | MOG2 (history=500, varThreshold=25) | CPU-efficient, adaptive |
| Morphology | Opening + Closing (3x3 ellipse, 2 iterations) | Removes small noise |
| Contour Detection | `cv2.findContours` with `RETR_EXTERNAL` | Standard approach |
| Area Filtering | min=0.1px, max=500px | Very permissive min threshold |
| Spatial Filtering | Horizon at 70% frame height | Filters ground detections |
| Exclusion Zones | Rectangle at (910, 180, 100x900) | Manual lamp post masking |

### Tracking Pipeline
**File:** `scripts/tracker.py`

| Component | Current Implementation | Notes |
|-----------|----------------------|-------|
| Algorithm | Centroid + Hungarian (scipy) | Optimal assignment matching |
| ID Persistence | max_disappeared=40 frames | ~1.3 seconds at 30fps |
| Distance Threshold | max_distance=120 pixels | May be too large for small birds |
| Temporal Validation | 15 frames, 50px movement | Probationary tracking |
| Trajectory Storage | 30 points per object | Used for visualization |

### Current Configuration
**File:** `scripts/config.json`

```json
{
  "detection": {
    "min_contour_area": 0.1,      // ISSUE: Too small for real birds
    "max_contour_area": 500,
    "mog2_history": 500,
    "mog2_var_threshold": 25,     // ISSUE: May miss subtle movements
    "blur_kernel_size": 5,
    "morph_kernel_size": 3,
    "morph_iterations": 2
  },
  "tracking": {
    "max_disappeared": 40,
    "max_distance": 120           // ISSUE: May cause ID merging
  }
}
```

---

## Identified Challenges

### Challenge 1: Small Bird Detection
**Problem:** Birds in the video appear as very small objects (5-30 pixels), making them difficult to distinguish from sensor noise.

**Current Behavior:**
- `min_contour_area=0.1` is too permissive, accepting single-pixel noise
- Morphological operations (3x3 kernel, 2 iterations) may eliminate legitimate small birds
- Gaussian blur (5x5) may blur out small objects entirely

**Evidence from Screenshot Analysis:**
- Birds appear as dark specks against light blue sky
- Estimated bird size: 3-15 pixels diameter
- High bird density creates tracking challenges

### Challenge 2: Static Object False Positives
**Problem:** Lamp posts, trees, and buildings trigger false detections when lighting changes or camera micro-movements occur.

**Current Mitigation:**
- Single hardcoded exclusion zone for lamp post
- Horizon filter removes ground-level detections
- Temporal filter requires movement to confirm

**Limitations:**
- Manual exclusion zone configuration per video
- Trees with moving leaves bypass temporal filter
- Edge pixels of static objects still trigger detections

### Challenge 3: Multi-Object Tracking Accuracy
**Problem:** When many birds fly close together, ID switching and merging occurs.

**Current Behavior:**
- Hungarian algorithm provides optimal matching
- `max_distance=120` may be too large for nearby birds
- No velocity prediction - relies on frame-to-frame proximity
- No appearance model for re-identification

### Challenge 4: CPU Performance Constraints
**Problem:** All processing must run efficiently on CPU without GPU acceleration.

**Current Performance Characteristics:**
- MOG2 is already CPU-optimized
- scipy's `linear_sum_assignment` is O(n³) but efficient for <100 objects
- No deep learning inference overhead
- Estimated: 15-30 FPS on modern CPU

---

## Proposed Improvements

### Improvement 1: Frame Differencing Enhancement
**Theory:** Combine MOG2 with simple frame differencing to better detect fast-moving small objects.

**Algorithm:**
```
1. Compute frame difference: diff = |frame[t] - frame[t-1]|
2. Threshold difference to create motion mask
3. AND motion mask with MOG2 foreground mask
4. Result: Objects that are BOTH moving AND foreground
```

**Benefits:**
- Frame differencing excels at detecting ANY movement (even 1 pixel)
- MOG2 handles gradual lighting changes
- Combination reduces false positives from static objects
- CPU cost: minimal (one extra subtraction + threshold)

**Validation Against Existing Code:**
- Current `detector.py` only uses MOG2 (`self.bg_subtractor.apply()`)
- Frame differencing can be added before morphological operations
- No structural changes needed to tracking pipeline

### Improvement 2: Adaptive Contour Area Thresholding
**Theory:** Use dynamic area thresholds based on frame statistics rather than fixed values.

**Algorithm:**
```
1. Collect all contour areas in frame
2. Calculate median area (robust to outliers)
3. Set min_area = 0.3 × median (capture smaller birds)
4. Set max_area = 10 × median (filter large blobs)
5. Apply hysteresis: smooth threshold changes over time
```

**Benefits:**
- Adapts to camera zoom level automatically
- Handles varying bird distances from camera
- Self-calibrating for different video conditions

**Validation Against Existing Code:**
- Current fixed thresholds in `filter_contours()` method (detector.py:177-207)
- Can be extended with per-frame area statistics
- Requires adding a calibration window (first N frames)

### Improvement 3: Velocity-Based Prediction (Kalman Lite)
**Theory:** Use simple velocity estimation to predict object positions, improving tracking through occlusions.

**Algorithm:**
```
For each tracked object:
  1. velocity = position[t] - position[t-1]
  2. predicted_position = position[t] + velocity
  3. Use predicted_position in distance calculation
  4. Accept matches within prediction_radius instead of fixed distance
```

**Benefits:**
- Handles fast-moving birds that would exceed `max_distance`
- Reduces ID switching when birds cross paths
- CPU-efficient (just addition/subtraction)
- Better than full Kalman filter for this use case

**Validation Against Existing Code:**
- Current `_compute_distance_matrix()` uses raw centroid positions
- Trajectory history already stored in `self.trajectories` OrderedDict
- Velocity can be computed from last 2 trajectory points

### Improvement 4: Persistence-Based Static Object Detection
**Theory:** Objects that remain stationary for extended periods are likely static objects (lamp, tree edges) and should be automatically masked.

**Algorithm:**
```
1. Maintain "persistence map" (same size as frame, single channel)
2. For each foreground pixel: persistence[y,x] += 1
3. For each background pixel: persistence[y,x] = max(0, persistence[y,x] - decay_rate)
4. Pixels exceeding persistence_threshold are classified as static
5. Mask out high-persistence regions from detection
```

**Benefits:**
- Automatically learns static object locations
- No manual exclusion zone configuration needed
- Adapts if camera moves or objects are added/removed
- Handles partial static objects (tree branches)

**Validation Against Existing Code:**
- Current exclusion zones are manual (config.json)
- Persistence map can replace or augment exclusion zones
- Requires adding frame-persistent state to BirdDetector class

### Improvement 5: Multi-Scale Detection
**Theory:** Process frame at multiple resolutions to detect birds at different distances/sizes.

**Algorithm:**
```
scales = [1.0, 0.75, 0.5]  // Original, 75%, 50% resolution
detections = []

for scale in scales:
    resized = resize(frame, scale)
    scale_detections = detect(resized)

    // Convert coordinates back to original scale
    for det in scale_detections:
        det.x /= scale
        det.y /= scale
        det.w /= scale
        det.h /= scale
        detections.append(det)

// Merge overlapping detections with NMS
final_detections = non_maximum_suppression(detections)
```

**Benefits:**
- Detects small distant birds at higher resolution
- Detects larger nearby birds at lower resolution (faster)
- Non-Maximum Suppression (NMS) eliminates duplicates

**Validation Against Existing Code:**
- Current detection is single-scale only
- Would require modifying `detect()` method in detector.py
- NMS can reuse existing contour filtering logic

### Improvement 6: Contrast Enhancement for Small Objects
**Theory:** Enhance local contrast to make small dark birds more visible against blue sky.

**Algorithm:**
```
1. Convert frame to LAB color space
2. Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to L channel
3. Merge back to BGR
4. Proceed with normal detection pipeline
```

**Benefits:**
- Small birds become more distinguishable from sky
- CLAHE is CPU-efficient and prevents over-amplification
- Works well with blue sky backgrounds
- Already available in OpenCV (`cv2.createCLAHE`)

**Validation Against Existing Code:**
- Current preprocessing only applies Gaussian blur
- CLAHE can be inserted in `preprocess_frame()` method
- No changes needed to downstream pipeline

### Improvement 7: Optical Flow for Motion Validation
**Theory:** Use sparse optical flow (Lucas-Kanade) to validate that detected objects exhibit coherent motion.

**Algorithm:**
```
1. Track corner points in detected bounding boxes using optical flow
2. Objects with consistent flow vectors are confirmed as moving
3. Objects with zero/random flow are likely static or noise
4. Use flow magnitude to estimate velocity for tracking
```

**Benefits:**
- Directly measures actual motion, not just appearance change
- Lucas-Kanade is CPU-efficient for sparse point tracking
- Can distinguish swaying branches (random flow) from flying birds (coherent flow)
- Provides velocity estimation for improved tracking

**Validation Against Existing Code:**
- Current system has no optical flow
- Would complement temporal filtering in tracker.py
- Can provide velocity for Improvement #3

---

## Static Object Filtering Strategies

### Strategy A: Automatic Exclusion Zone Learning
**Concept:** Learn exclusion zones automatically during first N frames.

**Implementation:**
```python
# During calibration phase (first 100 frames):
1. Accumulate foreground mask: cumulative_fg += current_fg_mask
2. After calibration: static_mask = cumulative_fg > (N * 0.8)
3. Apply static_mask as permanent exclusion zone
4. Optionally: save learned mask to JSON for reuse
```

**Pros:**
- Fully automatic, no manual configuration
- Captures exact shape of static objects (not just rectangles)
- Can be triggered by user command to "recalibrate"

**Cons:**
- Requires stable camera during calibration
- Moving objects during calibration may be masked
- 3-4 second calibration delay at startup

### Strategy B: Color-Based Sky Segmentation
**Concept:** Detect sky region by color and only search for birds within sky area.

**Implementation:**
```python
# Sky is typically blue (high H in HSV, low saturation)
hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
sky_mask = cv2.inRange(hsv, (90, 20, 100), (130, 255, 255))  # Blue range

# Morphological cleanup
sky_mask = cv2.morphologyEx(sky_mask, cv2.MORPH_CLOSE, kernel)

# Only detect within sky region
detection_mask = fg_mask & sky_mask
```

**Pros:**
- Inherently excludes buildings, trees, lamp posts (not blue)
- Works without calibration period
- Adapts to different lighting conditions

**Cons:**
- Fails at sunset/sunrise when sky isn't blue
- May miss birds flying against non-blue backgrounds
- Requires tuning HSV thresholds per video

### Strategy C: Edge Density Filtering
**Concept:** Static objects have stable edges; moving birds don't contribute to edge accumulation.

**Implementation:**
```python
# Accumulate edges over time
edges = cv2.Canny(frame, 50, 150)
edge_accumulator = 0.95 * edge_accumulator + 0.05 * edges

# High-accumulation areas are static structures
static_edge_mask = edge_accumulator > threshold

# Dilate to cover entire static objects
static_mask = cv2.dilate(static_edge_mask, kernel, iterations=5)
```

**Pros:**
- Detects structural edges (buildings, lamp posts) reliably
- Doesn't require specific sky color
- Self-updating as static objects change

**Cons:**
- May mask edge of frame where birds fly past
- Requires tuning accumulator decay rate
- Birds flying along edges may not be detected

### Strategy D: Temporal Variance Analysis
**Concept:** Pixels with low temporal variance are static; high variance indicates motion.

**Implementation:**
```python
# Maintain running variance estimate
frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
running_mean = alpha * running_mean + (1 - alpha) * frame_gray
running_var = alpha * running_var + (1 - alpha) * (frame_gray - running_mean)**2

# Low variance = static
static_mask = running_var < variance_threshold
```

**Pros:**
- Mathematically robust
- Handles gradual lighting changes well
- Automatically adapts to scene

**Cons:**
- Trees with moving leaves have high variance (good!)
- Very slow-moving clouds might trigger false positives
- Requires several seconds to stabilize

---

## Implementation Priority Matrix

| Improvement | Impact | CPU Cost | Complexity | Priority |
|-------------|--------|----------|------------|----------|
| 1. Frame Differencing | High | Low | Low | **P1** |
| 4. Persistence-Based Static Detection | High | Low | Medium | **P1** |
| 6. CLAHE Contrast Enhancement | Medium | Low | Low | **P2** |
| 2. Adaptive Area Thresholds | Medium | Low | Medium | **P2** |
| 3. Velocity Prediction | High | Low | Medium | **P3** |
| 7. Optical Flow Validation | High | Medium | High | **P3** |
| 5. Multi-Scale Detection | Medium | High | High | **P4** |

### Recommended Implementation Order

**Phase 1: Quick Wins (Low effort, high impact)**
1. Implement frame differencing enhancement
2. Add CLAHE contrast preprocessing
3. Tune existing configuration parameters (see below)

**Phase 2: Static Object Handling (Medium effort)**
4. Implement persistence-based static detection
5. Add automatic exclusion zone learning
6. Consider color-based sky segmentation

**Phase 3: Tracking Enhancement (Medium-High effort)**
7. Add velocity prediction to tracker
8. Implement optical flow validation
9. Reduce `max_distance` for tighter matching

**Phase 4: Advanced Detection (High effort, optional)**
10. Multi-scale detection pipeline
11. Adaptive contour thresholding
12. Full Kalman filter integration

---

## Configuration Recommendations

### Optimized config.json for Small Bird Detection

```json
{
  "detection": {
    "min_contour_area": 4,           // Changed from 0.1 - minimum viable bird size
    "max_contour_area": 300,         // Reduced from 500 - birds are small
    "mog2_history": 300,             // Reduced from 500 - faster adaptation
    "mog2_var_threshold": 16,        // Reduced from 25 - more sensitive
    "blur_kernel_size": 3,           // Reduced from 5 - preserve small details
    "morph_kernel_size": 2,          // Reduced from 3 - don't erode small birds
    "morph_iterations": 1            // Reduced from 2 - gentler cleanup
  },
  "tracking": {
    "max_disappeared": 25,           // Reduced from 40 - faster cleanup
    "max_distance": 60               // Reduced from 120 - tighter matching
  },
  "spatial_filter": {
    "enabled": true,
    "horizon_line_percent": 0.85     // Increased from 0.70 - less restrictive
  },
  "temporal_filter": {
    "enabled": true,
    "min_confirm_frames": 8,         // Reduced from 15 - faster confirmation
    "min_move_distance": 25.0        // Reduced from 50 - small birds move less px
  },
  "exclusion_zones": {
    "enabled": true,
    "zones": [
      {"x": 880, "y": 0, "width": 160, "height": 1080}  // Wider lamp zone
    ],
    "draw_debug": false
  }
}
```

### Parameter Tuning Guidelines

| Parameter | For More Detections | For Fewer False Positives |
|-----------|---------------------|---------------------------|
| `mog2_var_threshold` | Decrease (8-16) | Increase (25-40) |
| `min_contour_area` | Decrease (2-4) | Increase (10-20) |
| `max_contour_area` | Increase (400-600) | Decrease (150-250) |
| `blur_kernel_size` | Decrease (3) | Increase (7-9) |
| `morph_iterations` | Decrease (1) | Increase (2-3) |
| `min_confirm_frames` | Decrease (5-8) | Increase (20-30) |
| `max_distance` | Increase (100-150) | Decrease (40-60) |

---

## Appendix: Technical References

### A. Background Subtraction Algorithms (CPU-Friendly)

| Algorithm | OpenCV Function | Pros | Cons |
|-----------|-----------------|------|------|
| MOG2 | `createBackgroundSubtractorMOG2` | Adaptive, handles gradual changes | Slow to adapt to quick changes |
| KNN | `createBackgroundSubtractorKNN` | Good for complex backgrounds | Higher CPU cost |
| Frame Difference | Manual implementation | Fast, catches all motion | High false positive rate |
| Running Average | Manual implementation | Simple, predictable | Poor dynamic range |

### B. Object Tracking Algorithms (CPU-Friendly)

| Algorithm | Library | Complexity | Best For |
|-----------|---------|------------|----------|
| Centroid + Hungarian | scipy | O(n³) | <100 objects |
| SORT | Custom | O(n²) | Real-time multi-object |
| IOU Tracker | Custom | O(n²) | Overlapping objects |
| Kalman Filter | OpenCV/filterpy | O(n) per object | Predicting motion |

### C. Small Object Detection Techniques

1. **Super-Resolution Preprocessing**: Upscale frame before detection (2x-4x)
   - Pro: More pixels per bird
   - Con: 4-16x CPU cost increase

2. **Attention Mechanisms**: Focus processing on likely bird regions
   - Pro: Efficient use of CPU cycles
   - Con: May miss unexpected bird locations

3. **Temporal Stacking**: Stack multiple frames to enhance SNR
   - Pro: Noise averages out, signal accumulates
   - Con: Motion blur for moving objects

4. **Difference of Gaussians (DoG)**: Blob detection at multiple scales
   - Pro: Scale-invariant detection
   - Con: May detect round noise as blobs

### D. Files to Modify for Each Improvement

| Improvement | Primary File | Secondary Files |
|-------------|--------------|-----------------|
| Frame Differencing | `detector.py:91-103` | - |
| Adaptive Thresholds | `detector.py:177-207` | `config.json` |
| Velocity Prediction | `tracker.py:361-379` | `tracker.py:172-293` |
| Persistence Detection | `detector.py` (new method) | `config.json` |
| Multi-Scale | `detector.py:209-242` | `bird_tracker.py` |
| CLAHE Enhancement | `detector.py:91-103` | - |
| Optical Flow | `detector.py` (new method) | `tracker.py` |

---

## Document Validation

### Cross-Reference with Existing Code

- [x] Detection pipeline matches `detector.py` structure
- [x] Tracking algorithm matches `tracker.py` implementation
- [x] Configuration parameters verified against `config.json`
- [x] Proposed changes compatible with existing architecture
- [x] All file paths verified as correct
- [x] No GPU dependencies in proposed solutions

### Compatibility Notes

- All proposed improvements use OpenCV functions available on CPU
- scipy dependency already present for Hungarian algorithm
- No additional library installations required
- Memory footprint increase: minimal (<50MB for persistence maps)
- Expected CPU increase: 5-15% for Phase 1 improvements

---

## Outside-the-Box Innovations

### Innovation 1: Flock Behavior Prediction
**Concept:** Birds flying together exhibit correlated motion patterns. Use this to predict where birds will be.

**Theory:**
When birds flock, they follow three rules (Reynolds' Boids model):
1. **Separation**: Avoid crowding neighbors
2. **Alignment**: Steer toward average heading of neighbors
3. **Cohesion**: Steer toward average position of neighbors

**Application:**
```python
# If we detect 10 birds moving NE at 5px/frame, and one detection disappears:
# Predict its next position based on flock average velocity
flock_velocity = mean([bird.velocity for bird in nearby_birds])
predicted_position = last_known_position + flock_velocity

# Search for reappearance in prediction zone (not just max_distance radius)
search_radius = adaptive_radius_based_on_flock_coherence
```

**Benefits:**
- Can re-acquire birds that briefly disappear behind lamp post
- Handles occlusion better than individual tracking
- Mimics actual bird behavior

### Innovation 2: Negative Space Detection
**Concept:** Instead of detecting birds directly, detect the "holes" they create in the sky gradient.

**Theory:**
- Blue sky has a smooth brightness gradient (brighter near horizon, darker at zenith)
- Birds appear as dark anomalies in this gradient
- Buildings/lamp posts are LARGE anomalies; birds are SMALL anomalies

**Algorithm:**
```python
# 1. Model the sky as a smooth gradient
sky_model = fit_polynomial_surface(frame, degree=2, exclude_dark_regions)

# 2. Compute residual (actual - expected)
residual = frame_gray - sky_model

# 3. Birds are small negative residuals
bird_candidates = residual < -threshold

# 4. Static objects are large connected components - filter by size
bird_mask = remove_large_components(bird_candidates, max_size=100)
```

**Benefits:**
- Inherently ignores static objects (they're part of the scene model)
- Adapts to different sky conditions automatically
- Works regardless of absolute brightness

### Innovation 8: Motion Vector Coherence Filtering
**Concept:** Real birds have smooth, physically plausible motion; noise has random jumps.

**Theory:**
- Birds have mass and inertia; they can't teleport or change direction instantly
- Maximum acceleration is bounded by physics (~2-3g for most birds)
- Detections that violate physics are likely false positives

**Algorithm:**
```python
MAX_ACCELERATION = 50  # pixels/frame² (tune based on video)

for tracked_bird in all_tracked_birds:
    predicted_velocity = tracked_bird.velocity  # from last 2 frames
    actual_velocity = tracked_bird.new_position - tracked_bird.old_position

    acceleration = actual_velocity - predicted_velocity

    if magnitude(acceleration) > MAX_ACCELERATION:
        # Physically implausible - likely noise or wrong match
        tracked_bird.confidence *= 0.5
        if tracked_bird.confidence < threshold:
            deregister(tracked_bird)
```

**Benefits:**
- Physics-based validation is robust and explainable
- Catches ID switches (sudden direction change)
- Works regardless of bird size or appearance

---

## Summary: Top 5 Recommendations

Based on impact, feasibility, and CPU efficiency:

| Rank | Improvement | Why |
|------|-------------|-----|
| 1 | **Persistence-Based Static Detection** | Automatically eliminates lamp/tree/building false positives |
| 2 | **Frame Differencing + MOG2 Hybrid** | Best of both algorithms, minimal CPU cost |
| 3 | **CLAHE Contrast Enhancement** | Single line of code, significant visibility improvement |
| 4 | **Velocity Prediction** | Uses existing trajectory data, improves tracking accuracy |
| 5 | **Flock Behavior Prediction** | Unique approach leveraging bird biology for better tracking |

---

*Document prepared for CompVision bird tracking optimization project.*
*All recommendations maintain CPU-only operation requirement.*

---

## Gemini Independent Review & Validation

### 1. Feasibility Assessment
**Overall Verdict:** High Feasibility.
The proposed roadmap effectively leverages CPU-optimized OpenCV functions. The shift away from deep learning ensures the 15-30 FPS target is attainable on standard hardware.

### 2. Strategic Endorsements & Adjustments

#### A. Static Object Filtering (The "Lamp Post" Problem)
**Recommendation:** Prioritize **Improvement 4 (Persistence-Based Static Detection)** above all else.
*   **Why:** This is the robust solution to Challenge 2. Manual exclusion zones are brittle; a persistence map (or "heatmap") that masks pixels active >50% of the time provides a self-calibrating "anti-lamp" filter that works even if the camera framing shifts slightly.

#### B. Small Object Detection
**Recommendation:** Implement **Improvement 1 (Hybrid Detection)** immediately.
*   **Logic:** `MOG2` establishes the scene, but `Frame Differencing` captures the *event* of motion. Logical `AND`ing these (Foreground AND Moving) is the industry standard for minimizing static noise.

#### C. Tracking robustness
**Recommendation:** **Improvement 3 (Velocity Prediction)** is mandatory, not optional.
*   **Context:** For "Challenge 3: Multi-Object Tracking," simple Euclidean distance fails when birds swarm. A simple linear velocity vector (`next_pos = current_pos + velocity`) prevents ID swapping during density spikes.

#### D. Review of "Innovation 2: Negative Space Detection"
*   **Context:** Based on the verified nature of `birdsExample.mp4` (uniform sky gradient), this strategy is promoted from "Outside-the-Box" to **High Potential**.
*   **Adjustment:** Since the sky gradient is reliable, detecting "dark anomalies" against a modeled surface is likely **faster** than MOG2. It inherently solves the static object problem because buildings are not "small dark anomalies" but large structures. This should be prototyped alongside MOG2.

### 3. Implementation Warnings
1.  **Noise Amplification:** Lowering `min_contour_area` to 4px (as recommended in Config) increases sensitivity to sensor grain. **Strict Morphological Opening** (kernel size 2-3) is required to counter this.
2.  **Calibration Burn-in:** Strategy A (Auto Exclusion) needs a "rolling average" rather than a one-time setup, otherwise a bird sitting on a wire during startup becomes a permanent blind spot.

---
**Approved for Implementation Phase.**
