"""Graphics component for morse code pattern visualization."""

# Auto-initialize graphics event handling when module is imported
from . import auto_init  # noqa: F401
from .graphics_display import GraphicsDisplay
from .keys import GraphicsKey, GraphicsSection
from .pattern_display import PatternDisplay
from .schema import GraphicsSchema

__all__ = ["GraphicsDisplay", "PatternDisplay", "GraphicsKey", "GraphicsSchema", "GraphicsSection"]
