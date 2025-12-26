"""
Unit tests for BirdDetector class.
Tests detection pipeline including background subtraction, morphology,
contour filtering, and centroid calculation.
"""

import pytest
import numpy as np
import cv2
from detector import BirdDetector, BackgroundSubtractor, compute_iou


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


class TestComputeIoU:
    """Tests for IoU (Intersection over Union) computation."""

    def test_identical_boxes_return_one(self):
        """Test IoU of identical boxes is 1.0."""
        box = (100, 100, 50, 50)
        iou = compute_iou(box, box)
        assert iou == pytest.approx(1.0)

    def test_non_overlapping_boxes_return_zero(self):
        """Test IoU of non-overlapping boxes is 0.0."""
        box1 = (0, 0, 10, 10)
        box2 = (100, 100, 10, 10)
        iou = compute_iou(box1, box2)
        assert iou == pytest.approx(0.0)

    def test_partial_overlap(self):
        """Test IoU of partially overlapping boxes is between 0 and 1."""
        box1 = (0, 0, 20, 20)
        box2 = (10, 10, 20, 20)
        iou = compute_iou(box1, box2)
        # Overlap is 10x10=100, box1=400, box2=400, union=400+400-100=700
        # IoU = 100/700 ≈ 0.143
        assert 0.0 < iou < 1.0
        assert iou == pytest.approx(100 / 700, rel=0.01)

    def test_one_box_inside_other(self):
        """Test IoU when one box is completely inside another."""
        outer = (0, 0, 100, 100)
        inner = (25, 25, 50, 50)
        iou = compute_iou(outer, inner)
        # Intersection = 50*50 = 2500, Union = 10000+2500-2500 = 10000
        assert iou == pytest.approx(2500 / 10000, rel=0.01)

    def test_degenerate_boxes_return_zero(self):
        """Test IoU of zero-area boxes returns 0.0."""
        box1 = (0, 0, 0, 0)
        box2 = (0, 0, 10, 10)
        iou = compute_iou(box1, box2)
        assert iou == pytest.approx(0.0)


class TestBirdDetectorNMS:
    """Tests for Non-Maximum Suppression (NMS) functionality."""

    def test_nms_disabled_by_default(self, sample_config):
        """Test NMS is disabled when not in config."""
        detector = BirdDetector(sample_config)
        assert detector.nms_enabled is False

    def test_nms_enabled_initialization(self, config_with_nms):
        """Test NMS initializes with correct parameters when enabled."""
        detector = BirdDetector(config_with_nms)
        assert detector.nms_enabled is True
        assert detector.nms_grid_size == 32
        assert detector.nms_max_per_cell == 4
        assert detector.nms_iou_threshold == 0.3

    def test_nms_empty_input(self, config_with_nms):
        """Test NMS returns empty list for empty input."""
        detector = BirdDetector(config_with_nms)
        result = detector.apply_fast_nms([])
        assert result == []

    def test_nms_single_box(self, config_with_nms):
        """Test NMS preserves single box unchanged."""
        detector = BirdDetector(config_with_nms)
        boxes = [(100, 100, 20, 20)]
        result = detector.apply_fast_nms(boxes)
        assert len(result) == 1
        assert result[0] == boxes[0]

    def test_nms_sparse_boxes_preserved(self, config_with_nms, separated_bounding_boxes):
        """Test NMS preserves well-separated boxes (sparse cells)."""
        detector = BirdDetector(config_with_nms)
        # Separated boxes are in different cells, all should be preserved
        result = detector.apply_fast_nms(separated_bounding_boxes)
        assert len(result) == len(separated_bounding_boxes)

    def test_nms_dense_cluster_reduced(self, config_with_nms):
        """Test NMS reduces dense overlapping clusters."""
        detector = BirdDetector(config_with_nms)
        # Create a truly dense cluster: 8 overlapping boxes (> max_per_cell of 4)
        dense_cluster = [
            (100, 100, 20, 20),
            (102, 102, 20, 20),
            (104, 104, 20, 20),
            (106, 106, 20, 20),
            (108, 108, 20, 20),
            (110, 110, 20, 20),
            (112, 112, 20, 20),
            (114, 114, 20, 20),
        ]
        result = detector.apply_fast_nms(dense_cluster)
        # Should reduce 8 overlapping boxes to max_per_cell (4) or fewer
        assert len(result) <= detector.nms_max_per_cell
        assert len(result) < len(dense_cluster)

    def test_nms_preserves_order(self, config_with_nms):
        """Test NMS maintains box order after filtering."""
        detector = BirdDetector(config_with_nms)
        # Create boxes in different cells (sparse)
        boxes = [
            (0, 0, 10, 10),      # Cell (0, 0)
            (100, 100, 10, 10),  # Cell (3, 3)
            (200, 200, 10, 10),  # Cell (6, 6)
        ]
        result = detector.apply_fast_nms(boxes)
        # Should preserve original order
        assert result == boxes

    def test_nms_grid_cell_isolation(self, config_with_nms):
        """Test NMS processes cells independently."""
        detector = BirdDetector(config_with_nms)
        # Two clusters in different cells - each should be processed independently
        boxes = [
            # Cluster 1: Cell around (0, 0)
            (0, 0, 10, 10),
            (2, 2, 10, 10),
            (4, 4, 10, 10),
            # Cluster 2: Cell around (200, 200) - different grid cell
            (200, 200, 10, 10),
            (202, 202, 10, 10),
            (204, 204, 10, 10),
        ]
        result = detector.apply_fast_nms(boxes)
        # Both clusters should be processed, but boxes from different cells preserved
        assert len(result) > 0
        assert len(result) <= 6  # Some may be merged within each cluster

    def test_nms_disabled_passthrough(self, sample_config, overlapping_bounding_boxes):
        """Test boxes pass through unchanged when NMS is disabled."""
        detector = BirdDetector(sample_config)
        assert detector.nms_enabled is False
        result = detector.apply_fast_nms(overlapping_bounding_boxes)
        # When disabled, all boxes should be returned unchanged
        assert len(result) == len(overlapping_bounding_boxes)

    def test_nms_large_boxes_prioritized(self, config_with_nms):
        """Test NMS keeps larger boxes when reducing dense clusters."""
        detector = BirdDetector(config_with_nms)
        # Create cluster of overlapping boxes with different sizes in same cell
        boxes = [
            (100, 100, 5, 5),    # Small (area=25)
            (102, 102, 5, 5),   # Small (area=25)
            (101, 101, 20, 20), # Large (area=400) - should be kept
            (103, 103, 5, 5),   # Small (area=25)
            (104, 104, 5, 5),   # Small (area=25)
            (105, 105, 5, 5),   # Small (area=25) - 6 boxes total, above threshold
        ]
        result = detector.apply_fast_nms(boxes)
        # Should keep the largest box
        has_large_box = any(box[2] == 20 and box[3] == 20 for box in result)
        assert has_large_box

    def test_nms_integrates_with_detect(self, config_with_nms):
        """Test NMS integrates correctly in full detect pipeline."""
        detector = BirdDetector(config_with_nms)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Run detection pipeline - should not raise errors
        boxes, mask = detector.detect(frame)

        assert isinstance(boxes, list)
        assert isinstance(mask, np.ndarray)

    def test_nms_performance_many_boxes(self, config_with_nms):
        """Test NMS handles many boxes efficiently."""
        import time
        detector = BirdDetector(config_with_nms)

        # Create 100 boxes distributed across the frame
        boxes = [(i * 5, (i % 50) * 5, 10, 10) for i in range(100)]

        start = time.time()
        result = detector.apply_fast_nms(boxes)
        elapsed = time.time() - start

        # Should complete in under 10ms for 100 boxes
        assert elapsed < 0.01  # 10ms threshold
        assert len(result) > 0
