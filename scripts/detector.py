"""
Bird Detection Module
Provides background subtraction and contour-based detection for small birds against blue sky.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional


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


class ColorThresholder:
    """
    HSV color-based thresholding as alternative to background subtraction.
    Useful when sky color is very uniform.
    """

    def __init__(self, lower_hsv: Tuple[int, int, int] = (100, 50, 50),
                 upper_hsv: Tuple[int, int, int] = (130, 255, 255)):
        """
        Initialize color thresholder for blue sky.

        Args:
            lower_hsv: Lower HSV bounds for sky color
            upper_hsv: Upper HSV bounds for sky color
        """
        self.lower_hsv = np.array(lower_hsv)
        self.upper_hsv = np.array(upper_hsv)

    def apply(self, frame: np.ndarray) -> np.ndarray:
        """
        Apply color thresholding to isolate non-sky objects.

        Args:
            frame: Input frame (BGR)

        Returns:
            Binary mask where birds are white, sky is black
        """
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        sky_mask = cv2.inRange(hsv, self.lower_hsv, self.upper_hsv)
        # Invert to get birds (non-sky objects)
        bird_mask = cv2.bitwise_not(sky_mask)
        return bird_mask


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

        # Spatial filter configuration
        self.spatial_filter_enabled = config.get('spatial_filter', {}).get('enabled', False)
        horizon_percent = config.get('spatial_filter', {}).get('horizon_line_percent', 0.70)

        # Validate and clamp horizon_line_percent to [0, 1]
        if not (0.0 <= horizon_percent <= 1.0):
            print(f"WARNING: horizon_line_percent={horizon_percent} out of range [0.0, 1.0], clamping to valid range")
            horizon_percent = max(0.0, min(1.0, horizon_percent))
        self.horizon_line_percent = horizon_percent

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

    def preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Preprocess frame with Gaussian blur for noise reduction.

        Args:
            frame: Input frame (BGR)

        Returns:
            Blurred frame
        """
        # Apply Gaussian blur to reduce sensor noise
        blurred = cv2.GaussianBlur(frame, (self.blur_kernel, self.blur_kernel), 0)
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

        # Step 1: Preprocess (blur)
        preprocessed = self.preprocess_frame(frame)

        # Step 2: Background subtraction
        fg_mask = self.bg_subtractor.apply(preprocessed)

        # Step 3: Morphological operations
        cleaned_mask = self.apply_morphology(fg_mask)

        # Step 4: Find contours
        contours = self.find_contours(cleaned_mask)

        # Step 5: Filter and extract bounding boxes with spatial filtering
        bounding_boxes = self.filter_contours(contours, frame_height)

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
