"""Convenience functions for quick signal plotting with UILT backends.

Provides high-level interfaces for simple use cases where you just want to plot
a signal quickly without setting up the full UILT architecture.
"""

from collections import deque
from typing import Union

# Avoid circular imports by importing at function level

try:
    import numpy as np

    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None


def plot_signal_ascii(
    data: Union[list[float], deque, "np.ndarray"],
    sample_rate_hz: float | None = None,
    title: str = "Signal",
    width: int = 80,
    height: int = 6,
) -> list[str]:
    """Convenience function for quick ASCII signal plotting.

    This is a high-level interface for simple use cases where you
    just want to plot a single signal quickly using ASCII backend.

    Args:
        data: Signal data to plot
        sample_rate_hz: Optional sample rate for time-axis
        title: Plot title
        width: Plot width in characters
        height: Plot height in rows

    Returns:
        List of strings ready for printing

    Example:
        # Quick signal plot
        signal = [0.1, 0.5, 0.8, 0.3, -0.2, -0.7, -0.4]
        lines = plot_signal_ascii(signal, sample_rate_hz=1000.0, title="My Signal")
        for line in lines:
            print(line)
    """
    from ..backends.ascii_backend import ASCIIBackend

    backend = ASCIIBackend(width, height, title)
    backend.plot(data, sample_rate_hz=sample_rate_hz)
    return backend.render_sparkline()


def plot_signal_braille(
    data: Union[list[float], deque, "np.ndarray"],
    sample_rate_hz: float | None = None,
    title: str = "Signal",
    width: int = 80,
    height: int = 4,
) -> list[str]:
    """Convenience function for quick Braille signal plotting.

    Uses Braille backend for 2x horizontal resolution compared to ASCII.

    Args:
        data: Signal data to plot
        sample_rate_hz: Optional sample rate for time-axis
        title: Plot title
        width: Plot width in characters
        height: Plot height in rows

    Returns:
        List of strings ready for printing

    Example:
        # High-density Braille plot
        signal = [0.1, 0.5, 0.8, 0.3, -0.2, -0.7, -0.4]
        lines = plot_signal_braille(signal, sample_rate_hz=1000.0, title="My Signal")
        for line in lines:
            print(line)
    """
    from ..backends.braille_backend import BrailleBackend

    backend = BrailleBackend(width, height, title)
    backend.plot(data, sample_rate_hz=sample_rate_hz)
    return backend.render_braille()


def plot_signal_auto(
    data: Union[list[float], deque, "np.ndarray"],
    sample_rate_hz: float | None = None,
    title: str = "Signal",
    width: int = 80,
    height: int = 6,
    prefer_braille: bool = True,
) -> tuple[list[str], str]:
    """Auto-select best backend based on terminal capabilities.

    Tries Braille first for higher resolution, falls back to ASCII for compatibility.

    Args:
        data: Signal data to plot
        sample_rate_hz: Optional sample rate for time-axis
        title: Plot title
        width: Plot width in characters
        height: Plot height in rows
        prefer_braille: If True, try Braille first

    Returns:
        Tuple of (plot_lines, backend_used)

    Example:
        # Auto-select backend
        signal = [0.1, 0.5, 0.8, 0.3, -0.2, -0.7, -0.4]
        lines, backend = plot_signal_auto(signal, sample_rate_hz=1000.0)
        print(f"Using {backend} backend:")
        for line in lines:
            print(line)
    """
    if prefer_braille:
        try:
            # Try Braille first
            from ..backends.braille_backend import BrailleBackend

            backend = BrailleBackend(width, height, title)
            backend.plot(data, sample_rate_hz=sample_rate_hz)
            lines = backend.render_braille()
            # Test if we can actually print Braille characters
            test_char = "⠁"
            test_char.encode("utf-8")  # This will raise if no UTF-8 support
            return lines, "BRAILLE"
        except (UnicodeEncodeError, UnicodeError):
            # Fall back to ASCII
            pass

    # Use ASCII backend
    from ..backends.ascii_backend import ASCIIBackend

    backend = ASCIIBackend(width, height, title)
    backend.plot(data, sample_rate_hz=sample_rate_hz)
    lines = backend.render_sparkline()
    return lines, "ASCII"


def compare_backends(
    data: Union[list[float], deque, "np.ndarray"],
    sample_rate_hz: float | None = None,
    title: str = "Signal Comparison",
    width: int = 40,
    height: int = 4,
) -> list[str]:
    """Compare ASCII vs Braille backends side by side.

    Useful for demonstrating the resolution advantage of Braille.
    Uses pre-decimated data to ensure fair comparison between backends.

    Args:
        data: Signal data to plot
        sample_rate_hz: Optional sample rate for time-axis
        title: Plot title
        width: Plot width in characters (for each backend)
        height: Plot height in rows

    Returns:
        List of strings showing both backends side by side

    Example:
        # Compare backends
        signal = [math.sin(i * 0.1) for i in range(100)]
        lines = compare_backends(signal, sample_rate_hz=1000.0)
        for line in lines:
            print(line)
    """
    from ..backends.ascii_backend import ASCIIBackend
    from ..backends.braille_backend import BrailleBackend
    from ..utils.decimation import Backend, SmartDecimation

    # Pre-decimate to ASCII resolution for fair comparison
    # This ensures both backends see the same data points
    ascii_decimated = SmartDecimation.decimate(data, Backend.ASCII, width, height)

    # For Braille, we need to duplicate data points to match 2x resolution
    # Each ASCII point becomes two identical Braille points
    braille_decimated = []
    for value in ascii_decimated:
        braille_decimated.extend([value, value])

    # Render ASCII with pre-decimated data
    ascii_backend = ASCIIBackend(width, height, "ASCII")
    ascii_backend.plot(ascii_decimated, sample_rate_hz=sample_rate_hz)
    ascii_lines = ascii_backend.render_sparkline()

    # Render Braille with duplicated data for 2x resolution
    braille_backend = BrailleBackend(width, height, "Braille")
    braille_backend.plot(braille_decimated, sample_rate_hz=sample_rate_hz)
    braille_lines = braille_backend.render_braille()

    # Combine side by side
    combined = []
    combined.append(f"{title}")
    combined.append("")
    combined.append(f"{'ASCII Backend':<{width}} │ {'Braille Backend (2x resolution)'}")
    combined.append("─" * width + "─┼─" + "─" * width)

    max_lines = max(len(ascii_lines), len(braille_lines))
    for i in range(max_lines):
        ascii_line = ascii_lines[i] if i < len(ascii_lines) else " " * width
        braille_line = braille_lines[i] if i < len(braille_lines) else " " * width

        combined.append(f"{ascii_line} │ {braille_line}")

    return combined
