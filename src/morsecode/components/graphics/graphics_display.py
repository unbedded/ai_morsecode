"""Advanced graphics display component for morse code patterns using UILT."""

from typing import TYPE_CHECKING

from util.config import AwesomeConfigManager, ConfigurableBase
from util.graph.time_series_graph import TimeSeriesGraph

from .keys import GraphicsKey
from .schema import GraphicsSchema
from .sections import GraphicsSection

if TYPE_CHECKING:
    from morsecode.events.types import MorsePatternEvent


class GraphicsDisplay(ConfigurableBase):
    """Advanced graphics display for morse code patterns using UILT.

    Provides real-time signal visualization with automatic backend selection (ASCII/Braille).
    Displays morse code timing patterns, confidence levels, and signal quality.
    Designed for SSH-friendly real-time debugging and analysis.

    Uses ConfigurableBase inheritance pattern for type-safe configuration access
    and runtime reconfiguration support.
    """

    # ConfigurableBase requirements
    CONFIG_SCHEMA = GraphicsSchema
    CONFIG_SECTION = GraphicsSection.GRAPHICS.value
    CONFIG_KEYS = GraphicsKey

    def __init__(self, cfg_mgr: AwesomeConfigManager, overrides=None):
        """Initialize graphics display component with ConfigurableBase pattern.

        Args:
            cfg_mgr: Configuration manager instance
            overrides: Optional configuration overrides for testing/tuning.
        """
        # Call ConfigurableBase constructor (handles all config/logging boilerplate)
        super().__init__(cfg_mgr, overrides)

        # FIXED: Use TimeSeriesGraph instead of manual buffer management
        self._time_series_graph: TimeSeriesGraph | None = None
        self._last_update_time = 0.0

        self._initialize_time_series_graph()
        self.logger.info(
            "GraphicsDisplay initialized: enabled=%s, backend=%s, using TimeSeriesGraph API",
            self.enabled,
            self.backend_type,
        )

    def _load_config_values(self) -> None:
        """Load configuration values using type-safe enum access.

        This method is called by ConfigurableBase during initialization and reconfiguration.
        Only method we need to implement - all boilerplate handled by base class.
        """
        # STEP 1: Load core configuration with type safety
        self.enabled = self._cfg_section.get_bool(GraphicsKey.ENABLED)
        self.backend_type = self._cfg_section.get_string(GraphicsKey.BACKEND)
        self.width = self._cfg_section.get_int(GraphicsKey.WIDTH)
        self.height = self._cfg_section.get_int(GraphicsKey.HEIGHT)
        self.update_rate_hz = self._cfg_section.get_double(GraphicsKey.UPDATE_RATE_HZ)
        self.buffer_size = self._cfg_section.get_int(GraphicsKey.BUFFER_SIZE)

        # STEP 2: Global config for cross-cutting concerns (recommended pattern)
        try:
            global_cfg = self._cfg_mgr.get_section("global")
            self.debug = global_cfg.get_bool("debug") if global_cfg else False
            self.timeout_ms = global_cfg.get_int("timeout_ms") if global_cfg else 30000
        except KeyError:
            # Global section not configured - use defaults
            self.debug = False
            self.timeout_ms = 30000

        # STEP 3: Log completion with lazy % formatting (CRITICAL!)
        self.logger.info(
            "GraphicsDisplay configured: enabled=%s, backend=%s, size=%dx%d",
            self.enabled,
            self.backend_type,
            self.width,
            self.height,
        )

        # STEP 4: Debug logging controlled by config (not code!)
        self.logger.debug("Internal state: ready for pattern display")

    def _on_reconfiguration(self) -> None:
        """Handle reconfiguration side effects.

        Called by ConfigurableBase after configuration values are reloaded.
        Reinitialize TimeSeriesGraph if configuration changed.
        """
        # Reinitialize TimeSeriesGraph with new settings
        self._initialize_time_series_graph()
        self.logger.info("GraphicsDisplay reconfigured: enabled=%s, backend=%s", self.enabled, self.backend_type)

    def _initialize_time_series_graph(self) -> None:
        """Initialize TimeSeriesGraph based on configuration."""
        if not self.enabled:
            self._time_series_graph = None
            return

        # Calculate time window from buffer size and update rate
        time_window_sec = max(5.0, self.buffer_size / self.update_rate_hz)

        # Calculate expected sample rate from update rate
        sample_rate_hz = self.update_rate_hz

        # Create TimeSeriesGraph with proper configuration
        self._time_series_graph = TimeSeriesGraph(
            width=self.width,
            height=self.height,
            time_window_sec=time_window_sec,
            backend=self.backend_type,
            title="Morse Signal",
            sample_rate_hz=sample_rate_hz,
            auto_scale=True,  # Allow auto-scaling for signal amplitude
        )

        self.logger.debug(
            "Initialized TimeSeriesGraph: backend=%s, window=%.1fs, rate=%.1fHz",
            self.backend_type,
            time_window_sec,
            sample_rate_hz,
        )

    def add_signal_data(self, signal_value: float, confidence: float = 1.0, timing: float = 0.0) -> None:
        """Add signal data point to visualization buffer.

        Args:
            signal_value: Raw signal amplitude (-1.0 to 1.0)
            confidence: Pattern recognition confidence (0.0 to 1.0)
            timing: Timing information in seconds (optional)
        """
        if not self.enabled or not self._time_series_graph:
            return

        # FIXED: Use TimeSeriesGraph API - no manual buffer management needed
        if timing > 0.0:
            # Use explicit timestamp if provided
            self._time_series_graph.add_data_point(signal_value, timing)
        else:
            # Use sample-driven approach (automatic timing)
            self._time_series_graph.add_data_point(signal_value)

        # Store confidence for display stats (not used in graph)
        # Note: Could extend TimeSeriesGraph to support metadata in the future

        # Update display at configured rate
        import time

        current_time = time.time()
        if current_time - self._last_update_time >= (1.0 / self.update_rate_hz):
            self._update_display()
            self._last_update_time = current_time

    def display_pattern(self, event: "MorsePatternEvent") -> None:
        """Display morse pattern event information.

        Extracts signal data from event and adds to visualization buffer.

        Args:
            event: MorsePatternEvent to display
        """
        if not self.enabled:
            return

        # Extract relevant data from event
        # For now, use confidence as signal strength and duration for timing
        signal_strength = event.confidence  # Treat confidence as signal amplitude
        timing_info = event.duration_ms / 1000.0  # Convert to seconds

        self.add_signal_data(signal_strength, event.confidence, timing_info)

        # Also log pattern info for debugging
        self.logger.debug("Pattern: %s | Confidence: %.2f", event.pattern_type, event.confidence)

    def _update_display(self) -> None:
        """Update the visual display with current buffer data."""
        if not self.enabled or not self._time_series_graph:
            return

        try:
            # FIXED: Use TimeSeriesGraph render() API - handles all backend logic
            lines = self._time_series_graph.render()

            if not lines:
                return  # No data to display yet

            # Clear screen and display (simple approach)
            print("\033[2J\033[H", end="")  # Clear screen and move cursor to top
            for line in lines:
                print(line)

            # Display stats from TimeSeriesGraph
            stats = self._time_series_graph.get_stats()
            rate_hz = stats["calculated_sample_rate_hz"]
            backend = stats["backend"]
            print(f"\nBuffer: {stats['sample_count']} samples | Rate: {rate_hz:.1f}Hz | Backend: {backend}")

        except Exception as e:
            self.logger.error("Display update failed: %s", e)

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable graphics display.

        Args:
            enabled: True to enable display, False to disable
        """
        # Use reconfigure method for runtime changes
        self.reconfigure({"enabled": enabled})
        self.logger.debug("Graphics display enabled=%s", enabled)

    def clear_buffers(self) -> None:
        """Clear all signal buffers."""
        if self._time_series_graph:
            # FIXED: Use TimeSeriesGraph API to clear buffers
            # Note: TimeSeriesGraph doesn't expose clear() method, but we can recreate it
            self._initialize_time_series_graph()
            self.logger.debug("TimeSeriesGraph buffers cleared via recreation")
        else:
            self.logger.debug("No TimeSeriesGraph to clear")
