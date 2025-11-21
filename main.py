#!/usr/bin/env python3
"""
Glass-Morphic macOS Application

Demonstrates glass-morphic (translucent blur) effects on macOS using
PyQt5 and NSVisualEffectView.
"""

import sys
from PyQt5.QtWidgets import QApplication
from app.ui.main_window import MainWindow
from app.utils.macos_helpers import require_macos_compatibility


def main():
    """Application entry point."""
    try:
        require_macos_compatibility()

        app = QApplication(sys.argv)
        app.setApplicationName("Glass App")

        window = MainWindow()
        window.show()

        sys.exit(app.exec_())

    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
