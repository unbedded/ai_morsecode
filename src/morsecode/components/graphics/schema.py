"""Graphics component configuration schema with validation.

This module defines the configuration schema for the graphics component
with type validation, units, and constraints.
"""

from dataclasses import dataclass

from util.config.types import CfgField, CfgType, string_choices_field


@dataclass
class GraphicsSchema:
    """Configuration schema for graphics component."""

    mode = CfgField(
        type=CfgType.STRING,
        default="disabled",
        choices=["disabled", "ascii", "braille", "plotly", "pattern"],
        description="Graphics mode: disabled, ascii (SSH), braille (high-res), plotly (interactive), pattern (logging)",
    )

    # Additional fields for GraphicsDisplay compatibility
    display_width_chars = CfgField(
        type=CfgType.INT,
        default=0,
        min=0,
        max=200,
        unit="chars",
        description="Display width: 0=auto terminal detection, or fixed width 40-200",
    )

    display_height_chars = CfgField(
        type=CfgType.INT, default=20, min=10, max=50, unit="chars", description="Display height in characters"
    )

    refresh_rate_fps = CfgField(
        type=CfgType.INT, default=20, min=1, max=60, unit="fps", description="Display refresh rate"
    )

    buffer_size_sec = CfgField(
        type=CfgType.DOUBLE, default=5.0, min=0.5, max=20.0, unit="sec", description="Time-series buffer size"
    )

    log_level = string_choices_field(
        choices=["DEBUG", "INFO", "WARN", "ERROR"],
        default="INFO",
        description_prefix="Override app log level if more verbose",
    )
