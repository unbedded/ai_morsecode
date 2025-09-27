"""Audio component configuration keys - enum-based for auto-complete and type safety."""

from enum import Enum


class CfgKey(Enum):
    """Config keys for Audio component - auto-complete friendly!"""

    SAMPLE_RATE = "sample_rate"
    WAV_FILENAME = "wav_filename"
    AUTO_GAIN_CONTROL = "auto_gain_control"
    CHUNK_SIZE_MS = "chunk_size_ms"
    LOG_LEVEL = "log_level"


class CfgSection(Enum):
    """Section names for audio configuration."""

    AUDIO = "audio"
