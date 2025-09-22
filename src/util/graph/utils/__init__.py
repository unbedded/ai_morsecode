"""Utility modules for UILT graphing library."""

from .convenience import (
    compare_backends,
    plot_signal_ascii,
    plot_signal_auto,
    plot_signal_braille,
)
from .decimation import Backend, SmartDecimation

__all__ = [
    "SmartDecimation",
    "Backend",
    "plot_signal_ascii",
    "plot_signal_braille",
    "plot_signal_auto",
    "compare_backends",
]
