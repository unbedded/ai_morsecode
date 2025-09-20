"""Simple graphics display component for morse code patterns."""

from typing import TYPE_CHECKING

from util.config import AwesomeConfigManager
from util.logging import ComponentLogger

from .keys import GraphicsKey
from .schema import GraphicsSchema
from .sections import GraphicsSection

if TYPE_CHECKING:
    from morsecode.events.types import MorsePatternEvent


class GraphicsDisplay:
    """Simple graphics display for morse code patterns.

    Prints confidence and pattern_type for each event with simple printf output.
    Designed to be enabled by default for CLI usage but disabled during unit testing.
    """

    def __init__(self, cfg_mgr: AwesomeConfigManager):
        """Initialize graphics display component.

        Args:
            cfg_mgr: Configuration manager instance
        """
        # STEP 1: Initialize logger FIRST (required by CLAUDE.md)
        self.logger = ComponentLogger(__name__, cfg_mgr)
        self.logger.info("GraphicsDisplay initializing...")

        # STEP 2: Register component configuration schema
        cfg_mgr.register_enum_config(GraphicsSection.GRAPHICS.value, GraphicsSchema)
        cfg = cfg_mgr.get_section(GraphicsSection.GRAPHICS.value)

        # STEP 3: Register logging config for this component
        cfg_mgr.register_logging_config(__name__, default_level="INFO")

        # STEP 4: Access configuration with type safety
        self.enabled = cfg.get(GraphicsKey.ENABLED.value, True)

        # STEP 5: Log completion with lazy % formatting
        self.logger.info("GraphicsDisplay initialized: enabled=%s", self.enabled)

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
        self.enabled = enabled
        self.logger.debug("Graphics display enabled=%s", enabled)
