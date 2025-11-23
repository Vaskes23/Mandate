"""
Bird Tracking Module
Implements centroid-based tracking with Hungarian algorithm for optimal ID assignment.
"""

import numpy as np
from scipy.optimize import linear_sum_assignment
from collections import OrderedDict, deque
from typing import Dict, List, Tuple, Optional


class CentroidTracker:
    """
    Tracks objects using centroid distance minimization with Hungarian algorithm.
    Handles object registration, deregistration, and ID persistence across frames.
    """

    def __init__(self, max_disappeared: int = 30, max_distance: float = 100, config: dict = None):
        """
        Initialize centroid tracker.

        Args:
            max_disappeared: Maximum frames an object can be missing before deregistration
            max_distance: Maximum pixel distance for matching centroids (prevents cross-screen jumps)
            config: Optional configuration dictionary for temporal filtering
        """
        self.next_object_id = 0
        self.objects = OrderedDict()  # {object_id: (cx, cy)}
        self.disappeared = OrderedDict()  # {object_id: disappeared_count}
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance

        # Temporal filter configuration
        if config:
            self.temporal_filter_enabled = config.get('temporal_filter', {}).get('enabled', False)
            self.min_confirm_frames = config.get('temporal_filter', {}).get('min_confirm_frames', 15)
            self.min_move_distance = config.get('temporal_filter', {}).get('min_move_distance', 50.0)
        else:
            self.temporal_filter_enabled = False
            self.min_confirm_frames = 15
            self.min_move_distance = 50.0

        # Probationary tracking for temporal filtering
        self.next_probationary_id = 0
        self.probationary = OrderedDict()  # {prob_id: (cx, cy)} - current position
        self.probationary_initial = OrderedDict()  # {prob_id: (cx, cy)} - initial position
        self.probationary_frames = OrderedDict()  # {prob_id: frame_count}
        self.probationary_disappeared = OrderedDict()  # {prob_id: disappeared_count}
        self.probationary_trajectories = OrderedDict()  # {prob_id: deque(positions)} - for cumulative path
        self.probationary_max_disappeared = 5  # Fast cleanup for probationary objects

        # For trajectory visualization
        self.trajectories = {}  # {object_id: deque([(cx, cy), ...])}
        self.max_trail_length = 30

        # Statistics
        self.total_birds_seen = 0

    def register(self, centroid: np.ndarray) -> int:
        """
        Register a new object with the next available ID.

        Args:
            centroid: (cx, cy) coordinates

        Returns:
            The assigned object ID
        """
        object_id = self.next_object_id
        self.objects[object_id] = centroid
        self.disappeared[object_id] = 0
        self.trajectories[object_id] = deque(maxlen=self.max_trail_length)
        self.trajectories[object_id].append(tuple(centroid))
        self.next_object_id += 1
        self.total_birds_seen += 1
        return object_id

    def deregister(self, object_id: int):
        """
        Remove an object from tracking.

        Args:
            object_id: ID of object to remove
        """
        del self.objects[object_id]
        del self.disappeared[object_id]
        if object_id in self.trajectories:
            del self.trajectories[object_id]

    def register_probationary(self, centroid: np.ndarray) -> int:
        """
        Register a new probationary object (unconfirmed detection).

        Args:
            centroid: (cx, cy) coordinates

        Returns:
            The assigned probationary ID
        """
        prob_id = self.next_probationary_id
        self.probationary[prob_id] = centroid
        self.probationary_initial[prob_id] = centroid.copy()
        self.probationary_frames[prob_id] = 1
        self.probationary_disappeared[prob_id] = 0
        self.probationary_trajectories[prob_id] = deque([tuple(centroid)], maxlen=self.min_confirm_frames)
        self.next_probationary_id += 1
        return prob_id

    def deregister_probationary(self, prob_id: int):
        """
        Remove a probationary object (silent - no statistics update).

        Args:
            prob_id: Probationary ID to remove
        """
        if prob_id in self.probationary:
            del self.probationary[prob_id]
            del self.probationary_initial[prob_id]
            del self.probationary_frames[prob_id]
            del self.probationary_disappeared[prob_id]
            del self.probationary_trajectories[prob_id]

    def promote_probationary(self, prob_id: int) -> int:
        """
        Promote a probationary object to confirmed bird status.

        Args:
            prob_id: Probationary ID to promote

        Returns:
            The new confirmed object ID
        """
        centroid = self.probationary[prob_id]
        self.deregister_probationary(prob_id)
        return self.register(centroid)

    def check_probationary_promotion(self, prob_id: int) -> bool:
        """
        Check if a probationary object should be promoted to confirmed.
        Uses cumulative path length instead of net displacement to catch birds that
        circle, hover, or fly toward the camera.

        Args:
            prob_id: Probationary ID to check

        Returns:
            True if object should be promoted, False otherwise
        """
        if self.probationary_frames[prob_id] < self.min_confirm_frames:
            return False

        # Calculate cumulative path length (distance traveled along trajectory)
        trajectory = list(self.probationary_trajectories[prob_id])
        if len(trajectory) < 2:
            return False

        cumulative_distance = 0.0
        for i in range(1, len(trajectory)):
            prev_pos = np.array(trajectory[i-1])
            curr_pos = np.array(trajectory[i])
            cumulative_distance += np.linalg.norm(curr_pos - prev_pos)

        # Also check net displacement as a secondary validation
        initial_pos = self.probationary_initial[prob_id]
        current_pos = self.probationary[prob_id]
        net_displacement = np.linalg.norm(current_pos - initial_pos)

        # Promote if EITHER cumulative path OR net displacement exceeds threshold
        # This catches both straight-line flyers and birds that circle/hover
        return cumulative_distance >= self.min_move_distance or net_displacement >= self.min_move_distance

    def update(self, input_centroids: np.ndarray) -> Dict[int, np.ndarray]:
        """
        Update tracker with new detections using Hungarian algorithm.
        Implements two-phase tracking: probationary validation, then confirmed tracking.

        Args:
            input_centroids: Array of shape (N, 2) with new centroid coordinates

        Returns:
            Dictionary mapping {object_id: centroid} for confirmed objects only
        """
        # If temporal filtering is disabled, use original behavior
        if not self.temporal_filter_enabled:
            return self._update_without_temporal_filter(input_centroids)

        # Phase 1: Handle no detections case
        if len(input_centroids) == 0:
            # Mark confirmed objects as disappeared
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)

            # Mark probationary objects as disappeared (faster cleanup)
            for prob_id in list(self.probationary_disappeared.keys()):
                self.probationary_disappeared[prob_id] += 1
                if self.probationary_disappeared[prob_id] > self.probationary_max_disappeared:
                    self.deregister_probationary(prob_id)

            return self.objects

        # Phase 2: Match confirmed objects with detections
        remaining_centroids = input_centroids.copy()
        used_detection_indices = set()

        if len(self.objects) > 0:
            object_ids = list(self.objects.keys())
            object_centroids = np.array(list(self.objects.values()))

            distances = self._compute_distance_matrix(object_centroids, remaining_centroids)
            row_indices, col_indices = linear_sum_assignment(distances)

            used_rows = set()

            for row, col in zip(row_indices, col_indices):
                if distances[row, col] < self.max_distance:
                    object_id = object_ids[row]
                    self.objects[object_id] = remaining_centroids[col]
                    self.disappeared[object_id] = 0
                    self.trajectories[object_id].append(tuple(remaining_centroids[col]))
                    used_rows.add(row)
                    used_detection_indices.add(col)

            # Handle unmatched confirmed objects
            unused_rows = set(range(len(object_ids))) - used_rows
            for row in unused_rows:
                object_id = object_ids[row]
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)

        # Phase 3: Match probationary objects with remaining detections
        remaining_detection_indices = set(range(len(remaining_centroids))) - used_detection_indices

        # Track which probationary objects were matched
        matched_prob_ids = set()

        if len(self.probationary) > 0 and len(remaining_detection_indices) > 0:
            prob_ids = list(self.probationary.keys())
            prob_centroids = np.array(list(self.probationary.values()))

            # Convert to sorted list ONCE to guarantee consistent ordering
            remaining_indices_list = sorted(remaining_detection_indices)
            remaining_centroids_subset = remaining_centroids[remaining_indices_list]

            distances = self._compute_distance_matrix(prob_centroids, remaining_centroids_subset)
            row_indices, col_indices = linear_sum_assignment(distances)

            for row, col in zip(row_indices, col_indices):
                if distances[row, col] < self.max_distance:
                    prob_id = prob_ids[row]
                    actual_detection_idx = remaining_indices_list[col]

                    # Update probationary object
                    new_centroid = remaining_centroids[actual_detection_idx]
                    self.probationary[prob_id] = new_centroid
                    self.probationary_disappeared[prob_id] = 0
                    self.probationary_frames[prob_id] += 1
                    self.probationary_trajectories[prob_id].append(tuple(new_centroid))

                    # Check if should be promoted to confirmed
                    if self.check_probationary_promotion(prob_id):
                        self.promote_probationary(prob_id)
                    # Check if failed to move enough after min_confirm_frames
                    elif self.probationary_frames[prob_id] >= self.min_confirm_frames:
                        # Failed validation - deregister silently
                        self.deregister_probationary(prob_id)

                    matched_prob_ids.add(prob_id)
                    used_detection_indices.add(actual_detection_idx)

        # CRITICAL FIX: Age ALL unmatched probationary objects, not just when detections exist
        # This prevents memory leaks and stale probationary tracks
        for prob_id in list(self.probationary.keys()):
            if prob_id not in matched_prob_ids:
                self.probationary_disappeared[prob_id] += 1
                if self.probationary_disappeared[prob_id] > self.probationary_max_disappeared:
                    self.deregister_probationary(prob_id)

        # Phase 4: Register new probationary objects for remaining detections
        final_remaining_indices = set(range(len(remaining_centroids))) - used_detection_indices
        for idx in final_remaining_indices:
            self.register_probationary(remaining_centroids[idx])

        return self.objects

    def _update_without_temporal_filter(self, input_centroids: np.ndarray) -> Dict[int, np.ndarray]:
        """
        Original update logic without temporal filtering (for backwards compatibility).

        Args:
            input_centroids: Array of shape (N, 2) with new centroid coordinates

        Returns:
            Dictionary mapping {object_id: centroid}
        """
        # Case 1: No detections - mark all as disappeared
        if len(input_centroids) == 0:
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)
            return self.objects

        # Case 2: No existing objects - register all detections
        if len(self.objects) == 0:
            for centroid in input_centroids:
                self.register(centroid)
            return self.objects

        # Case 3: Match existing objects to new detections
        object_ids = list(self.objects.keys())
        object_centroids = np.array(list(self.objects.values()))

        distances = self._compute_distance_matrix(object_centroids, input_centroids)
        row_indices, col_indices = linear_sum_assignment(distances)

        used_rows = set()
        used_cols = set()

        for row, col in zip(row_indices, col_indices):
            if distances[row, col] < self.max_distance:
                object_id = object_ids[row]
                self.objects[object_id] = input_centroids[col]
                self.disappeared[object_id] = 0
                self.trajectories[object_id].append(tuple(input_centroids[col]))
                used_rows.add(row)
                used_cols.add(col)

        unused_rows = set(range(len(object_ids))) - used_rows
        unused_cols = set(range(len(input_centroids))) - used_cols

        for row in unused_rows:
            object_id = object_ids[row]
            self.disappeared[object_id] += 1
            if self.disappeared[object_id] > self.max_disappeared:
                self.deregister(object_id)

        for col in unused_cols:
            self.register(input_centroids[col])

        return self.objects

    def _compute_distance_matrix(self, centroids_a: np.ndarray, centroids_b: np.ndarray) -> np.ndarray:
        """
        Compute Euclidean distance matrix between two sets of centroids.

        Args:
            centroids_a: Array of shape (M, 2)
            centroids_b: Array of shape (N, 2)

        Returns:
            Distance matrix of shape (M, N)
        """
        # Expand dimensions for broadcasting
        a_expanded = centroids_a[:, np.newaxis, :]  # (M, 1, 2)
        b_expanded = centroids_b[np.newaxis, :, :]  # (1, N, 2)

        # Compute Euclidean distances
        distances = np.linalg.norm(a_expanded - b_expanded, axis=2)

        return distances

    def get_trajectory(self, object_id: int) -> List[Tuple[int, int]]:
        """
        Get the trajectory of an object.

        Args:
            object_id: ID of object

        Returns:
            List of (cx, cy) tuples representing the path
        """
        if object_id in self.trajectories:
            return list(self.trajectories[object_id])
        return []

    def get_statistics(self) -> Dict[str, int]:
        """
        Get tracking statistics.

        Returns:
            Dictionary with current count and total seen
        """
        return {
            'current_birds': len(self.objects),
            'total_birds_seen': self.total_birds_seen
        }

    def reset(self):
        """
        Reset tracker to initial state.
        """
        self.next_object_id = 0
        self.objects = OrderedDict()
        self.disappeared = OrderedDict()
        self.trajectories = {}
        self.total_birds_seen = 0
