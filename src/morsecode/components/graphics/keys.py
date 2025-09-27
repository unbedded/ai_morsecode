"""Graphics component configuration keys and sections."""

from enum import Enum


class GraphicsKey(Enum):
    """Graphics component configuration keys."""

    ENABLED = "enabled"
    BACKEND = "backend"
    DISPLAY_WIDTH_CHARS = "display_width_chars"
    DISPLAY_HEIGHT_CHARS = "display_height_chars"
    REFRESH_RATE_FPS = "refresh_rate_fps"
    BUFFER_SIZE_SEC = "buffer_size_sec"
    ENABLE_DEBUG_LOGGING = "enable_debug_logging"
    CHUNK_SIZE_MS = "chunk_size_ms"
    CONVOLUTION_INTERVAL_MS = "convolution_interval_ms"
    PLAYBACK_SPEED = "playback_speed"


class GraphicsSection(Enum):
    """Graphics component configuration sections."""

    GRAPHICS = "graphics"
