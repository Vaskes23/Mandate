#!/usr/bin/env python3
"""
Bird Tracker - Real-time Bird Detection and Tracking
Uses classical computer vision techniques for CPU-efficient processing.

Usage:
    CLI Mode:
        python bird_tracker.py --input video.mp4 --output output.mp4

    IPC Mode (for Electron integration):
        python bird_tracker.py --ipc
"""

import cv2
import numpy as np
import json
import argparse
import sys
import os
from pathlib import Path
from typing import Optional, Dict, List, Tuple

from detector import BirdDetector
from tracker import CentroidTracker


class BirdTrackingSystem:
    """
    Complete bird tracking system integrating detection and tracking.
    """

    def __init__(self, config_path: str = "config.json"):
        """
        Initialize bird tracking system.

        Args:
            config_path: Path to configuration JSON file
        """
        # Load configuration
        self.config = self._load_config(config_path)

        # Initialize detector and tracker
        self.detector = BirdDetector(self.config)
        self.tracker = CentroidTracker(
            max_disappeared=self.config['tracking']['max_disappeared'],
            max_distance=self.config['tracking']['max_distance'],
            config=self.config
        )

        # Visualization config
        self.vis_config = self.config['visualization']
        self.output_config = self.config['output']

    def _load_config(self, config_path: str) -> dict:
        """
        Load configuration from JSON file.

        Args:
            config_path: Path to config file

        Returns:
            Configuration dictionary
        """
        config_full_path = Path(__file__).parent / config_path

        if not config_full_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_full_path}")

        with open(config_full_path, 'r') as f:
            return json.load(f)

    def process_video_stream(self, input_path: str, frame_callback=None) -> Dict:
        """
        Process video frame-by-frame and stream tracking data (for Electron integration).

        Args:
            input_path: Path to input video file
            frame_callback: Callback function(frame_num, tracking_data) for each frame

        Returns:
            Dictionary with processing statistics
        """
        # Open video
        cap = cv2.VideoCapture(input_path)

        if not cap.isOpened():
            raise IOError(f"Cannot open video file: {input_path}")

        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Processing loop
        frame_num = 0
        processing_stats = {
            'total_frames': total_frames,
            'processed_frames': 0,
            'max_simultaneous_birds': 0,
            'total_unique_birds': 0,
            'fps': fps,
            'width': width,
            'height': height
        }

        try:
            while True:
                ret, frame = cap.read()

                if not ret:
                    break

                frame_num += 1

                # Detect birds in current frame
                bounding_boxes, mask = self.detector.detect(frame)

                # Get centroids from bounding boxes
                centroids = self.detector.get_centroids(bounding_boxes)

                # Update tracker
                objects, detection_indices = self.tracker.update(centroids)

                # Update statistics
                stats = self.tracker.get_statistics()
                processing_stats['processed_frames'] = frame_num
                processing_stats['max_simultaneous_birds'] = max(
                    processing_stats['max_simultaneous_birds'],
                    stats['current_birds']
                )
                processing_stats['total_unique_birds'] = stats['total_birds_seen']

                # Prepare tracking data for this frame
                tracking_data = {
                    'frame': frame_num,
                    'objects': [],
                    'stats': {
                        'current_birds': stats['current_birds'],
                        'total_birds': stats['total_birds_seen']
                    }
                }

                # Add bird objects with bounding boxes using detection indices
                for object_id, centroid in objects.items():
                    cx, cy = int(centroid[0]), int(centroid[1])

                    # Find corresponding bounding box using detection index
                    detection_idx = detection_indices.get(object_id)
                    if detection_idx is not None and detection_idx < len(bounding_boxes):
                        x, y, w, h = bounding_boxes[detection_idx]
                        tracking_data['objects'].append({
                            'id': object_id,
                            'x': x,
                            'y': y,
                            'w': w,
                            'h': h,
                            'cx': cx,
                            'cy': cy
                        })

                # Send frame data via callback
                if frame_callback:
                    frame_callback(frame_num, tracking_data)

        finally:
            cap.release()

        return processing_stats

    def process_video(self, input_path: str, output_path: Optional[str] = None,
                      progress_callback=None) -> Dict:
        """
        Process entire video with bird detection and tracking.

        Args:
            input_path: Path to input video file
            output_path: Path to output video file (optional)
            progress_callback: Callback function(frame_num, stats) for progress updates

        Returns:
            Dictionary with processing statistics
        """
        # Open video
        cap = cv2.VideoCapture(input_path)

        if not cap.isOpened():
            raise IOError(f"Cannot open video file: {input_path}")

        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Initialize video writer if saving output
        writer = None
        if output_path and self.output_config['save_video']:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        # Processing loop
        frame_num = 0
        processing_stats = {
            'total_frames': total_frames,
            'processed_frames': 0,
            'max_simultaneous_birds': 0,
            'total_unique_birds': 0
        }

        try:
            while True:
                ret, frame = cap.read()

                if not ret:
                    break

                frame_num += 1

                # Detect birds in current frame
                bounding_boxes, mask = self.detector.detect(frame)

                # Get centroids from bounding boxes
                centroids = self.detector.get_centroids(bounding_boxes)

                # Update tracker
                objects, detection_indices = self.tracker.update(centroids)

                # Visualize
                annotated_frame = self._visualize(frame, objects, bounding_boxes, detection_indices)

                # Update statistics
                stats = self.tracker.get_statistics()
                processing_stats['processed_frames'] = frame_num
                processing_stats['max_simultaneous_birds'] = max(
                    processing_stats['max_simultaneous_birds'],
                    stats['current_birds']
                )
                processing_stats['total_unique_birds'] = stats['total_birds_seen']

                # Show display window if enabled
                if self.output_config['show_display']:
                    cv2.imshow('Bird Tracking', annotated_frame)

                    # Check for 'q' key to quit
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

                # Write frame if saving
                if writer is not None:
                    writer.write(annotated_frame)

                # Progress callback
                if progress_callback:
                    progress_callback(frame_num, stats)

        finally:
            # Cleanup
            cap.release()
            if writer is not None:
                writer.release()
            if self.output_config['show_display']:
                cv2.destroyAllWindows()

        return processing_stats

    def _visualize(self, frame: np.ndarray, objects: Dict[int, np.ndarray],
                   bounding_boxes: List[Tuple[int, int, int, int]],
                   detection_indices: Dict[int, int]) -> np.ndarray:
        """
        Draw bounding boxes, IDs, and statistics on frame.

        Args:
            frame: Input frame
            objects: Dictionary of tracked objects {id: centroid}
            bounding_boxes: List of bounding boxes

        Returns:
            Annotated frame
        """
        annotated = frame.copy()

        # Draw each tracked object using detection indices
        for object_id, centroid in objects.items():
            cx, cy = int(centroid[0]), int(centroid[1])

            # Find corresponding bounding box using detection index
            detection_idx = detection_indices.get(object_id)
            if detection_idx is not None and detection_idx < len(bounding_boxes):
                x, y, w, h = bounding_boxes[detection_idx]

                # Draw bounding box
                color = tuple(self.vis_config['box_color'])
                cv2.rectangle(annotated, (x, y), (x + w, y + h),
                             color, self.vis_config['box_thickness'])

                # Draw ID label
                text = f"ID: {object_id}"
                text_color = tuple(self.vis_config['text_color'])
                font_scale = self.vis_config['font_scale']

                # Background for text
                (text_w, text_h), _ = cv2.getTextSize(
                    text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2
                )
                cv2.rectangle(annotated, (x, y - text_h - 10), (x + text_w, y),
                             color, -1)

                # Draw text
                cv2.putText(annotated, text, (x, y - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, font_scale,
                           text_color, 2)

            # Draw centroid
            cv2.circle(annotated, (cx, cy), 4, (0, 0, 255), -1)

            # Draw trajectory if enabled
            if self.vis_config['show_trails']:
                trajectory = self.tracker.get_trajectory(object_id)
                if len(trajectory) > 1:
                    pts = np.array(trajectory, dtype=np.int32)
                    cv2.polylines(annotated, [pts], False, (255, 0, 0), 2)

        # Draw exclusion zones if debug mode enabled
        if self.detector.draw_exclusion_zones and self.detector.exclusion_zones_enabled:
            self._draw_exclusion_zones(annotated)

        # Draw statistics
        stats = self.tracker.get_statistics()
        self._draw_statistics(annotated, stats)

        return annotated

    def _draw_statistics(self, frame: np.ndarray, stats: Dict):
        """
        Draw tracking statistics on frame.

        Args:
            frame: Frame to draw on
            stats: Statistics dictionary
        """
        # Background rectangle
        cv2.rectangle(frame, (10, 10), (400, 100), (0, 0, 0), -1)

        # Text
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        color = (255, 255, 255)
        thickness = 2

        cv2.putText(frame, f"Current Birds: {stats['current_birds']}",
                   (20, 40), font, font_scale, color, thickness)
        cv2.putText(frame, f"Total Birds Detected: {stats['total_birds_seen']}",
                   (20, 75), font, font_scale, color, thickness)

    def _draw_exclusion_zones(self, frame: np.ndarray):
        """
        Draw semi-transparent rectangles over exclusion zones for debugging.

        Args:
            frame: Frame to draw on
        """
        # Create overlay for semi-transparency
        overlay = frame.copy()

        for zone in self.detector.exclusion_zones:
            x = zone.get('x', 0)
            y = zone.get('y', 0)
            width = zone.get('width', 0)
            height = zone.get('height', 0)

            # Draw filled rectangle on overlay
            cv2.rectangle(overlay, (x, y), (x + width, y + height), (0, 0, 255), -1)

            # Draw border
            cv2.rectangle(frame, (x, y), (x + width, y + height), (0, 0, 255), 2)

            # Add label
            label = "EXCLUSION ZONE"
            cv2.putText(frame, label, (x + 5, y + 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        # Blend overlay with original frame (30% opacity)
        cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)


def run_cli_mode(args):
    """
    Run bird tracker in CLI mode.

    Args:
        args: Command line arguments
    """
    print("=" * 60)
    print("Bird Tracking System - CLI Mode")
    print("=" * 60)
    print(f"Input:  {args.input}")
    if args.output:
        print(f"Output: {args.output}")
    print("=" * 60)
    print()

    # Initialize system
    tracker = BirdTrackingSystem(args.config)

    # Progress callback
    def progress_callback(frame_num, stats):
        if frame_num % 30 == 0:  # Print every 30 frames
            print(f"Frame {frame_num}: "
                  f"Current={stats['current_birds']}, "
                  f"Total={stats['total_birds_seen']}")

    # Process video
    try:
        results = tracker.process_video(
            args.input,
            args.output,
            progress_callback=progress_callback
        )

        print()
        print("=" * 60)
        print("Processing Complete!")
        print("=" * 60)
        print(f"Total Frames:          {results['total_frames']}")
        print(f"Processed Frames:      {results['processed_frames']}")
        print(f"Max Simultaneous Birds: {results['max_simultaneous_birds']}")
        print(f"Total Unique Birds:    {results['total_unique_birds']}")
        print("=" * 60)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def run_ipc_mode(args):
    """
    Run bird tracker in IPC mode for Electron integration.
    Reads commands from stdin, writes JSON responses to stdout.

    Args:
        args: Command line arguments
    """
    tracker = BirdTrackingSystem(args.config)

    # Frame callback that outputs tracking data to stdout
    def frame_callback(frame_num, tracking_data):
        output = {
            'type': 'frame_data',
            'data': tracking_data
        }
        print(json.dumps(output), flush=True)

    # Listen for commands from stdin
    for line in sys.stdin:
        try:
            command = json.loads(line.strip())

            if command['action'] == 'start':
                input_path = command['input']

                # Start processing in streaming mode
                output = {'type': 'started'}
                print(json.dumps(output), flush=True)

                results = tracker.process_video_stream(
                    input_path,
                    frame_callback=frame_callback
                )

                # Send completion message
                output = {
                    'type': 'completed',
                    'results': results
                }
                print(json.dumps(output), flush=True)

            elif command['action'] == 'stop':
                # Stop processing (would need threading for proper implementation)
                output = {'type': 'stopped'}
                print(json.dumps(output), flush=True)
                break

        except Exception as e:
            error_output = {
                'type': 'error',
                'message': str(e)
            }
            print(json.dumps(error_output), flush=True)


def main():
    """
    Main entry point.
    """
    parser = argparse.ArgumentParser(
        description='Bird Detection and Tracking System'
    )

    parser.add_argument(
        '--input', '-i',
        type=str,
        help='Input video file path'
    )

    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output video file path (optional)'
    )

    parser.add_argument(
        '--config', '-c',
        type=str,
        default='config.json',
        help='Configuration file path (default: config.json)'
    )

    parser.add_argument(
        '--ipc',
        action='store_true',
        help='Run in IPC mode for Electron integration'
    )

    args = parser.parse_args()

    if args.ipc:
        run_ipc_mode(args)
    else:
        if not args.input:
            parser.error("--input is required in CLI mode")
        run_cli_mode(args)


if __name__ == '__main__':
    main()
