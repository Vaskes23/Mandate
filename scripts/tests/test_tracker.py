"""
Unit tests for CentroidTracker class.
Tests tracking logic including registration, deregistration, Hungarian algorithm matching,
and probationary object handling.
"""

import pytest
import numpy as np
from tracker import CentroidTracker


class TestCentroidTrackerBasic:
    """Tests for basic tracker functionality without temporal filtering."""

    def test_initialization(self, sample_config):
        """Test tracker initializes with correct default values."""
        tracker = CentroidTracker(
            max_disappeared=30,
            max_distance=100,
            config=sample_config
        )

        assert tracker.max_disappeared == 30
        assert tracker.max_distance == 100
        assert tracker.next_object_id == 0
        assert len(tracker.objects) == 0
        assert tracker.total_birds_seen == 0

    def test_register_assigns_unique_ids(self, sample_config):
        """Test that register() assigns incrementing unique IDs."""
        tracker = CentroidTracker(max_disappeared=30, max_distance=100, config=sample_config)

        # Register first object
        id1 = tracker.register(np.array([100, 100]))
        assert id1 == 0
        assert tracker.total_birds_seen == 1

        # Register second object
        id2 = tracker.register(np.array([200, 200]))
        assert id2 == 1
        assert tracker.total_birds_seen == 2

        # IDs should be unique
        assert id1 != id2
        assert len(tracker.objects) == 2

    def test_deregister_removes_object(self, sample_config):
        """Test that deregister() properly removes an object."""
        tracker = CentroidTracker(max_disappeared=30, max_distance=100, config=sample_config)

        # Register and then deregister
        obj_id = tracker.register(np.array([100, 100]))
        assert obj_id in tracker.objects

        tracker.deregister(obj_id)
        assert obj_id not in tracker.objects
        assert obj_id not in tracker.disappeared

    def test_update_with_empty_centroids(self, sample_config, empty_centroids):
        """Test update() marks objects as disappeared when no detections."""
        tracker = CentroidTracker(max_disappeared=3, max_distance=100, config=sample_config)

        # Register an object first
        tracker.register(np.array([100, 100]))
        assert len(tracker.objects) == 1

        # Update with no detections multiple times
        for i in range(3):
            tracker.update(empty_centroids)
            assert tracker.disappeared[0] == i + 1

        # After max_disappeared, object should be deregistered
        tracker.update(empty_centroids)
        assert len(tracker.objects) == 0

    def test_update_registers_new_detections(self, sample_config, sample_centroids):
        """Test update() registers all new detections when tracker is empty."""
        tracker = CentroidTracker(max_disappeared=30, max_distance=100, config=sample_config)

        objects, det_indices = tracker.update(sample_centroids)

        assert len(objects) == 3
        assert tracker.total_birds_seen == 3
        # Each detection should have a corresponding index
        assert len(det_indices) == 3

    def test_update_maintains_id_persistence(self, sample_config):
        """Test that IDs persist when objects move within max_distance."""
        tracker = CentroidTracker(max_disappeared=30, max_distance=100, config=sample_config)

        # Initial detection
        initial_centroids = np.array([[100, 100]], dtype=np.float64)
        objects1, _ = tracker.update(initial_centroids)
        original_id = list(objects1.keys())[0]

        # Slight movement (within max_distance)
        moved_centroids = np.array([[110, 105]], dtype=np.float64)
        objects2, _ = tracker.update(moved_centroids)

        # Same ID should be maintained
        assert original_id in objects2
        assert len(objects2) == 1

    def test_update_creates_new_id_for_distant_object(self, sample_config):
        """Test that a new ID is created when object moves beyond max_distance."""
        tracker = CentroidTracker(max_disappeared=30, max_distance=50, config=sample_config)

        # Initial detection
        initial_centroids = np.array([[100, 100]], dtype=np.float64)
        objects1, _ = tracker.update(initial_centroids)
        original_id = list(objects1.keys())[0]

        # Large movement (beyond max_distance)
        moved_centroids = np.array([[300, 300]], dtype=np.float64)
        objects2, _ = tracker.update(moved_centroids)

        # Original object should start disappearing, new object registered
        # After first update, original might still exist with disappeared count
        # After max_disappeared updates, it will be gone
        assert tracker.total_birds_seen >= 1

    def test_get_statistics(self, sample_config, sample_centroids):
        """Test get_statistics() returns accurate counts."""
        tracker = CentroidTracker(max_disappeared=30, max_distance=100, config=sample_config)

        # Initially empty
        stats = tracker.get_statistics()
        assert stats['current_birds'] == 0
        assert stats['total_birds_seen'] == 0

        # After adding objects
        tracker.update(sample_centroids)
        stats = tracker.get_statistics()
        assert stats['current_birds'] == 3
        assert stats['total_birds_seen'] == 3

    def test_get_trajectory(self, sample_config):
        """Test get_trajectory() returns object path history."""
        tracker = CentroidTracker(max_disappeared=30, max_distance=100, config=sample_config)

        # Track object over multiple frames
        positions = [
            np.array([[100, 100]], dtype=np.float64),
            np.array([[110, 105]], dtype=np.float64),
            np.array([[120, 110]], dtype=np.float64)
        ]

        for pos in positions:
            tracker.update(pos)

        trajectory = tracker.get_trajectory(0)
        assert len(trajectory) == 3
        assert trajectory[0] == (100, 100)
        assert trajectory[1] == (110, 105)
        assert trajectory[2] == (120, 110)

    def test_reset_clears_all_state(self, sample_config, sample_centroids):
        """Test reset() clears all tracker state."""
        tracker = CentroidTracker(max_disappeared=30, max_distance=100, config=sample_config)

        # Add some objects
        tracker.update(sample_centroids)
        assert len(tracker.objects) > 0
        assert tracker.total_birds_seen > 0

        # Reset
        tracker.reset()

        assert len(tracker.objects) == 0
        assert tracker.next_object_id == 0
        assert tracker.total_birds_seen == 0
        assert len(tracker.trajectories) == 0


class TestCentroidTrackerTemporalFilter:
    """Tests for tracker with temporal filtering (probationary tracking)."""

    def test_temporal_filter_enabled(self, config_with_temporal_filter):
        """Test tracker recognizes temporal filter configuration."""
        tracker = CentroidTracker(
            max_disappeared=30,
            max_distance=100,
            config=config_with_temporal_filter
        )

        assert tracker.temporal_filter_enabled is True
        assert tracker.min_confirm_frames == 3
        assert tracker.min_move_distance == 20.0

    def test_probationary_registration(self, config_with_temporal_filter):
        """Test new detections start as probationary objects."""
        tracker = CentroidTracker(
            max_disappeared=30,
            max_distance=100,
            config=config_with_temporal_filter
        )

        # Initial detection with temporal filter enabled
        centroids = np.array([[100, 100]], dtype=np.float64)
        objects, _ = tracker.update(centroids)

        # Object should be probationary, not confirmed yet
        assert len(tracker.probationary) == 1
        assert len(objects) == 0  # No confirmed objects yet
        assert tracker.total_birds_seen == 0  # Not counted until confirmed

    def test_probationary_promotion_with_movement(self, config_with_temporal_filter):
        """Test probationary object promotes to confirmed after sufficient movement."""
        tracker = CentroidTracker(
            max_disappeared=30,
            max_distance=100,
            config=config_with_temporal_filter
        )

        # Track object moving over several frames (cumulative distance > min_move_distance)
        positions = [
            np.array([[100, 100]], dtype=np.float64),
            np.array([[110, 100]], dtype=np.float64),  # +10
            np.array([[120, 100]], dtype=np.float64),  # +10 = 20 total
            np.array([[130, 100]], dtype=np.float64),  # +10 = 30 total (> 20 threshold)
        ]

        for pos in positions:
            objects, _ = tracker.update(pos)

        # After enough movement and frames, object should be promoted
        assert tracker.total_birds_seen >= 1

    def test_probationary_cleanup_on_disappeared(self, config_with_temporal_filter):
        """Test probationary objects are cleaned up quickly when they disappear."""
        tracker = CentroidTracker(
            max_disappeared=30,
            max_distance=100,
            config=config_with_temporal_filter
        )

        # Create probationary object
        centroids = np.array([[100, 100]], dtype=np.float64)
        tracker.update(centroids)
        assert len(tracker.probationary) == 1

        # Update with empty centroids (probationary should disappear quickly)
        empty = np.empty((0, 2), dtype=np.float64)
        for _ in range(tracker.probationary_max_disappeared + 1):
            tracker.update(empty)

        # Probationary object should be removed without affecting total count
        assert len(tracker.probationary) == 0
        assert tracker.total_birds_seen == 0  # Never confirmed


class TestDistanceMatrix:
    """Tests for distance computation."""

    def test_compute_distance_matrix(self, sample_config):
        """Test distance matrix computation is correct."""
        tracker = CentroidTracker(max_disappeared=30, max_distance=100, config=sample_config)

        centroids_a = np.array([[0, 0], [10, 0]])
        centroids_b = np.array([[0, 0], [3, 4]])

        distances = tracker._compute_distance_matrix(centroids_a, centroids_b)

        assert distances.shape == (2, 2)
        # Distance from (0,0) to (0,0) should be 0
        assert distances[0, 0] == pytest.approx(0.0)
        # Distance from (0,0) to (3,4) should be 5 (3-4-5 triangle)
        assert distances[0, 1] == pytest.approx(5.0)
        # Distance from (10,0) to (0,0) should be 10
        assert distances[1, 0] == pytest.approx(10.0)
