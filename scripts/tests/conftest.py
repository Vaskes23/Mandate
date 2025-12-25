"""
Shared pytest fixtures for bird tracker tests.
"""

import sys
import os
import pytest
import numpy as np

# Add parent directory to path so we can import detector and tracker modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def sample_config():
    """
    Minimal configuration dictionary for testing detector and tracker.
    Matches the structure expected by BirdDetector and CentroidTracker.
    """
    return {
        'detection': {
            'min_contour_area': 4,
            'max_contour_area': 300,
            'mog2_history': 300,
            'mog2_var_threshold': 16,
            'blur_kernel_size': 3,
            'morph_kernel_size': 2,
            'morph_iterations': 1,
            'clahe_enabled': True,
            'clahe_clip_limit': 2.0,
            'clahe_tile_size': 8
        },
        'tracking': {
            'max_disappeared': 25,
            'max_distance': 60
        },
        'spatial_filter': {
            'enabled': False,
            'horizon_line_percent': 0.85
        },
        'temporal_filter': {
            'enabled': False,
            'min_confirm_frames': 8,
            'min_move_distance': 25.0
        },
        'exclusion_zones': {
            'enabled': False,
            'zones': [],
            'draw_debug': False
        },
        'visualization': {
            'show_trails': False,
            'trail_length': 30,
            'box_color': [0, 255, 0],
            'text_color': [255, 255, 255],
            'font_scale': 0.6,
            'box_thickness': 2
        },
        'output': {
            'show_display': False,
            'save_video': False,
            'display_fps': True
        }
    }


@pytest.fixture
def config_with_temporal_filter(sample_config):
    """
    Configuration with temporal filtering enabled for testing probationary tracking.
    """
    config = sample_config.copy()
    config['temporal_filter'] = {
        'enabled': True,
        'min_confirm_frames': 3,  # Lower for faster tests
        'min_move_distance': 20.0  # Lower for easier testing
    }
    return config


@pytest.fixture
def config_with_spatial_filter(sample_config):
    """
    Configuration with spatial filtering enabled.
    """
    config = sample_config.copy()
    config['spatial_filter'] = {
        'enabled': True,
        'horizon_line_percent': 0.70
    }
    return config


@pytest.fixture
def config_with_exclusion_zones(sample_config):
    """
    Configuration with exclusion zones enabled.
    """
    config = sample_config.copy()
    config['exclusion_zones'] = {
        'enabled': True,
        'zones': [
            {'x': 100, 'y': 100, 'width': 50, 'height': 200}
        ],
        'draw_debug': False
    }
    return config


@pytest.fixture
def blank_frame():
    """
    Create a blank 640x480 BGR frame (black).
    """
    return np.zeros((480, 640, 3), dtype=np.uint8)


@pytest.fixture
def white_frame():
    """
    Create a white 640x480 BGR frame.
    """
    return np.ones((480, 640, 3), dtype=np.uint8) * 255


@pytest.fixture
def frame_with_blob():
    """
    Create a frame with a white blob on black background (simulates a bird).
    Blob is centered at (320, 100) with size ~20x20 pixels.
    """
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    # Draw a white circle to simulate a bird
    import cv2
    cv2.circle(frame, (320, 100), 10, (255, 255, 255), -1)
    return frame


@pytest.fixture
def sample_centroids():
    """
    Sample centroid array for tracker testing.
    """
    return np.array([
        [100, 100],
        [200, 200],
        [300, 150]
    ], dtype=np.float64)


@pytest.fixture
def empty_centroids():
    """
    Empty centroid array (no detections).
    """
    return np.empty((0, 2), dtype=np.float64)


@pytest.fixture
def sample_bounding_boxes():
    """
    Sample bounding boxes for testing.
    Each box is (x, y, w, h).
    """
    return [
        (90, 90, 20, 20),    # Centroid: (100, 100)
        (190, 190, 20, 20),  # Centroid: (200, 200)
        (290, 140, 20, 20)   # Centroid: (300, 150)
    ]


@pytest.fixture
def config_with_static_detection(sample_config):
    """
    Configuration with static detection enabled for testing persistence-based filtering.
    Uses low calibration_frames for faster test execution.
    """
    config = sample_config.copy()
    config['static_detection'] = {
        'enabled': True,
        'calibration_frames': 10,  # Low for fast tests
        'persistence_threshold': 0.5,
        'learning_rate': 0.1  # Higher rate for faster accumulation in tests
    }
    return config
