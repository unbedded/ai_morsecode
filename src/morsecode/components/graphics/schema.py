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
        }
