"""Simple graphics display component for morse code patterns."""

from typing import TYPE_CHECKING

from util.config import AwesomeConfigManager, ConfigurableBase

from .keys import GraphicsKey
from .schema import GraphicsSchema
from .sections import GraphicsSection

if TYPE_CHECKING:
    from morsecode.events.types import MorsePatternEvent


class GraphicsDisplay(ConfigurableBase):
    """Simple graphics display for morse code patterns.

    Prints confidence and pattern_type for each event with simple printf output.
    Designed to be enabled by default for CLI usage but disabled during unit testing.

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

        self.logger.info("GraphicsDisplay initialized: enabled=%s", self.enabled)

    def _load_config_values(self) -> None:
        """Load configuration values using type-safe enum access.

        This method is called by ConfigurableBase during initialization and reconfiguration.
        Only method we need to implement - all boilerplate handled by base class.
        """
        # STEP 1: Load core configuration with type safety
        self.enabled = self._cfg_section.get_bool(GraphicsKey.ENABLED)

        # STEP 2: Global config for cross-cutting concerns (recommended pattern)
        global_cfg = self._cfg_mgr.get_section("global")
        self.debug = global_cfg.get_bool("debug") if global_cfg.get("debug") else False  # type: ignore[attr-defined]
        self.timeout_ms = global_cfg.get_int("timeout_ms") if global_cfg.get("timeout_ms") else 30000  # type: ignore[attr-defined]

        # STEP 3: Log completion with lazy % formatting (CRITICAL!)
        self.logger.info("GraphicsDisplay configured: enabled=%s", self.enabled)

        # STEP 4: Debug logging controlled by config (not code!)
        self.logger.debug("Internal state: ready for pattern display")

    def _on_reconfiguration(self) -> None:
        """Handle reconfiguration side effects.

        Called by ConfigurableBase after configuration values are reloaded.
        No special reconfiguration needed for this simple component.
        """
        self.logger.info("GraphicsDisplay reconfigured: enabled=%s", self.enabled)

    def display_pattern(self, event: "MorsePatternEvent") -> None:
        """Display morse pattern event information.

        Simple printf output showing confidence and pattern_type.

        Args:
            event: MorsePatternEvent to display
        """
        if not self.enabled:
            return

        # Simple printf output as requested - confidence and pattern_type
        print(f"Pattern: {event.pattern_type} | Confidence: {event.confidence:.2f}")

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable graphics display.

        Args:
            enabled: True to enable display, False to disable
        """
        # Use reconfigure method for runtime changes
        self.reconfigure({"enabled": enabled})
        self.logger.debug("Graphics display enabled=%s", enabled)
