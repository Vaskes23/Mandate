#!/usr/bin/env python3
"""
Test script to verify bird tracking system installation.
"""

import sys

def test_imports():
    """Test if all required modules can be imported."""
    print("Testing module imports...")

    try:
        import cv2
        print("✓ OpenCV imported successfully (version: {})".format(cv2.__version__))
    except ImportError as e:
        print("✗ OpenCV import failed: {}".format(e))
        return False

    try:
        import numpy as np
        print("✓ NumPy imported successfully (version: {})".format(np.__version__))
    except ImportError as e:
        print("✗ NumPy import failed: {}".format(e))
        return False

    try:
        import scipy
        print("✓ SciPy imported successfully (version: {})".format(scipy.__version__))
    except ImportError as e:
        print("✗ SciPy import failed: {}".format(e))
        return False

    return True


def test_local_modules():
    """Test if local modules can be imported."""
    print("\nTesting local modules...")

    try:
        from detector import BirdDetector, BackgroundSubtractor
        print("✓ detector.py imported successfully")
    except ImportError as e:
        print("✗ detector.py import failed: {}".format(e))
        return False

    try:
        from tracker import CentroidTracker
        print("✓ tracker.py imported successfully")
    except ImportError as e:
        print("✗ tracker.py import failed: {}".format(e))
        return False

    return True


def test_config():
    """Test if config file exists and is valid JSON."""
    print("\nTesting configuration...")

    import json
    from pathlib import Path

    config_path = Path(__file__).parent / 'config.json'

    if not config_path.exists():
        print("✗ config.json not found")
        return False

    print("✓ config.json exists")

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        print("✓ config.json is valid JSON")

        # Check required sections
        required_sections = ['detection', 'tracking', 'visualization', 'output']
        for section in required_sections:
            if section in config:
                print("✓ config.json has '{}' section".format(section))
            else:
                print("✗ config.json missing '{}' section".format(section))
                return False

        return True
    except json.JSONDecodeError as e:
        print("✗ config.json is invalid: {}".format(e))
        return False


def test_video_file():
    """Test if example video file exists."""
    print("\nTesting video file...")

    from pathlib import Path

    video_path = Path(__file__).parent.parent / 'birdsExample.mp4'

    if video_path.exists():
        print("✓ birdsExample.mp4 found at: {}".format(video_path))

        # Check if OpenCV can open it
        import cv2
        cap = cv2.VideoCapture(str(video_path))

        if cap.isOpened():
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            print("✓ Video can be opened")
            print("  Resolution: {}x{}".format(width, height))
            print("  FPS: {}".format(fps))
            print("  Total Frames: {}".format(frame_count))

            cap.release()
            return True
        else:
            print("✗ Video exists but cannot be opened")
            return False
    else:
        print("⚠ birdsExample.mp4 not found (optional)")
        print("  Expected at: {}".format(video_path))
        return True  # Not critical for installation


def test_detector_initialization():
    """Test if detector can be initialized."""
    print("\nTesting detector initialization...")

    try:
        import json
        from pathlib import Path
        from detector import BirdDetector

        config_path = Path(__file__).parent / 'config.json'
        with open(config_path, 'r') as f:
            config = json.load(f)

        detector = BirdDetector(config)
        print("✓ BirdDetector initialized successfully")
        return True
    except Exception as e:
        print("✗ BirdDetector initialization failed: {}".format(e))
        return False


def test_tracker_initialization():
    """Test if tracker can be initialized."""
    print("\nTesting tracker initialization...")

    try:
        from tracker import CentroidTracker

        tracker = CentroidTracker(max_disappeared=30, max_distance=100)
        print("✓ CentroidTracker initialized successfully")
        return True
    except Exception as e:
        print("✗ CentroidTracker initialization failed: {}".format(e))
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Bird Tracking System - Installation Test")
    print("=" * 60)
    print()

    tests = [
        test_imports,
        test_local_modules,
        test_config,
        test_video_file,
        test_detector_initialization,
        test_tracker_initialization
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print("✗ Test failed with exception: {}".format(e))
            results.append(False)
        print()

    print("=" * 60)
    print("Test Results: {}/{} passed".format(sum(results), len(results)))
    print("=" * 60)

    if all(results):
        print("\n✓ All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("  1. Run: python bird_tracker.py --input ../birdsExample.mp4")
        print("  2. See BIRD_TRACKING_QUICKSTART.md for usage guide")
        return 0
    else:
        print("\n✗ Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("  - Install dependencies: pip install -r requirements.txt")
        print("  - Ensure all .py files are in the scripts/ directory")
        print("  - Check config.json is valid")
        return 1


if __name__ == '__main__':
    sys.exit(main())
