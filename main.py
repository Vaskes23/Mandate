#!/usr/bin/env python3
"""
Glass-Morphic macOS Application

Demonstrates glass-morphic (translucent blur) effects on macOS using
PyQt5 and NSVisualEffectView.
"""

import sys
import logging
from PyQt5.QtWidgets import QApplication, QMessageBox
from app.ui.main_window import MainWindow
from app.utils.macos_helpers import require_macos_compatibility

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def main():
    """Application entry point."""
    app = None
    try:
        require_macos_compatibility()

        app = QApplication(sys.argv)
        app.setApplicationName("Glass App")

        window = MainWindow()
        window.show()

        sys.exit(app.exec_())

    except RuntimeError as e:
        logging.error(f"Startup error: {e}")
        if app:
            # Show error dialog if Qt app is initialized
            QMessageBox.critical(None, "Error", str(e))
        else:
            print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        logging.exception("Unexpected error during startup")
        if app:
            QMessageBox.critical(None, "Unexpected Error", f"An unexpected error occurred:\n{e}")
        else:
            print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
