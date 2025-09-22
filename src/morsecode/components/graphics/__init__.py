"""Graphics component for morse code pattern visualization."""

# Auto-initialize graphics event handling when module is imported
from . import auto_init  # noqa: F401
from .debug_display import ASCIIDebugDisplay
from .graphics_display import GraphicsDisplay
from .keys import GraphicsKey
from .schema import GraphicsSchema
from .sections import GraphicsSection

__all__ = ["GraphicsDisplay", "ASCIIDebugDisplay", "GraphicsKey", "GraphicsSchema", "GraphicsSection"]
