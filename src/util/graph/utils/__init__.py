"""Utility modules for UILT graphing library."""

from .decimation import SmartDecimation, Backend
from .convenience import (
    plot_signal_ascii,
    plot_signal_braille,
    plot_signal_auto,
    compare_backends,
)

__all__ = [
    "SmartDecimation",
    "Backend",
    "plot_signal_ascii",
    "plot_signal_braille",
    "plot_signal_auto",
    "compare_backends",
]