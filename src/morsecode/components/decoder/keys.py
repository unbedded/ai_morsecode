"""Decoder configuration keys and sections.

This module defines the configuration keys and sections for the decoder component
using enum-based configuration patterns for type safety and auto-completion.
"""

from enum import Enum


class CfgKey(Enum):
    """Configuration keys for decoder component."""

    WPM = "wpm"
    DOT_DURATION = "dot_duration"
    TOLERANCE = "tolerance"


class CfgSection(Enum):
    """Configuration sections for decoder component."""

    DECODER = "decoder"
