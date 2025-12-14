"""
Integration tests for BirdTrackingSystem class.
Tests the complete tracking pipeline including config loading,
video processing, and frame callback invocation.
"""

import pytest
import os
import json
import tempfile
import numpy as np
import cv2
from pathlib import Path

from bird_tracker import BirdTrackingSystem


class TestBirdTrackingSystemInitialization:
    """Tests for BirdTrackingSystem initialization."""

    def test_initialization_with_config_file(self):
        """Test BirdTrackingSystem initializes from config.json file."""
        # Get path to actual config file in scripts directory
        scripts_dir = Path(__file__).parent.parent
        config_path = scripts_dir / 'config.json'

        if not config_path.exists():
            pytest.skip("config.json not found in scripts directory")

        # Change to scripts dir so relative path works
        original_dir = os.getcwd()
        os.chdir(scripts_dir)

        try:
            tracker = BirdTrackingSystem(config_path='config.json')

            assert tracker.config is not None
            assert tracker.detector is not None
            assert tracker.tracker is not None
            assert 'detection' in tracker.config
            assert 'tracking' in tracker.config
        finally:
            os.chdir(original_dir)

    def test_initialization_missing_config_raises_error(self):
        """Test BirdTrackingSystem raises error for missing config file."""
        with pytest.raises(FileNotFoundError):
            BirdTrackingSystem(config_path='nonexistent_config.json')


class TestBirdTrackingSystemProcessFrames:
    """Tests for the _process_frames generator."""

    @pytest.fixture
    def temp_video(self):
        """Create a temporary test video file."""
        # Create a simple 10-frame video
        temp_dir = tempfile.mkdtemp()
        video_path = os.path.join(temp_dir, 'test_video.mp4')

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(video_path, fourcc, 30, (640, 480))

        for i in range(10):
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            # Add a moving white circle to simulate a bird
            x = 100 + i * 20
            cv2.circle(frame, (x, 100), 10, (255, 255, 255), -1)
            writer.write(frame)

        writer.release()

        yield video_path

        # Cleanup
        os.remove(video_path)
        os.rmdir(temp_dir)

    @pytest.fixture
    def tracking_system(self):
        """Create a BirdTrackingSystem with test config."""
        scripts_dir = Path(__file__).parent.parent
        config_path = scripts_dir / 'config.json'

        if not config_path.exists():
            pytest.skip("config.json not found")

        original_dir = os.getcwd()
        os.chdir(scripts_dir)

        try:
            system = BirdTrackingSystem(config_path='config.json')
            yield system
        finally:
            os.chdir(original_dir)

    def test_process_frames_generator_yields_data(self, tracking_system, temp_video):
        """Test _process_frames generator yields frame data."""
        frames_processed = 0

        for frame_num, frame, boxes, objects, det_idx, stats, video_props in tracking_system._process_frames(temp_video):
            frames_processed += 1

            # Verify yielded data structure
            assert isinstance(frame_num, int)
            assert frame_num > 0
            assert isinstance(frame, np.ndarray)
            assert frame.shape == (480, 640, 3)
            assert isinstance(boxes, list)
            assert isinstance(objects, dict)
            assert isinstance(det_idx, dict)
            assert isinstance(stats, dict)
            assert isinstance(video_props, dict)

            # Verify video properties
            assert 'fps' in video_props
            assert 'width' in video_props
            assert 'height' in video_props
            assert 'total_frames' in video_props

        assert frames_processed == 10

    def test_process_frames_raises_on_invalid_video(self, tracking_system):
        """Test _process_frames raises IOError for invalid video path."""
        with pytest.raises(IOError):
            # Try to iterate the generator
            for _ in tracking_system._process_frames('/nonexistent/video.mp4'):
                pass


class TestBirdTrackingSystemProcessVideoStream:
    """Tests for process_video_stream method (IPC mode)."""

    @pytest.fixture
    def temp_video(self):
        """Create a temporary test video file."""
        temp_dir = tempfile.mkdtemp()
        video_path = os.path.join(temp_dir, 'test_video.mp4')

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(video_path, fourcc, 30, (640, 480))

        for i in range(5):
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            writer.write(frame)

        writer.release()

        yield video_path

        os.remove(video_path)
        os.rmdir(temp_dir)

    @pytest.fixture
    def tracking_system(self):
        """Create a BirdTrackingSystem with test config."""
        scripts_dir = Path(__file__).parent.parent
        config_path = scripts_dir / 'config.json'

        if not config_path.exists():
            pytest.skip("config.json not found")

        original_dir = os.getcwd()
        os.chdir(scripts_dir)

        try:
            system = BirdTrackingSystem(config_path='config.json')
            yield system
        finally:
            os.chdir(original_dir)

    def test_process_video_stream_returns_stats(self, tracking_system, temp_video):
        """Test process_video_stream returns processing statistics."""
        stats = tracking_system.process_video_stream(temp_video)

        assert isinstance(stats, dict)
        assert 'total_frames' in stats
        assert 'processed_frames' in stats
        assert 'max_simultaneous_birds' in stats
        assert 'total_unique_birds' in stats
        assert 'fps' in stats
        assert 'width' in stats
        assert 'height' in stats

        assert stats['processed_frames'] == 5
        assert stats['width'] == 640
        assert stats['height'] == 480

    def test_process_video_stream_invokes_callback(self, tracking_system, temp_video):
        """Test process_video_stream invokes frame_callback for each frame."""
        callback_data = []

        def frame_callback(frame_num, tracking_data):
            callback_data.append({
                'frame_num': frame_num,
                'tracking_data': tracking_data
            })

        tracking_system.process_video_stream(temp_video, frame_callback=frame_callback)

        # Callback should be invoked for each frame
        assert len(callback_data) == 5

        # Verify callback data structure
        for data in callback_data:
            assert 'frame_num' in data
            assert 'tracking_data' in data
            td = data['tracking_data']
            assert 'frame' in td
            assert 'objects' in td
            assert 'stats' in td

    def test_process_video_stream_without_callback(self, tracking_system, temp_video):
        """Test process_video_stream works without callback."""
        # Should not raise error
        stats = tracking_system.process_video_stream(temp_video, frame_callback=None)

        assert stats['processed_frames'] == 5


class TestBirdTrackingSystemBuildTrackingData:
    """Tests for _build_tracking_data helper method."""

    @pytest.fixture
    def tracking_system(self):
        """Create a BirdTrackingSystem with test config."""
        scripts_dir = Path(__file__).parent.parent
        config_path = scripts_dir / 'config.json'

        if not config_path.exists():
            pytest.skip("config.json not found")

        original_dir = os.getcwd()
        os.chdir(scripts_dir)

        try:
            system = BirdTrackingSystem(config_path='config.json')
            yield system
        finally:
            os.chdir(original_dir)

    def test_build_tracking_data_empty(self, tracking_system):
        """Test _build_tracking_data with no objects."""
        tracking_data = tracking_system._build_tracking_data(
            frame_num=1,
            objects={},
            detection_indices={},
            bounding_boxes=[],
            stats={'current_birds': 0, 'total_birds_seen': 0}
        )

        assert tracking_data['frame'] == 1
        assert tracking_data['objects'] == []
        assert tracking_data['stats']['current_birds'] == 0
        assert tracking_data['stats']['total_birds'] == 0

    def test_build_tracking_data_with_objects(self, tracking_system):
        """Test _build_tracking_data with tracked objects."""
        objects = {
            0: np.array([100, 100]),
            1: np.array([200, 150])
        }
        detection_indices = {0: 0, 1: 1}
        bounding_boxes = [
            (90, 90, 20, 20),
            (190, 140, 20, 20)
        ]
        stats = {'current_birds': 2, 'total_birds_seen': 2}

        tracking_data = tracking_system._build_tracking_data(
            frame_num=5,
            objects=objects,
            detection_indices=detection_indices,
            bounding_boxes=bounding_boxes,
            stats=stats
        )

        assert tracking_data['frame'] == 5
        assert len(tracking_data['objects']) == 2
        assert tracking_data['stats']['current_birds'] == 2
        assert tracking_data['stats']['total_birds'] == 2

        # Verify object data structure
        obj = tracking_data['objects'][0]
        assert 'id' in obj
        assert 'x' in obj
        assert 'y' in obj
        assert 'w' in obj
        assert 'h' in obj
        assert 'cx' in obj
        assert 'cy' in obj


class TestBirdTrackingSystemConfigLoading:
    """Tests for configuration loading."""

    def test_load_config_validates_structure(self):
        """Test config loading validates expected structure."""
        scripts_dir = Path(__file__).parent.parent
        config_path = scripts_dir / 'config.json'

        if not config_path.exists():
            pytest.skip("config.json not found")

        with open(config_path, 'r') as f:
            config = json.load(f)

        # Verify required sections exist
        assert 'detection' in config
        assert 'tracking' in config
        assert 'visualization' in config
        assert 'output' in config

        # Verify detection parameters
        assert 'min_contour_area' in config['detection']
        assert 'max_contour_area' in config['detection']
        assert 'mog2_history' in config['detection']
        assert 'mog2_var_threshold' in config['detection']

        # Verify tracking parameters
        assert 'max_disappeared' in config['tracking']
        assert 'max_distance' in config['tracking']
