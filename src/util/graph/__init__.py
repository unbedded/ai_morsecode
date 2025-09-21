"""UTIL Graphing Library - Universal Interface for Live Telemetry (UILT).

A high-performance asyncio-based graphing utility with matplotlib-like interface
that supports multiple output backends (ASCII, Braille) for real-time data
visualization. Designed for SSH-friendly debugging and live telemetry display.

Key Features:
- Asyncio-driven: Non-blocking real-time updates
- Backend Agnostic: ASCII, Braille, and future matplotlib GUI
- Matplotlib-like API: Familiar interface for easy adoption
- Backend-aware decimation: Optimized for each output format
- 2x horizontal resolution with Braille backend
- C++ porting considerations

Example Usage:

Quick plotting:
    from util.graph import plot_signal_ascii, plot_signal_braille

    data = [0.1, 0.5, 0.8, 0.3, -0.2, -0.7, -0.4]

    # ASCII plot
    lines = plot_signal_ascii(data, sample_rate_hz=1000.0)
    for line in lines:
        print(line)

    # High-resolution Braille plot
    lines = plot_signal_braille(data, sample_rate_hz=1000.0)
    for line in lines:
        print(line)

Backend comparison:
    from util.graph import compare_backends

    lines = compare_backends(data, sample_rate_hz=1000.0)
    for line in lines:
        print(line)

Direct backend usage:
    from util.graph import ASCIIBackend, BrailleBackend

    backend = BrailleBackend(width=80, height=4)
    backend.plot(data, sample_rate_hz=1000.0)
    lines = backend.render_braille()
"""

# Core components
from .core.time_axis import TimeAxis
from .core.data_buffer import DataBuffer

# Backend implementations
from .backends.ascii_backend import ASCIIBackend
from .backends.braille_backend import BrailleBackend

# Utilities
from .utils.decimation import SmartDecimation, Backend

# Convenience functions (imported on demand to avoid circular imports)
def plot_signal_ascii(*args, **kwargs):
    from .utils.convenience import plot_signal_ascii as _plot_signal_ascii
    return _plot_signal_ascii(*args, **kwargs)

def plot_signal_braille(*args, **kwargs):
    from .utils.convenience import plot_signal_braille as _plot_signal_braille
    return _plot_signal_braille(*args, **kwargs)

def plot_signal_auto(*args, **kwargs):
    from .utils.convenience import plot_signal_auto as _plot_signal_auto
    return _plot_signal_auto(*args, **kwargs)

def compare_backends(*args, **kwargs):
    from .utils.convenience import compare_backends as _compare_backends
    return _compare_backends(*args, **kwargs)

__all__ = [
    # Core components
    "TimeAxis",
    "DataBuffer",

    # Backends
    "ASCIIBackend",
    "BrailleBackend",

    # Utilities
    "SmartDecimation",
    "Backend",

    # Convenience functions
    "plot_signal_ascii",
    "plot_signal_braille",
    "plot_signal_auto",
    "compare_backends",
]

__version__ = "0.1.0"