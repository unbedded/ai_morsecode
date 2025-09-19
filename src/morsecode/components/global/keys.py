"""Global application configuration keys."""

from enum import Enum


class CfgKey(Enum):
    """Global application configuration keys."""
    DEBUG = "debug"
    LOG_LEVEL = "log_level"
    OUTPUT_FILE = "output_file"
    PROFILE = "profile"
