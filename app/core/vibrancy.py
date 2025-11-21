"""
NSVisualEffectView wrapper utilities for glass-morphic effects.

This module provides a clean Python interface to macOS NSVisualEffectView,
which enables translucent blur effects. It handles the PyObjC bridge and
provides type-safe wrappers around AppKit functionality.
"""

import objc
from ctypes import c_void_p

try:
    from AppKit import (
        NSMakeRect,
        NSVisualEffectView,
        NSVisualEffectStateActive,
        NSVisualEffectStateInactive,
        NSVisualEffectStateFollowsWindowActiveState,
        NSVisualEffectBlendingModeBehindWindow,
        NSVisualEffectBlendingModeWithinWindow,
        NSViewWidthSizable,
        NSViewHeightSizable,
        NSWindowBelow,
        NSAppearance,
    )
    APPKIT_AVAILABLE = True
except ImportError:
    APPKIT_AVAILABLE = False


class VibrancyHelper:
    """
    Helper class for managing NSVisualEffectView.

    This class provides static methods for creating, configuring, and integrating
    NSVisualEffectView instances into PyQt windows.
    """

    # Material constants (NSVisualEffectMaterial enum values)
    MATERIALS = {
        "sidebar": 0,
        "titlebar": 3,
        "sheet": 4,
        "menu": 5,
        "popover": 6,
        "contentBackground": 7,
        "windowBackground": 8,
        "underWindowBackground": 9,
        "headerView": 11,
        "hudWindow": 13,
    }

    # State constants
    STATES = {
        "active": NSVisualEffectStateActive if APPKIT_AVAILABLE else None,
        "inactive": NSVisualEffectStateInactive if APPKIT_AVAILABLE else None,
        "followsWindow": NSVisualEffectStateFollowsWindowActiveState if APPKIT_AVAILABLE else None,
    }

    # Blending mode constants
    BLENDING_MODES = {
        "behindWindow": NSVisualEffectBlendingModeBehindWindow if APPKIT_AVAILABLE else None,
        "withinWindow": NSVisualEffectBlendingModeWithinWindow if APPKIT_AVAILABLE else None,
    }

    @staticmethod
    def is_available() -> bool:
        """
        Check if NSVisualEffectView is available.

        Returns:
            True if AppKit is available, False otherwise
        """
        return APPKIT_AVAILABLE

    @staticmethod
    def create_visual_effect_view(width: int, height: int):
        """
        Create an NSVisualEffectView with the given dimensions.

        Args:
            width: Width in pixels
            height: Height in pixels

        Returns:
            NSVisualEffectView instance configured with auto-resizing

        Raises:
            RuntimeError: If AppKit is not available
        """
        if not APPKIT_AVAILABLE:
            raise RuntimeError("AppKit is not available")

        frame = NSMakeRect(0, 0, width, height)
        view = NSVisualEffectView.alloc().initWithFrame_(frame)
        view.setWantsLayer_(True)
        view.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        return view

    @staticmethod
    def configure_visual_effect_view(view, material: str, blending_mode: str, state: str, emphasized: bool = False):
        """
        Configure an NSVisualEffectView with the specified properties.

        Args:
            view: NSVisualEffectView instance
            material: Material type (e.g., 'sidebar', 'menu')
            blending_mode: 'behindWindow' or 'withinWindow'
            state: 'active', 'inactive', or 'followsWindow'
            emphasized: Whether to add emphasis/tint

        Raises:
            ValueError: If material, blending_mode, or state is invalid
            RuntimeError: If AppKit is not available
        """
        if not APPKIT_AVAILABLE:
            raise RuntimeError("AppKit is not available")

        if material not in VibrancyHelper.MATERIALS:
            raise ValueError(f"Invalid material: {material}")
        view.setMaterial_(VibrancyHelper.MATERIALS[material])

        if blending_mode not in VibrancyHelper.BLENDING_MODES:
            raise ValueError(f"Invalid blending mode: {blending_mode}")
        view.setBlendingMode_(VibrancyHelper.BLENDING_MODES[blending_mode])

        if state not in VibrancyHelper.STATES:
            raise ValueError(f"Invalid state: {state}")
        view.setState_(VibrancyHelper.STATES[state])

        if hasattr(view, "setEmphasized_"):
            view.setEmphasized_(emphasized)

    @staticmethod
    def add_visual_effect_to_window(qt_window, visual_effect_view):
        """
        Add an NSVisualEffectView to a Qt window's native view hierarchy.

        The view is positioned below all existing content so it acts as a background.

        Args:
            qt_window: PyQt5 QMainWindow instance
            visual_effect_view: NSVisualEffectView instance

        Raises:
            RuntimeError: If AppKit is unavailable or window setup fails
        """
        if not APPKIT_AVAILABLE:
            raise RuntimeError("AppKit is not available")

        try:
            # Get native macOS window from Qt
            ns_view = objc.objc_object(c_void_p=qt_window.winId().__int__())
            ns_window = ns_view.window()

            if ns_window is None:
                raise RuntimeError("Failed to get native window")

            # Add visual effect view below all content
            content_view = ns_window.contentView()
            content_view.addSubview_positioned_relativeTo_(visual_effect_view, NSWindowBelow, None)

        except Exception as e:
            raise RuntimeError(f"Failed to add visual effect view: {e}")

    @staticmethod
    def set_window_appearance(qt_window, appearance_name: str):
        """
        Set the appearance mode for a Qt window.

        Args:
            qt_window: PyQt5 QMainWindow instance
            appearance_name: Appearance name (e.g., 'NSAppearanceNameVibrantDark')

        Raises:
            RuntimeError: If AppKit is not available
        """
        if not APPKIT_AVAILABLE:
            raise RuntimeError("AppKit is not available")

        try:
            ns_view = objc.objc_object(c_void_p=qt_window.winId().__int__())
            ns_window = ns_view.window()

            if ns_window:
                appearance = NSAppearance.appearanceNamed_(appearance_name)
                if appearance:
                    ns_window.setAppearance_(appearance)
        except Exception:
            pass

    @staticmethod
    def set_window_alpha(qt_window, alpha: float):
        """
        Set the transparency level of a Qt window.

        Args:
            qt_window: PyQt5 QMainWindow instance
            alpha: Transparency (0.0 = transparent, 1.0 = opaque)

        Raises:
            RuntimeError: If AppKit is not available
        """
        if not APPKIT_AVAILABLE:
            raise RuntimeError("AppKit is not available")

        try:
            ns_view = objc.objc_object(c_void_p=qt_window.winId().__int__())
            ns_window = ns_view.window()

            if ns_window:
                ns_window.setAlphaValue_(max(0.0, min(1.0, alpha)))
        except Exception:
            pass

    @staticmethod
    def configure_window_for_transparency(qt_window):
        """
        Configure a Qt window for transparency and full-size content view.

        Sets the titlebar as transparent and enables full-size content view
        (edge-to-edge content).

        Args:
            qt_window: PyQt5 QMainWindow instance

        Raises:
            RuntimeError: If AppKit is not available
        """
        if not APPKIT_AVAILABLE:
            raise RuntimeError("AppKit is not available")

        try:
            ns_view = objc.objc_object(c_void_p=qt_window.winId().__int__())
            ns_window = ns_view.window()

            if ns_window:
                ns_window.setTitlebarAppearsTransparent_(True)
                NSFullSizeContentViewWindowMask = 1 << 15
                style_mask = ns_window.styleMask()
                ns_window.setStyleMask_(style_mask | NSFullSizeContentViewWindowMask)
        except Exception:
            pass
