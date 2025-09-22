"""Constants for graphics debug display component.

This module centralizes all magic numbers, thresholds, and configuration values
to eliminate inconsistencies and improve maintainability.
"""

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class DisplayConstants:
    """Display layout and sizing constants."""

    # Chart dimensions and margins
    MIN_CHART_WIDTH: Final[int] = 40
    CHART_MARGIN_CHARS: Final[int] = 4  # 2 chars on each side
    MIN_CHART_HEIGHT: Final[int] = 6

    # Probability chart layout (4 charts side-by-side)
    PROBABILITY_CHART_COUNT: Final[int] = 4
    MIN_PROB_CHART_WIDTH: Final[int] = 5
    PROB_CHART_MARGIN: Final[int] = 4

    # Layout section sizes (proportional)
    HEADER_SIZE: Final[int] = 3
    MAIN_CHART_SIZE: Final[int] = 6
    STATUS_SIZE: Final[int] = 6

    # Alternative compact layout
    COMPACT_HEADER_SIZE: Final[int] = 3
    COMPACT_CHART_SIZE: Final[int] = 14
    COMPACT_STATUS_SIZE: Final[int] = 5


@dataclass(frozen=True)
class BufferConstants:
    """Buffer management and data processing constants."""

    # Placeholder data handling
    PLACEHOLDER_SKIP_THRESHOLD: Final[int] = 50  # Skip first N entries (was inconsistent 50/100)

    # Buffer sizing
    DEFAULT_BUFFER_UPDATE_RATE_HZ: Final[int] = 1000  # Assume ~1000Hz for buffer calculations
    DECODED_TEXT_MAX_LENGTH: Final[int] = 100  # Keep last N characters

    # Priming data counts
    FFT_PRIMING_POINTS: Final[int] = 50
    SIGNAL_PRIMING_POINTS: Final[int] = 100  # More points for smoother signal display


@dataclass(frozen=True)
class SignalConstants:
    """Signal processing and visualization constants."""

    # Sample rates and timing
    CHART_SAMPLE_RATE_HZ: Final[float] = 100.0  # For UILT backend plotting

    # Chart rendering levels
    SPARKLINE_LEVELS_PER_ROW: Final[int] = 8
    FFT_CHART_ROWS: Final[int] = 20  # 20 rows × 8 levels = 160 total levels (4x taller)
    PROBABILITY_CHART_ROWS: Final[int] = 3  # 3 rows × 8 levels = 24 total levels (3x char tall)

    # Sparkline characters (8 levels of block height)
    SPARKLINE_CHARS: Final[str] = "▁▂▃▄▅▆▇█"

    # Scaling and thresholds
    MIN_SCALE_VALUE: Final[float] = 1e-6  # Prevent division by zero
    DEFAULT_THRESHOLD: Final[float] = 0.25
    SCALE_DECAY_FACTOR: Final[float] = 0.999  # Auto-scaling decay rate

    # Value formatting thresholds
    KILOUNIT_THRESHOLD: Final[int] = 1000  # Display as "K" when >= 1000


@dataclass(frozen=True)
class DebugConstants:
    """Debug logging and monitoring constants."""

    # Event logging thresholds
    FFT_DEBUG_MIN_BUFFER: Final[int] = 51
    FFT_DEBUG_MAX_BUFFER: Final[int] = 55
    TIME_DIFF_WARNING_MS: Final[float] = 100.0  # Warn if events > 100ms apart

    # Display refresh and timing
    THREAD_STOP_TIMEOUT_SEC: Final[float] = 1.5
    OSCILLATION_SPEED_FACTOR: Final[float] = 0.5  # For mock data timing


@dataclass(frozen=True)
class ChartCalculations:
    """Helper methods for consistent chart dimension calculations."""

    @staticmethod
    def main_chart_width(display_width: int) -> int:
        """Calculate width for main charts (FFT, magnitude)."""
        return max(DisplayConstants.MIN_CHART_WIDTH, display_width - DisplayConstants.CHART_MARGIN_CHARS)

    @staticmethod
    def main_chart_height(display_height: int) -> int:
        """Calculate height for main charts."""
        return max(DisplayConstants.MIN_CHART_HEIGHT, display_height // 4)

    @staticmethod
    def probability_chart_width(display_width: int) -> int:
        """Calculate width for individual probability charts (4 side-by-side)."""
        return max(
            DisplayConstants.MIN_PROB_CHART_WIDTH,
            (display_width // DisplayConstants.PROBABILITY_CHART_COUNT) - DisplayConstants.PROB_CHART_MARGIN,
        )

    @staticmethod
    def total_sparkline_levels(rows: int) -> int:
        """Calculate total levels for sparkline display."""
        return rows * SignalConstants.SPARKLINE_LEVELS_PER_ROW

    @staticmethod
    def should_skip_placeholder_data(buffer_length: int) -> bool:
        """Check if we should skip placeholder data."""
        return buffer_length > BufferConstants.PLACEHOLDER_SKIP_THRESHOLD

    @staticmethod
    def get_real_data_slice(data: list, buffer_length: int) -> list:
        """Get real data slice, skipping placeholder entries if needed."""
        if ChartCalculations.should_skip_placeholder_data(buffer_length):
            return data[BufferConstants.PLACEHOLDER_SKIP_THRESHOLD :]
        return data


# Export the main constant groups for easy importing
__all__ = ["DisplayConstants", "BufferConstants", "SignalConstants", "DebugConstants", "ChartCalculations"]
