"""Auto-initialization for graphics component via import.

This module sets up graphics event handling automatically when imported.
Uses publish-subscribe pattern for true loose coupling.
"""

import os
import sys

from ...events.bus import get_global_event_bus
from ...events.types import MorsePatternEvent


class SimpleGraphicsDisplay:
    """Simple graphics display that doesn't require configuration manager."""

    def __init__(self):
        """Initialize simple graphics display."""
        self.enabled = True  # Always enabled for CLI

    def display_pattern(self, event: "MorsePatternEvent") -> None:
        """Display morse pattern event information.

        Simple printf output showing confidence and pattern_type.

        Args:
            event: MorsePatternEvent to display
        """
        if not self.enabled:
            return

        # Simple printf output as requested - confidence and pattern_type
        # Note: Commented out to avoid console output when debug graphics is active
        # print(f"Pattern: {event.pattern_type} | Confidence: {event.confidence:.2f}")


class GraphicsAutoHandler:
    """Auto-initializing graphics handler using pub-sub pattern."""

    def __init__(self):
        """Initialize graphics handler with auto-detection of CLI vs testing."""
        # Better detection of actual test execution (not just module loading)
        is_testing = (
            "PYTEST_CURRENT_TEST" in os.environ  # pytest sets this
            or hasattr(sys, "_called_from_test")  # some test runners set this
            or "pytest" in sys.argv[0]
            if sys.argv
            else False  # running pytest directly
        )
        if is_testing:
            # Skip graphics initialization during testing
            self.graphics_display = None
            return

        # Initialize simple graphics for CLI usage (no complex config needed)
        try:
            # Create simple graphics display without complex config manager
            self.graphics_display = SimpleGraphicsDisplay()

            # Subscribe to events
            event_bus = get_global_event_bus()
            event_bus.subscribe(MorsePatternEvent, self.handle_morse_pattern)

        except Exception as e:
            # If graphics initialization fails, disable silently
            print(f"Graphics initialization failed: {e}")
            self.graphics_display = None

    def handle_morse_pattern(self, event: MorsePatternEvent) -> None:
        """Handle morse pattern events for graphics display."""
        if self.graphics_display:
            self.graphics_display.display_pattern(event)


# Auto-initialize when module is imported
_graphics_handler = GraphicsAutoHandler()
