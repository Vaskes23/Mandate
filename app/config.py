"""
Configuration settings for glass-morphic windows.

This module defines enumerations and configuration classes for controlling
the appearance of glass-morphic (translucent blur) windows.
"""

from enum import Enum


class MaterialType(Enum):
    """
    NSVisualEffectView material types (macOS 10.14+).

    Each material provides a different blur intensity and tint:
    - SIDEBAR: Standard sidebar appearance (default)
    - TITLEBAR: Titlebar-style blur
    - MENU: Menu background style
    - POPOVER: Popover background style
    - HUD_WINDOW: Heads-up display style
    - CONTENT_BACKGROUND: Content area background
    """

    SIDEBAR = "sidebar"
    TITLEBAR = "titlebar"
    HEADER_VIEW = "headerView"
    MENU = "menu"
    POPOVER = "popover"
    HUD_WINDOW = "hudWindow"
    CONTENT_BACKGROUND = "contentBackground"
    WINDOW_BACKGROUND = "windowBackground"
    UNDER_WINDOW_BACKGROUND = "underWindowBackground"
    SHEET = "sheet"


class BlendingMode(Enum):
    """
    Visual effect blending modes.

    - BEHIND_WINDOW: Blur content behind the window (desktop/other windows)
    - WITHIN_WINDOW: Blur content within the window itself
    """

    BEHIND_WINDOW = "behindWindow"
    WITHIN_WINDOW = "withinWindow"


class VibrancyState(Enum):
    """
    Visual effect state.

    - ACTIVE: Always show blur effect
    - INACTIVE: Only show blur when window is inactive
    - FOLLOWS_WINDOW: Automatically switch based on window active state
    """

    ACTIVE = "active"
    INACTIVE = "inactive"
    FOLLOWS_WINDOW = "followsWindow"


class AppearanceMode(Enum):
    """
    macOS appearance modes.

    - VIBRANT_DARK: Dark mode with vibrancy (recommended)
    - VIBRANT_LIGHT: Light mode with vibrancy
    - AQUA: Standard light mode
    - DARK_AQUA: Standard dark mode
    """

    AQUA = "NSAppearanceNameAqua"
    VIBRANT_LIGHT = "NSAppearanceNameVibrantLight"
    VIBRANT_DARK = "NSAppearanceNameVibrantDark"
    DARK_AQUA = "NSAppearanceNameDarkAqua"


class GlassConfig:
    """
    Configuration for glass-morphic window appearance.

    This class encapsulates all visual effect settings for a glass-morphic window.
    """

    def __init__(
        self,
        material: MaterialType = MaterialType.SIDEBAR,
        blending_mode: BlendingMode = BlendingMode.BEHIND_WINDOW,
        state: VibrancyState = VibrancyState.ACTIVE,
        appearance: AppearanceMode = AppearanceMode.VIBRANT_DARK,
        window_alpha: float = 0.95,
        emphasized: bool = False,
    ):
        """
        Initialize glass configuration.

        Args:
            material: The material type (affects blur intensity and tint)
            blending_mode: Where the blur is applied (behind or within window)
            state: When the blur is visible (always, never, or auto)
            appearance: Light or dark appearance mode
            window_alpha: Window opacity (0.0 = transparent, 1.0 = opaque)
            emphasized: Whether to add emphasis/tint to the blur effect
        """
        self.material = material
        self.blending_mode = blending_mode
        self.state = state
        self.appearance = appearance
        self.window_alpha = max(0.0, min(1.0, window_alpha))
        self.emphasized = emphasized


# Default configuration for glass-morphic windows
DEFAULT_CONFIG = GlassConfig(
    material=MaterialType.SIDEBAR,
    blending_mode=BlendingMode.BEHIND_WINDOW,
    state=VibrancyState.ACTIVE,
    appearance=AppearanceMode.VIBRANT_DARK,
    window_alpha=0.95,
    emphasized=False,
)

# Window defaults
DEFAULT_WINDOW_SIZE = (800, 600)
DEFAULT_WINDOW_TITLE = "Glass App"
