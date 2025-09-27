"""Graphics component configuration schema with validation.

This module defines the configuration schema for the graphics component
with type validation, units, and constraints.
"""

from dataclasses import dataclass

from util.config.types import CfgField, CfgType


@dataclass
class GraphicsSchema:
    """Configuration schema for graphics component."""

    enabled = CfgField(
        type=CfgType.BOOL,
        default=True,
        description="Enable graphics display for pattern visualization",
    )

    backend = CfgField(
        type=CfgType.STRING,
        default="ascii",
        choices=["ascii", "braille", "plotly", "pattern"],
        description="Graphics backend: ascii (SSH), braille (high-res), plotly (interactive), pattern (logging)",
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

    enable_debug_logging = CfgField(type=CfgType.BOOL, default=False, description="Enable debug logging for display")

    chunk_size_ms = CfgField(
        type=CfgType.INT,
        default=20,
        min=10,
        max=100,
        unit="ms",
        description="Processing chunk size (should match decoder_app.py actual processing)",
    )

    convolution_interval_ms = CfgField(
        type=CfgType.INT,
        default=20,
        min=10,
        max=2000,
        unit="ms",
        description="Convolution processing interval for probability data (20ms = 50Hz sync with FFT/magnitude)",
    )

    playback_speed = CfgField(
        type=CfgType.DOUBLE,
        default=1.0,
        min=0.1,
        max=10.0,
        description="Playback speed multiplier for time synchronization",
    )
