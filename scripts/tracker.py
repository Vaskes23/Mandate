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

    def __init__(self, max_disappeared: int = 30, max_distance: float = 100):
        """
        Initialize centroid tracker.

        Args:
            max_disappeared: Maximum frames an object can be missing before deregistration
            max_distance: Maximum pixel distance for matching centroids (prevents cross-screen jumps)
        """
        self.next_object_id = 0
        self.objects = OrderedDict()  # {object_id: (cx, cy)}
        self.disappeared = OrderedDict()  # {object_id: disappeared_count}
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance

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

    def update(self, input_centroids: np.ndarray) -> Dict[int, np.ndarray]:
        """
        Update tracker with new detections using Hungarian algorithm.

        Args:
            input_centroids: Array of shape (N, 2) with new centroid coordinates

        Returns:
            Dictionary mapping {object_id: centroid}
        """
        # Case 1: No detections - mark all as disappeared
        if len(input_centroids) == 0:
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1

                # Deregister if disappeared too long
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

        # Compute distance matrix between existing and new centroids
        distances = self._compute_distance_matrix(object_centroids, input_centroids)

        # Apply Hungarian algorithm for optimal assignment
        row_indices, col_indices = linear_sum_assignment(distances)

        # Track which objects and detections have been matched
        used_rows = set()
        used_cols = set()

        for row, col in zip(row_indices, col_indices):
            # Only match if distance is below threshold
            if distances[row, col] < self.max_distance:
                object_id = object_ids[row]

                # Update object position
                self.objects[object_id] = input_centroids[col]
                self.disappeared[object_id] = 0

                # Update trajectory
                self.trajectories[object_id].append(tuple(input_centroids[col]))

                used_rows.add(row)
                used_cols.add(col)

        # Find unmatched objects and detections
        unused_rows = set(range(len(object_ids))) - used_rows
        unused_cols = set(range(len(input_centroids))) - used_cols

        # Handle unmatched existing objects
        for row in unused_rows:
            object_id = object_ids[row]
            self.disappeared[object_id] += 1

            # Deregister if disappeared too long
            if self.disappeared[object_id] > self.max_disappeared:
                self.deregister(object_id)

        # Register new objects for unmatched detections
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
