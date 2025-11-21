"""
Base glass-morphic window class.

This module provides GlassMorphicWindow, a reusable QMainWindow subclass that
integrates macOS NSVisualEffectView for creating windows with translucent blur effects.
"""

import logging

from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import Qt, QTimer

from app.config import GlassConfig, DEFAULT_CONFIG
from app.core.vibrancy import VibrancyHelper
from app.utils.macos_helpers import require_macos_compatibility

# Set up logging
logger = logging.getLogger(__name__)

# Cache NSMakeRect at module scope to avoid repeated imports
try:
    from AppKit import NSMakeRect
    _NS_MAKE_RECT = NSMakeRect
except ImportError:
    _NS_MAKE_RECT = None


class GlassMorphicWindow(QMainWindow):
    """
    Base window class with glass-morphic (translucent blur) effect.

    This class creates a frameless, transparent Qt window with macOS NSVisualEffectView
    positioned behind all content, providing an authentic glass blur effect.

    Features:
        - Frameless window design
        - Background blur using NSVisualEffectView
        - Drag-to-move functionality
        - Runtime configuration updates
        - Auto-resizing blur view

    Usage:
        window = GlassMorphicWindow(config=my_glass_config)
        window.show()
    """

    def __init__(self, config: GlassConfig = None, parent=None):
        """
        Initialize a glass-morphic window.

        Args:
            config: GlassConfig instance specifying blur material, transparency, etc.
                   If None, uses DEFAULT_CONFIG from app.config.
            parent: Parent widget (optional)

        Raises:
            RuntimeError: If not running on macOS 10.14+ or AppKit is unavailable
        """
        super().__init__(parent)

        require_macos_compatibility()

        if not VibrancyHelper.is_available():
            raise RuntimeError("NSVisualEffectView is not available on this system.")

        self.glass_config = config or DEFAULT_CONFIG
        self._visual_effect_view = None

        self._setup_window_flags()
        self._setup_transparency()

    def _setup_window_flags(self):
        """Configure window with native macOS chrome for proper resizing."""
        # Use standard window flags - macOS will provide native resize and window controls
        self.setWindowFlags(Qt.Window)
        # Window will have standard macOS titlebar controls (close, minimize, maximize)
        # The vibrancy effect will be applied to the entire content area

    def _setup_transparency(self):
        """Enable window transparency (required for blur effect)."""
        self.setAttribute(Qt.WA_TranslucentBackground, True)

    def showEvent(self, event):
        """
        Set up glass effect when window is first shown.

        The NSVisualEffectView requires a native window handle, which is only
        available after the window is shown. We use QTimer.singleShot to defer
        setup until the event loop processes the show event.

        Args:
            event: QShowEvent
        """
        super().showEvent(event)

        if self._visual_effect_view is None:
            QTimer.singleShot(0, self._setup_glass_effect)

    def _setup_glass_effect(self):
        """
        Create and configure NSVisualEffectView with current glass_config.

        This method:
        1. Creates an NSVisualEffectView
        2. Configures material, blending mode, and state
        3. Adds it to the window below all Qt widgets
        4. Sets window appearance and alpha
        """
        try:
            self._visual_effect_view = VibrancyHelper.create_visual_effect_view(
                self.width(), self.height()
            )

            VibrancyHelper.configure_visual_effect_view(
                self._visual_effect_view,
                material=self.glass_config.material.value,
                blending_mode=self.glass_config.blending_mode.value,
                state=self.glass_config.state.value,
                emphasized=self.glass_config.emphasized,
            )

            VibrancyHelper.add_visual_effect_to_window(self, self._visual_effect_view)
            VibrancyHelper.configure_window_for_transparency(self)
            VibrancyHelper.set_window_appearance(self, self.glass_config.appearance.value)
            VibrancyHelper.set_window_alpha(self, self.glass_config.window_alpha)

        except Exception as e:
            logger.exception("Failed to set up glass effect")
            # Re-raise to make failures visible during development
            raise

    def update_glass_config(self, config: GlassConfig):
        """
        Update the glass effect with a new configuration.

        This reconfigures the existing NSVisualEffectView without recreating it.

        Args:
            config: New GlassConfig instance
        """
        self.glass_config = config

        if self._visual_effect_view is not None:
            try:
                VibrancyHelper.configure_visual_effect_view(
                    self._visual_effect_view,
                    material=config.material.value,
                    blending_mode=config.blending_mode.value,
                    state=config.state.value,
                    emphasized=config.emphasized,
                )
                VibrancyHelper.set_window_appearance(self, config.appearance.value)
                VibrancyHelper.set_window_alpha(self, config.window_alpha)
            except Exception as e:
                logger.exception("Failed to update glass effect")
                raise

    def resizeEvent(self, event):
        """
        Update visual effect view frame when window is resized.

        Uses cached NSMakeRect to avoid repeated imports on every resize event.

        Args:
            event: QResizeEvent
        """
        super().resizeEvent(event)

        if self._visual_effect_view is not None and _NS_MAKE_RECT is not None:
            try:
                frame = _NS_MAKE_RECT(0, 0, self.width(), self.height())
                self._visual_effect_view.setFrame_(frame)
            except Exception:
                pass

