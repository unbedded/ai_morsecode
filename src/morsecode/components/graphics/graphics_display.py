"""Advanced graphics display component for morse code patterns using UILT."""

from collections import deque
from typing import TYPE_CHECKING

from util.config import AwesomeConfigManager, ConfigurableBase
from util.graph import ASCIIBackend, BrailleBackend, plot_signal_auto

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

        # Initialize UILT backend and signal buffer
        self._backend: ASCIIBackend | BrailleBackend | None = None
        self._signal_buffer: deque[float] = deque(maxlen=self.buffer_size)
        self._confidence_buffer: deque[float] = deque(maxlen=self.buffer_size)
        self._timing_buffer: deque[float] = deque(maxlen=self.buffer_size)
        self._last_update_time = 0.0

        self._initialize_backend()
        self.logger.info("GraphicsDisplay initialized: enabled=%s, backend=%s", self.enabled, self.backend_type)

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
        Reinitialize backend if configuration changed.
        """
        # Resize buffers if buffer_size changed
        if hasattr(self, "_signal_buffer"):
            self._signal_buffer = deque(list(self._signal_buffer), maxlen=self.buffer_size)
            self._confidence_buffer = deque(list(self._confidence_buffer), maxlen=self.buffer_size)
            self._timing_buffer = deque(list(self._timing_buffer), maxlen=self.buffer_size)

        # Reinitialize backend with new settings
        self._initialize_backend()
        self.logger.info("GraphicsDisplay reconfigured: enabled=%s, backend=%s", self.enabled, self.backend_type)

    def _initialize_backend(self) -> None:
        """Initialize UILT backend based on configuration."""
        if not self.enabled:
            self._backend = None
            return

        if self.backend_type == "ascii":
            self._backend = ASCIIBackend(self.width, self.height, "Morse Signal")
        elif self.backend_type == "braille":
            self._backend = BrailleBackend(self.width, self.height, "Morse Signal")
        else:  # auto
            # Use plot_signal_auto for automatic backend selection
            self._backend = None  # Will use convenience function instead

        self.logger.debug("Initialized backend: %s", self.backend_type)

    def add_signal_data(self, signal_value: float, confidence: float = 1.0, timing: float = 0.0) -> None:
        """Add signal data point to visualization buffer.

        Args:
            signal_value: Raw signal amplitude (-1.0 to 1.0)
            confidence: Pattern recognition confidence (0.0 to 1.0)
            timing: Timing information in seconds
        """
        if not self.enabled:
            return

        self._signal_buffer.append(signal_value)
        self._confidence_buffer.append(confidence)
        self._timing_buffer.append(timing)

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
        if not self.enabled or not self._signal_buffer:
            return

        signal_data = list(self._signal_buffer)

        try:
            if self._backend:
                # Use direct backend
                self._backend.clear()
                self._backend.plot(signal_data, sample_rate_hz=self.update_rate_hz)

                if hasattr(self._backend, "render_braille"):
                    lines = self._backend.render_braille()
                else:
                    lines = self._backend.render_sparkline()
            else:
                # Use auto backend selection
                lines, backend_used = plot_signal_auto(
                    signal_data,
                    sample_rate_hz=self.update_rate_hz,
                    title="Morse Signal",
                    width=self.width,
                    height=self.height,
                    prefer_braille=True,
                )

            # Clear screen and display (simple approach)
            print("\033[2J\033[H", end="")  # Clear screen and move cursor to top
            for line in lines:
                print(line)

            # Display stats
            if self._confidence_buffer:
                avg_confidence = sum(self._confidence_buffer) / len(self._confidence_buffer)
                print(f"\nBuffer: {len(signal_data)} samples | Avg Confidence: {avg_confidence:.2f}")

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
        self._signal_buffer.clear()
        self._confidence_buffer.clear()
        self._timing_buffer.clear()
        self.logger.debug("Signal buffers cleared")
