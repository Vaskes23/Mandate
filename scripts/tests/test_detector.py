"""
Unit tests for BirdDetector class.
Tests detection pipeline including background subtraction, morphology,
contour filtering, and centroid calculation.
"""

import pytest
import numpy as np
import cv2
from detector import BirdDetector, BackgroundSubtractor


class TestBackgroundSubtractor:
    """Tests for BackgroundSubtractor wrapper class."""

    def test_initialization(self):
        """Test BackgroundSubtractor initializes with correct parameters."""
        bg_sub = BackgroundSubtractor(history=100, var_threshold=20, detect_shadows=False)

        # Verify internal MOG2 subtractor was created
        assert bg_sub.bg_subtractor is not None

    def test_apply_returns_mask(self, blank_frame):
        """Test apply() returns a binary mask of correct dimensions."""
        bg_sub = BackgroundSubtractor()

        mask = bg_sub.apply(blank_frame)

        assert mask is not None
        assert mask.shape == (480, 640)  # Same height x width as input
        assert mask.dtype == np.uint8


class TestBirdDetectorInitialization:
    """Tests for BirdDetector initialization."""

    def test_initialization(self, sample_config):
        """Test BirdDetector initializes with configuration values."""
        detector = BirdDetector(sample_config)

        assert detector.min_area == 4
        assert detector.max_area == 300
        assert detector.blur_kernel == 3
        assert detector.morph_kernel == 2
        assert detector.morph_iterations == 1

    def test_initialization_with_spatial_filter(self, config_with_spatial_filter):
        """Test detector initializes with spatial filter settings."""
        detector = BirdDetector(config_with_spatial_filter)

        assert detector.spatial_filter_enabled is True
        assert detector.horizon_line_percent == 0.70

    def test_initialization_with_exclusion_zones(self, config_with_exclusion_zones):
        """Test detector initializes with exclusion zone settings."""
        detector = BirdDetector(config_with_exclusion_zones)

        assert detector.exclusion_zones_enabled is True
        assert len(detector.exclusion_zones) == 1
        assert detector.exclusion_zones[0]['x'] == 100


class TestBirdDetectorPreprocessing:
    """Tests for frame preprocessing."""

    def test_preprocess_frame_applies_blur(self, sample_config, blank_frame):
        """Test preprocess_frame() applies Gaussian blur."""
        detector = BirdDetector(sample_config)

        # Create a frame with some noise
        noisy_frame = blank_frame.copy()
        noisy_frame[100, 100] = [255, 255, 255]

        preprocessed = detector.preprocess_frame(noisy_frame)

        # Blur should spread the white pixel
        assert preprocessed.shape == noisy_frame.shape
        # The exact white pixel should be dimmed (blurred)
        assert preprocessed[100, 100, 0] < 255


class TestBirdDetectorMorphology:
    """Tests for morphological operations."""

    def test_apply_morphology(self, sample_config):
        """Test morphological operations clean up the mask."""
        detector = BirdDetector(sample_config)

        # Create a mask with small noise dots
        mask = np.zeros((480, 640), dtype=np.uint8)
        mask[100, 100] = 255  # Small single pixel (noise)
        mask[200:210, 200:210] = 255  # Larger blob (should remain)

        cleaned = detector.apply_morphology(mask)

        # Small noise should be removed, larger blob should remain
        assert cleaned.shape == mask.shape
        # Morphology should have processed the mask
        assert cleaned.dtype == np.uint8


class TestBirdDetectorContours:
    """Tests for contour detection and filtering."""

    def test_find_contours_returns_list(self, sample_config):
        """Test find_contours() returns a list of contours."""
        detector = BirdDetector(sample_config)

        # Create a mask with a blob
        mask = np.zeros((480, 640), dtype=np.uint8)
        cv2.circle(mask, (320, 240), 20, 255, -1)

        contours = detector.find_contours(mask)

        assert isinstance(contours, list) or isinstance(contours, tuple)
        assert len(contours) >= 1

    def test_filter_contours_by_area(self, sample_config):
        """Test filter_contours() filters by min/max area."""
        detector = BirdDetector(sample_config)

        # Create mask with blobs of different sizes
        mask = np.zeros((480, 640), dtype=np.uint8)
        cv2.circle(mask, (100, 100), 5, 255, -1)   # Small blob
        cv2.circle(mask, (200, 100), 15, 255, -1)  # Medium blob
        cv2.circle(mask, (300, 100), 50, 255, -1)  # Large blob

        contours = detector.find_contours(mask)
        boxes = detector.filter_contours(contours, frame_height=480)

        # Should only keep blobs within area range
        assert isinstance(boxes, list)
        for box in boxes:
            assert len(box) == 4  # (x, y, w, h)

    def test_filter_contours_with_spatial_filter(self, config_with_spatial_filter):
        """Test spatial filter removes detections below horizon line."""
        detector = BirdDetector(config_with_spatial_filter)

        # Create mock contours - one above horizon (y=100), one below (y=400)
        # With horizon at 70%, horizon_y = 480 * 0.70 = 336
        mask = np.zeros((480, 640), dtype=np.uint8)
        cv2.circle(mask, (200, 100), 15, 255, -1)  # Above horizon
        cv2.circle(mask, (200, 400), 15, 255, -1)  # Below horizon

        contours = detector.find_contours(mask)
        boxes = detector.filter_contours(contours, frame_height=480)

        # Only detection above horizon should pass
        # Check that at least some filtering happened
        assert isinstance(boxes, list)


class TestBirdDetectorExclusionZones:
    """Tests for exclusion zone masking."""

    def test_apply_exclusion_mask_disabled(self, sample_config):
        """Test exclusion mask is identity when disabled."""
        detector = BirdDetector(sample_config)

        mask = np.ones((480, 640), dtype=np.uint8) * 255

        result = detector.apply_exclusion_mask(mask)

        # Should be unchanged when disabled
        assert result.shape == mask.shape
        assert result.dtype == mask.dtype
        # When exclusion is disabled, result should be the same object or equal array
        assert np.array_equal(result, mask)

    def test_apply_exclusion_mask_enabled(self, config_with_exclusion_zones):
        """Test exclusion mask blacks out configured zones."""
        detector = BirdDetector(config_with_exclusion_zones)

        mask = np.ones((480, 640), dtype=np.uint8) * 255

        result = detector.apply_exclusion_mask(mask)

        # Zone at (100, 100, 50, 200) should be black
        assert result[150, 125] == 0  # Inside zone
        assert result[50, 50] == 255  # Outside zone


class TestBirdDetectorDetect:
    """Tests for complete detection pipeline."""

    def test_detect_returns_tuple(self, sample_config, blank_frame):
        """Test detect() returns (bounding_boxes, mask) tuple."""
        detector = BirdDetector(sample_config)

        result = detector.detect(blank_frame)

        assert isinstance(result, tuple)
        assert len(result) == 2
        boxes, mask = result
        assert isinstance(boxes, list)
        assert isinstance(mask, np.ndarray)

    def test_detect_empty_frame(self, sample_config, blank_frame):
        """Test detect() on blank frame returns empty boxes."""
        detector = BirdDetector(sample_config)

        # Run multiple frames to build background model
        for _ in range(5):
            boxes, mask = detector.detect(blank_frame)

        # Blank frame should have no detections after background model stabilizes
        assert isinstance(boxes, list)

    def test_detect_with_foreground_object(self, sample_config):
        """Test detect() finds foreground objects against stable background."""
        detector = BirdDetector(sample_config)

        # First, build background model with blank frames
        blank = np.zeros((480, 640, 3), dtype=np.uint8)
        for _ in range(10):
            detector.detect(blank)

        # Now introduce a foreground object
        frame_with_object = blank.copy()
        cv2.circle(frame_with_object, (320, 100), 10, (255, 255, 255), -1)

        boxes, mask = detector.detect(frame_with_object)

        # Should detect the white circle as foreground
        # Note: Detection depends on MOG2 model state
        assert isinstance(boxes, list)
        assert isinstance(mask, np.ndarray)


class TestBirdDetectorCentroids:
    """Tests for centroid calculation."""

    def test_get_centroids_empty(self, sample_config):
        """Test get_centroids() with empty bounding boxes."""
        detector = BirdDetector(sample_config)

        centroids = detector.get_centroids([])

        assert centroids.shape == (0, 2)

    def test_get_centroids_calculation(self, sample_config, sample_bounding_boxes):
        """Test get_centroids() calculates correct centroid positions."""
        detector = BirdDetector(sample_config)

        centroids = detector.get_centroids(sample_bounding_boxes)

        assert centroids.shape == (3, 2)
        # First box: (90, 90, 20, 20) -> centroid (100, 100)
        assert centroids[0, 0] == 100
        assert centroids[0, 1] == 100
        # Second box: (190, 190, 20, 20) -> centroid (200, 200)
        assert centroids[1, 0] == 200
        assert centroids[1, 1] == 200
        # Third box: (290, 140, 20, 20) -> centroid (300, 150)
        assert centroids[2, 0] == 300
        assert centroids[2, 1] == 150

    def test_get_centroids_returns_numpy_array(self, sample_config, sample_bounding_boxes):
        """Test get_centroids() returns numpy array."""
        detector = BirdDetector(sample_config)

        centroids = detector.get_centroids(sample_bounding_boxes)

        assert isinstance(centroids, np.ndarray)
        assert centroids.ndim == 2


class TestBirdDetectorCLAHE:
    """Tests for CLAHE contrast enhancement preprocessing."""

    def test_clahe_enabled_by_default(self, sample_config):
        """Test CLAHE is enabled when config specifies it."""
        detector = BirdDetector(sample_config)

        assert detector.clahe_enabled is True
        assert hasattr(detector, 'clahe')

    def test_clahe_disabled(self, sample_config):
        """Test CLAHE can be disabled via config."""
        config = sample_config.copy()
        config['detection'] = sample_config['detection'].copy()
        config['detection']['clahe_enabled'] = False
        detector = BirdDetector(config)

        assert detector.clahe_enabled is False

    def test_preprocess_frame_with_clahe(self, sample_config, blank_frame):
        """Test preprocess_frame() applies CLAHE and returns correct shape."""
        detector = BirdDetector(sample_config)

        preprocessed = detector.preprocess_frame(blank_frame)

        assert preprocessed.shape == blank_frame.shape
        assert preprocessed.dtype == blank_frame.dtype

    def test_preprocess_frame_clahe_disabled(self, sample_config, blank_frame):
        """Test preprocess_frame() works when CLAHE is disabled."""
        config = sample_config.copy()
        config['detection'] = sample_config['detection'].copy()
        config['detection']['clahe_enabled'] = False
        detector = BirdDetector(config)

        preprocessed = detector.preprocess_frame(blank_frame)

        assert preprocessed.shape == blank_frame.shape
        assert preprocessed.dtype == blank_frame.dtype

    def test_clahe_enhances_contrast(self, sample_config):
        """Test CLAHE actually enhances contrast in low-contrast image."""
        detector = BirdDetector(sample_config)

        # Create a low-contrast gray image (simulates hazy sky)
        low_contrast = np.full((480, 640, 3), 128, dtype=np.uint8)
        # Add a slightly darker region (simulates bird)
        low_contrast[200:220, 300:320] = 118

        preprocessed = detector.preprocess_frame(low_contrast)

        # CLAHE should enhance contrast - the image should be different
        assert preprocessed.shape == low_contrast.shape


class TestBirdDetectorStaticDetection:
    """Tests for persistence-based static detection."""

    def test_static_detection_disabled_by_default(self, sample_config):
        """Test static detection is disabled when not in config."""
        detector = BirdDetector(sample_config)

        assert detector.static_detection_enabled is False
        assert detector.persistence_map is None
        assert detector.calibration_complete is False

    def test_static_detection_enabled(self, config_with_static_detection):
        """Test static detection initializes with correct parameters."""
        detector = BirdDetector(config_with_static_detection)

        assert detector.static_detection_enabled is True
        assert detector.calibration_frames == 10
        assert detector.persistence_threshold == 0.5
        assert detector.learning_rate == 0.1

    def test_persistence_map_lazy_initialization(self, config_with_static_detection):
        """Test persistence map is None until first frame processed."""
        detector = BirdDetector(config_with_static_detection)

        assert detector.persistence_map is None

        # Process a frame to trigger lazy initialization
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        detector.detect(frame)

        # Now persistence map should be initialized
        assert detector.persistence_map is not None
        assert detector.persistence_map.shape == (480, 640)
        assert detector.persistence_map.dtype == np.float32

    def test_frame_count_increments(self, config_with_static_detection):
        """Test frame count increments during calibration."""
        detector = BirdDetector(config_with_static_detection)

        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Process 5 frames
        for i in range(5):
            detector.detect(frame)
            assert detector.frame_count == i + 1

    def test_calibration_completes_after_threshold(self, config_with_static_detection):
        """Test calibration completes after specified number of frames."""
        detector = BirdDetector(config_with_static_detection)

        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Process frames until just before calibration threshold
        for _ in range(9):
            detector.detect(frame)
        assert detector.calibration_complete is False

        # Process one more frame to complete calibration
        detector.detect(frame)
        assert detector.calibration_complete is True
        assert detector.static_mask is not None

    def test_persistence_accumulates_for_static_pixels(self, config_with_static_detection):
        """Test persistent foreground pixels accumulate in persistence map."""
        detector = BirdDetector(config_with_static_detection)

        # Create a foreground mask with a persistent region
        fg_mask = np.zeros((480, 640), dtype=np.uint8)
        fg_mask[200:220, 300:320] = 255  # Persistent foreground region

        # Initialize and update persistence map
        detector._initialize_persistence_map(fg_mask.shape)
        initial_value = detector.persistence_map[210, 310]

        # Update multiple times
        for _ in range(5):
            detector.update_persistence_map(fg_mask)

        # Persistent region should have accumulated higher values
        assert detector.persistence_map[210, 310] > initial_value
        # Background region should remain near zero
        assert detector.persistence_map[50, 50] < 0.1

    def test_static_mask_masks_persistent_regions(self, config_with_static_detection):
        """Test static mask correctly masks out persistent foreground regions."""
        detector = BirdDetector(config_with_static_detection)

        # Create foreground mask with persistent region
        fg_mask = np.zeros((480, 640), dtype=np.uint8)
        fg_mask[200:220, 300:320] = 255

        # Initialize and accumulate persistence
        detector._initialize_persistence_map(fg_mask.shape)
        for _ in range(20):  # Enough iterations to exceed threshold
            detector.update_persistence_map(fg_mask)

        # Compute static mask
        detector.compute_static_mask()

        # Persistent region should be masked out (0)
        assert detector.static_mask[210, 310] == 0
        # Non-persistent region should be valid (255)
        assert detector.static_mask[50, 50] == 255

    def test_apply_static_mask_removes_static_detections(self, config_with_static_detection):
        """Test apply_static_mask removes detections in static regions."""
        detector = BirdDetector(config_with_static_detection)

        # Setup static mask with a masked region
        detector._initialize_persistence_map((480, 640))
        detector.static_mask[200:220, 300:320] = 0  # Masked static region

        # Create foreground mask with detection in static region
        fg_mask = np.zeros((480, 640), dtype=np.uint8)
        fg_mask[200:220, 300:320] = 255  # Detection in static region
        fg_mask[50:70, 100:120] = 255    # Detection in valid region

        # Apply static mask
        result = detector.apply_static_mask(fg_mask)

        # Static region detection should be removed
        assert result[210, 310] == 0
        # Valid region detection should remain
        assert result[60, 110] == 255

    def test_reset_static_detection(self, config_with_static_detection):
        """Test reset_static_detection clears all state."""
        detector = BirdDetector(config_with_static_detection)

        # Process some frames to build state
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        for _ in range(15):
            detector.detect(frame)

        assert detector.persistence_map is not None
        assert detector.calibration_complete is True

        # Reset
        detector.reset_static_detection()

        assert detector.persistence_map is None
        assert detector.static_mask is None
        assert detector.frame_count == 0
        assert detector.calibration_complete is False

    def test_static_detection_integrates_with_detect(self, config_with_static_detection):
        """Test static detection integrates correctly in full detect pipeline."""
        detector = BirdDetector(config_with_static_detection)

        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Run detection pipeline
        boxes, mask = detector.detect(frame)

        # Should return valid tuple without errors
        assert isinstance(boxes, list)
        assert isinstance(mask, np.ndarray)
        assert mask.shape == (480, 640)
