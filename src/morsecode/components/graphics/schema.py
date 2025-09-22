"""Graphics component configuration schema."""

from typing import Any

from .keys import GraphicsKey


class GraphicsSchema:
    """Configuration schema for graphics component."""

    @staticmethod
    def get_schema() -> dict[str, Any]:
        """Get graphics component configuration schema.

        Returns:
            Dict containing the graphics configuration schema
        """
        return {
            GraphicsKey.ENABLED.value: True,  # Enabled by default for CLI
            GraphicsKey.BACKEND.value: "auto",  # auto, ascii, braille
            GraphicsKey.WIDTH.value: 80,  # Display width in characters
            GraphicsKey.HEIGHT.value: 6,  # Display height in rows
            GraphicsKey.UPDATE_RATE_HZ.value: 10.0,  # Real-time update rate
            GraphicsKey.BUFFER_SIZE.value: 1000,  # Signal buffer size
        }
