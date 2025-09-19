"""Audio component implementations for Morse code decoding."""

# Export everything from config modules for easy importing
from .hal import HardwareAbstractionLayer
from .keys import CfgKey, CfgSection
from .schema import ConfigSchema

__all__ = [
    "CfgKey",
    "CfgSection",
    "ConfigSchema",
    "HardwareAbstractionLayer",
]
