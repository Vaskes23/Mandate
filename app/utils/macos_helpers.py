"""
macOS platform detection and compatibility checking utilities.

This module provides helper functions for verifying macOS version compatibility
before using NSVisualEffectView features.
"""

import platform
import sys


def is_macos() -> bool:
    """
    Check if running on macOS.

    Returns:
        True if on macOS, False otherwise
    """
    return sys.platform == "darwin"


def get_macos_version() -> tuple:
    """
    Get macOS version as a tuple of integers.

    Handles macOS 11+ where platform.mac_ver() may return '10.16' (Rosetta)
    or empty string. Falls back to Darwin version conversion.

    Returns:
        Tuple of (major, minor, patch) or None if not on macOS

    Example:
        >>> get_macos_version()
        (14, 1, 0)  # macOS Sonoma 14.1
    """
    if not is_macos():
        return None

    try:
        # Try platform.mac_ver() first
        version_str = platform.mac_ver()[0]

        # macOS 11+ may return empty string or '10.16' under Rosetta
        if not version_str or version_str == '10.16':
            # Fall back to uname release (Darwin version)
            # Darwin 20.x = macOS 11.x, Darwin 21.x = macOS 12.x, etc.
            darwin_release = platform.uname().release
            darwin_major = int(darwin_release.split('.')[0])

            if darwin_major >= 20:
                # Convert Darwin version to macOS version
                macos_major = darwin_major - 9  # Darwin 20 = macOS 11
                version_str = f"{macos_major}.0.0"

        version_parts = version_str.split(".")
        return tuple(int(part) for part in version_parts)
    except (ValueError, IndexError, AttributeError):
        return None


def check_macos_compatibility() -> bool:
    """
    Check if macOS version supports NSVisualEffectView materials.

    Requires macOS 10.14 (Mojave) or later.

    Returns:
        True if compatible, False otherwise
    """
    if not is_macos():
        return False

    version = get_macos_version()
    if version is None:
        return False

    major = version[0]
    return major >= 11 or (major == 10 and len(version) > 1 and version[1] >= 14)


def require_macos():
    """
    Raise exception if not running on macOS.

    Raises:
        RuntimeError: If not on macOS
    """
    if not is_macos():
        raise RuntimeError(f"This application requires macOS. Current platform: {sys.platform}")


def require_macos_compatibility():
    """
    Raise exception if macOS version is too old for NSVisualEffectView.

    Raises:
        RuntimeError: If not on macOS or version < 10.14
    """
    require_macos()

    if not check_macos_compatibility():
        version = get_macos_version()
        version_str = ".".join(map(str, version)) if version else "unknown"
        raise RuntimeError(
            f"This application requires macOS 10.14 (Mojave) or later. "
            f"Current version: {version_str}"
        )
