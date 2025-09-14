"""Protocol interfaces for the Morse code decoder architecture.

This package contains Protocol definitions that define contracts for all major
components in the system, enabling loose coupling, dependency injection, and
easy testing through mock implementations.
"""

from .audio import AudioSource
from .decoder import MorseDecoder
from .signal import SignalProcessor

__all__ = [
    "AudioSource",
    "SignalProcessor",
    "MorseDecoder",
]
