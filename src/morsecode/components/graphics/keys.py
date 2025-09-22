"""Graphics component configuration keys."""

from enum import Enum


class GraphicsKey(Enum):
    """Graphics component configuration keys."""

    ENABLED = "enabled"
    BACKEND = "backend"
    WIDTH = "width"
    HEIGHT = "height"
    UPDATE_RATE_HZ = "update_rate_hz"
    BUFFER_SIZE = "buffer_size"
