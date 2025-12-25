"""
Bird Detection Module
Provides background subtraction and contour-based detection for small birds against blue sky.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional


def compute_iou(box1: Tuple[int, int, int, int], box2: Tuple[int, int, int, int]) -> float:
    """
    Compute Intersection over Union (IoU) between two bounding boxes.
    IoU measures overlap: 0.0 = no overlap, 1.0 = identical boxes.

    Args:
        box1: First bounding box as (x, y, width, height)
        box2: Second bounding box as (x, y, width, height)

    Returns:
        IoU value between 0.0 and 1.0
    """
    # Convert (x, y, w, h) format to corner coordinates (x1, y1, x2, y2)
    x1_a, y1_a = box1[0], box1[1]
    x2_a, y2_a = box1[0] + box1[2], box1[1] + box1[3]

    x1_b, y1_b = box2[0], box2[1]
    x2_b, y2_b = box2[0] + box2[2], box2[1] + box2[3]

    # Compute intersection rectangle coordinates
    x1_inter = max(x1_a, x1_b)
    y1_inter = max(y1_a, y1_b)
    x2_inter = min(x2_a, x2_b)
    y2_inter = min(y2_a, y2_b)

    # Compute intersection area (0 if boxes don't overlap)
    inter_width = max(0, x2_inter - x1_inter)
    inter_height = max(0, y2_inter - y1_inter)
    inter_area = inter_width * inter_height

    # Compute union area = area_a + area_b - intersection
    area_a = box1[2] * box1[3]
    area_b = box2[2] * box2[3]
    union_area = area_a + area_b - inter_area

    # Avoid division by zero for degenerate boxes
    if union_area == 0:
        return 0.0

    return inter_area / union_area


class BackgroundSubtractor:
    """
    Wrapper for MOG2 background subtraction optimized for bird detection.
    """

    def __init__(self, history: int = 500, var_threshold: float = 16, detect_shadows: bool = False):
        """
        Initialize MOG2 background subtractor.

        Args:
            history: Number of frames for background model
            var_threshold: Threshold for pixel-model match (lower = more sensitive)
            detect_shadows: Whether to detect shadows (False for performance)
        """
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=history,
            varThreshold=var_threshold,
            detectShadows=detect_shadows
        )

    def apply(self, frame: np.ndarray) -> np.ndarray:
        """
        Apply background subtraction to frame.

        Args:
            frame: Input frame (BGR)

        Returns:
            Binary foreground mask
        """
        return self.bg_subtractor.apply(frame)


class BirdDetector:
    """
    Complete bird detection pipeline using background subtraction and morphological ops.
    """

    def __init__(self, config: dict):
        """
        Initialize bird detector with configuration.

        Args:
            config: Detection configuration dictionary
        """
        self.config = config
        self.min_area = config['detection']['min_contour_area']
        self.max_area = config['detection']['max_contour_area']
        self.blur_kernel = config['detection']['blur_kernel_size']
        self.morph_kernel = config['detection']['morph_kernel_size']
        self.morph_iterations = config['detection']['morph_iterations']

        # Initialize Frame Differencing state
        # Motion threshold: SMALLER = detects slow movement. LARGER = only fast movement
        self.prev_frame = None
        self.motion_diff_threshold = config['detection'].get('motion_diff_threshold', 15)

        # Spatial filter configuration
        self.spatial_filter_enabled = config.get('spatial_filter', {}).get('enabled', False)
        horizon_percent = config.get('spatial_filter', {}).get('horizon_line_percent', 0.70)

        # Validate and clamp horizon_line_percent to [0, 1]
        if not (0.0 <= horizon_percent <= 1.0):
            print(f"WARNING: horizon_line_percent={horizon_percent} out of range [0.0, 1.0], clamping to valid range")
            horizon_percent = max(0.0, min(1.0, horizon_percent))
        self.horizon_line_percent = horizon_percent

        # Exclusion zones configuration (static masking for lamp posts, etc.)
        self.exclusion_zones_enabled = config.get('exclusion_zones', {}).get('enabled', False)
        self.exclusion_zones = config.get('exclusion_zones', {}).get('zones', [])
        self.draw_exclusion_zones = config.get('exclusion_zones', {}).get('draw_debug', False)

        # Initialize background subtractor
        self.bg_subtractor = BackgroundSubtractor(
            history=config['detection']['mog2_history'],
            var_threshold=config['detection']['mog2_var_threshold'],
            detect_shadows=False
        )

        # Create morphological kernel
        self.kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (self.morph_kernel, self.morph_kernel)
        )

        # CLAHE (Contrast Limited Adaptive Histogram Equalization) configuration
        # Enhances local contrast to make small dark birds more visible against blue sky
        self.clahe_enabled = config['detection'].get('clahe_enabled', True)
        self.clahe_clip_limit = config['detection'].get('clahe_clip_limit', 2.0)
        self.clahe_tile_size = config['detection'].get('clahe_tile_size', 8)

        # Pre-create CLAHE object for performance (avoid recreating each frame)
        if self.clahe_enabled:
            self.clahe = cv2.createCLAHE(
                clipLimit=self.clahe_clip_limit,
                tileGridSize=(self.clahe_tile_size, self.clahe_tile_size)
            )

        # Persistence-based static detection configuration
        # Automatically learns and masks persistent foreground pixels (lamp posts, antennas)
        self.static_detection_enabled = config.get('static_detection', {}).get('enabled', False)
        self.calibration_frames = config.get('static_detection', {}).get('calibration_frames', 100)
        self.persistence_threshold = config.get('static_detection', {}).get('persistence_threshold', 0.5)
        self.learning_rate = config.get('static_detection', {}).get('learning_rate', 0.05)

        # Persistence map state (lazy initialized on first frame)
        self.persistence_map: Optional[np.ndarray] = None  # Float32 accumulator [0.0, 1.0]
        self.static_mask: Optional[np.ndarray] = None      # Binary mask of static regions
        self.frame_count: int = 0                          # Frames processed for calibration
        self.calibration_complete: bool = False            # Flag when calibration is done

        # NMS (Non-Maximum Suppression) configuration
        # Merges overlapping bounding boxes to reduce false-positive clusters
        self.nms_enabled = config.get('nms', {}).get('enabled', False)
        self.iou_threshold = config.get('nms', {}).get('iou_threshold', 0.3)

    def preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Preprocess frame with CLAHE contrast enhancement and Gaussian blur.
        CLAHE enhances local contrast to make small dark birds more visible against blue sky.

        Args:
            frame: Input frame (BGR)

        Returns:
            Preprocessed frame with enhanced contrast and reduced noise
        """
        # Step 1: Apply CLAHE to enhance local contrast for small object detection
        if self.clahe_enabled:
            # Convert to LAB color space for perceptually uniform contrast enhancement
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)

            # Split LAB channels - L is luminance (brightness)
            l_channel, a_channel, b_channel = cv2.split(lab)

            # Apply CLAHE to luminance channel only (preserves color)
            l_enhanced = self.clahe.apply(l_channel)

            # Merge enhanced L channel back with original A and B channels
            lab_enhanced = cv2.merge([l_enhanced, a_channel, b_channel])

            # Convert back to BGR color space
            enhanced = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)
        else:
            enhanced = frame

        # Step 2: Apply Gaussian blur to reduce sensor noise
        blurred = cv2.GaussianBlur(enhanced, (self.blur_kernel, self.blur_kernel), 0)
        return blurred

    def apply_morphology(self, mask: np.ndarray) -> np.ndarray:
        """
        Apply morphological operations to clean up the mask.

        Args:
            mask: Binary mask from background subtraction

        Returns:
            Cleaned binary mask
        """
        # Opening: erosion followed by dilation (removes small noise)
        opened = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.kernel,
                                  iterations=self.morph_iterations)

        # Closing: dilation followed by erosion (fills small gaps)
        closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, self.kernel,
                                  iterations=self.morph_iterations)

        return closed

    def apply_exclusion_mask(self, mask: np.ndarray) -> np.ndarray:
        """
        Apply exclusion zones to foreground mask (masks out static obstacles like lamp posts).

        Args:
            mask: Binary foreground mask

        Returns:
            Masked foreground with exclusion zones set to 0 (black)
        """
        if not self.exclusion_zones_enabled or not self.exclusion_zones:
            return mask

        # Create a copy to avoid modifying the original
        masked = mask.copy()

        # Apply each exclusion zone
        for zone in self.exclusion_zones:
            x = zone.get('x', 0)
            y = zone.get('y', 0)
            width = zone.get('width', 0)
            height = zone.get('height', 0)

            # Clip zone coordinates to frame dimensions to prevent crashes
            frame_height, frame_width = masked.shape[:2]
            x = max(0, min(x, frame_width))
            y = max(0, min(y, frame_height))
            width = min(width, frame_width - x)
            height = min(height, frame_height - y)

            # Skip invalid zones
            if width <= 0 or height <= 0:
                continue

            # Set the rectangular region to 0 (black) - no detections in this area
            cv2.rectangle(masked, (x, y), (x + width, y + height), 0, -1)

        return masked

    def _initialize_persistence_map(self, frame_shape: tuple) -> None:
        """
        Lazy initialize persistence map on first frame.
        Creates a float32 array matching frame height x width for accumulation.

        Args:
            frame_shape: Shape tuple (height, width) or (height, width, channels)
        """
        height, width = frame_shape[:2]
        self.persistence_map = np.zeros((height, width), dtype=np.float32)
        self.static_mask = np.ones((height, width), dtype=np.uint8) * 255  # Start with all pixels valid

    def update_persistence_map(self, fg_mask: np.ndarray) -> None:
        """
        Update persistence map with exponential moving average of foreground pixels.
        Pixels that are frequently foreground accumulate higher values.

        Args:
            fg_mask: Binary foreground mask from MOG2 (0 or 255)
        """
        if self.persistence_map is None:
            self._initialize_persistence_map(fg_mask.shape)

        # Normalize mask to [0, 1] for EMA calculation
        normalized_mask = (fg_mask > 0).astype(np.float32)

        # Exponential moving average: new_val = (1-a)*old_val + a*new_observation
        # Foreground pixels accumulate towards 1.0, background decays towards 0.0
        self.persistence_map = (1 - self.learning_rate) * self.persistence_map + self.learning_rate * normalized_mask

        # Increment frame count for calibration tracking
        self.frame_count += 1

    def compute_static_mask(self) -> None:
        """
        Compute binary static mask from persistence map.
        Pixels with persistence above threshold are considered static obstacles.
        Called once after calibration period completes.
        """
        if self.persistence_map is None:
            return

        # Pixels with high persistence (> threshold) are static, mask them OUT (set to 0)
        # Pixels with low persistence (< threshold) are valid detection areas (255)
        self.static_mask = np.where(
            self.persistence_map > self.persistence_threshold,
            0,    # Static pixel - mask out
            255   # Valid pixel - keep detections
        ).astype(np.uint8)

    def apply_static_mask(self, mask: np.ndarray) -> np.ndarray:
        """
        Apply learned static mask to foreground mask.
        Removes detections in areas identified as persistent static objects.

        Args:
            mask: Binary foreground mask

        Returns:
            Masked foreground with static regions removed
        """
        if not self.static_detection_enabled or self.static_mask is None:
            return mask

        # Bitwise AND: only keep pixels that are BOTH foreground AND not-static
        return cv2.bitwise_and(mask, self.static_mask)

    def reset_static_detection(self) -> None:
        """
        Reset static detection for recalibration.
        Call this if camera moves or lighting changes significantly.
        """
        self.persistence_map = None
        self.static_mask = None
        self.frame_count = 0
        self.calibration_complete = False

    def find_contours(self, mask: np.ndarray) -> List[np.ndarray]:
        """
        Find contours in the binary mask.

        Args:
            mask: Binary mask

        Returns:
            List of contours
        """
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return contours

    def filter_contours(self, contours: List[np.ndarray], frame_height: int) -> List[Tuple[int, int, int, int]]:
        """
        Filter contours by area and spatial location (horizon line).

        Args:
            contours: List of contours
            frame_height: Height of the frame for horizon line calculation

        Returns:
            List of bounding boxes (x, y, w, h) for valid birds
        """
        valid_boxes = []

        # Calculate horizon line Y-coordinate (objects below this line are filtered out)
        horizon_line_y = int(frame_height * self.horizon_line_percent) if self.spatial_filter_enabled else frame_height

        for contour in contours:
            area = cv2.contourArea(contour)

            # Filter by area to eliminate noise and very large objects
            if self.min_area <= area <= self.max_area:
                x, y, w, h = cv2.boundingRect(contour)

                # Calculate centroid Y-coordinate
                cy = y + h // 2

                # Apply spatial filter: only accept detections above horizon line
                if cy < horizon_line_y:
                    valid_boxes.append((x, y, w, h))

        return valid_boxes

    def apply_nms(self, bounding_boxes: List[Tuple[int, int, int, int]]) -> List[Tuple[int, int, int, int]]:
        """
        Apply Non-Maximum Suppression to merge highly overlapping bounding boxes.
        Reduces false-positive clusters (e.g., around lamp posts) while preserving
        scattered detections (real birds in a flock).

        Algorithm:
        1. Sort boxes by area (larger boxes have priority - more likely real birds)
        2. Take largest remaining box, add to output
        3. Remove all boxes that overlap significantly (IoU > threshold)
        4. Repeat until no boxes remain

        Args:
            bounding_boxes: List of (x, y, w, h) tuples from filter_contours()

        Returns:
            Filtered list of (x, y, w, h) tuples after suppressing overlapping boxes
        """
        # Early exit if NMS disabled or not enough boxes to compare
        if not self.nms_enabled or len(bounding_boxes) <= 1:
            return bounding_boxes

        # Convert to list for modification (input may be tuple/iterator)
        boxes = list(bounding_boxes)

        # Sort by area descending - larger boxes processed first
        # Larger detections are more likely real birds vs noise fragments
        boxes.sort(key=lambda b: b[2] * b[3], reverse=True)

        # Track which boxes to keep after suppression
        keep = []

        while boxes:
            # Take the largest remaining box as reference
            current = boxes.pop(0)
            keep.append(current)

            # Filter out boxes that overlap significantly with current box
            remaining = []
            for box in boxes:
                iou = compute_iou(current, box)

                # Keep boxes with low overlap (separate detections, e.g., different birds)
                # Suppress boxes with high overlap (redundant detections, e.g., false positives)
                if iou < self.iou_threshold:
                    remaining.append(box)

            boxes = remaining

        return keep

    def detect(self, frame: np.ndarray) -> Tuple[List[Tuple[int, int, int, int]], np.ndarray]:
        """
        Complete detection pipeline: preprocess -> subtract -> morphology -> contours.

        Args:
            frame: Input frame (BGR)

        Returns:
            Tuple of (bounding_boxes, visualization_mask)
            - bounding_boxes: List of (x, y, w, h) tuples
            - visualization_mask: Binary mask for debugging
        """
        # Get frame dimensions
        frame_height = frame.shape[0]

        # Step 1: Preprocess (blur + CLAHE)
        preprocessed = self.preprocess_frame(frame)

        # Step 1.5: Frame Differencing (Motion Detection)
        # Calculate absolute difference between current and previous frame
        gray = cv2.cvtColor(preprocessed, cv2.COLOR_BGR2GRAY)
        motion_mask = None

        if self.prev_frame is None:
            self.prev_frame = gray
            # First frame has no motion history, so we rely on MOG2 (which also needs learning)
            # or we could default to all-motion or no-motion.
            # Letting MOG2 handle it (it will likely find nothing or everything) is safest.
        else:
            diff = cv2.absdiff(self.prev_frame, gray)
            _, motion_mask = cv2.threshold(diff, self.motion_diff_threshold, 255, cv2.THRESH_BINARY)
            self.prev_frame = gray

        # Step 2: Background subtraction
        fg_mask = self.bg_subtractor.apply(preprocessed)

        # Step 2.1: Combine MOG2 with Frame Differencing
        # Logical AND: A pixel must be BOTH considered foreground by MOG2 AND moving
        if motion_mask is not None:
            fg_mask = cv2.bitwise_and(fg_mask, motion_mask)

        # Step 2.2: Persistence-based static detection
        # During calibration: accumulate foreground pixels to learn static objects
        # After calibration: mask out persistent static regions (lamp posts, antennas)
        if self.static_detection_enabled:
            # Always update persistence map (rolling average even after calibration)
            self.update_persistence_map(fg_mask)

            # Check if calibration period is complete
            if not self.calibration_complete and self.frame_count >= self.calibration_frames:
                self.compute_static_mask()
                self.calibration_complete = True

            # Apply static mask after calibration is complete
            if self.calibration_complete:
                fg_mask = self.apply_static_mask(fg_mask)

        # Step 2.5: Apply exclusion zones (manual fallback for static obstacles)
        fg_mask = self.apply_exclusion_mask(fg_mask)

        # Step 3: Morphological operations
        cleaned_mask = self.apply_morphology(fg_mask)

        # Step 4: Find contours
        contours = self.find_contours(cleaned_mask)

        # Step 5: Filter and extract bounding boxes with spatial filtering
        bounding_boxes = self.filter_contours(contours, frame_height)

        # Step 6: Apply Non-Maximum Suppression to merge overlapping detections
        # Reduces false-positive clusters around static objects (lamp posts, buildings)
        if self.nms_enabled:
            bounding_boxes = self.apply_nms(bounding_boxes)

        return bounding_boxes, cleaned_mask

    def get_centroids(self, bounding_boxes: List[Tuple[int, int, int, int]]) -> np.ndarray:
        """
        Calculate centroids from bounding boxes.

        Args:
            bounding_boxes: List of (x, y, w, h) tuples

        Returns:
            Numpy array of shape (N, 2) containing (cx, cy) coordinates
        """
        centroids = []

        for (x, y, w, h) in bounding_boxes:
            cx = x + w // 2
            cy = y + h // 2
            centroids.append([cx, cy])

        return np.array(centroids) if centroids else np.empty((0, 2))
