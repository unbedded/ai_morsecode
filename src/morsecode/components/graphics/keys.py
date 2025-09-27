"""Graphics component configuration keys and sections."""

from enum import Enum


class GraphicsKey(Enum):
    """Graphics component configuration keys."""

    MODE = "mode"
    DISPLAY_WIDTH_CHARS = "display_width_chars"
    DISPLAY_HEIGHT_CHARS = "display_height_chars"
    REFRESH_RATE_FPS = "refresh_rate_fps"
    BUFFER_SIZE_SEC = "buffer_size_sec"
    LOG_LEVEL = "log_level"


class GraphicsSection(Enum):
    """Graphics component configuration sections."""

    GRAPHICS = "graphics"
