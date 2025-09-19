"""Decoder configuration schema with validation.

This module defines the configuration schema for the decoder component
with type validation, units, and constraints.
"""

from dataclasses import dataclass

from util.config.types import CfgField, CfgType


@dataclass
class ConfigSchema:
    """Configuration schema for decoder component."""

    wpm = CfgField(
        type=CfgType.INT,
        default=15,
        min=5,
        max=50,
        unit="wpm",
        description="Words per minute for timing calculations",
    )

    dot_duration = CfgField(
        type=CfgType.DOUBLE,
        default=80.0,
        min=20.0,
        max=300.0,
        unit="ms",
        description="Duration of a dot element in milliseconds",
    )

    tolerance = CfgField(
        type=CfgType.DOUBLE,
        default=0.3,
        min=0.1,
        max=0.8,
        unit="norm",
        description="Tolerance factor for timing variations (0.0-1.0)",
    )
