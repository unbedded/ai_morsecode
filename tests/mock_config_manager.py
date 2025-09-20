"""Mock AwesomeConfigManager for testing purposes.

This module provides a mock implementation of AwesomeConfigManager that can be used
in unit tests to avoid complex configuration setup while testing component behavior.
"""

from enum import Enum
from typing import Any


class MockConfigSection:
    """Mock configuration section that provides typed access methods."""

    def __init__(self, data: dict[str, Any]):
        self.data = data

    def get_int(self, key) -> int:
        """Get integer value from config."""
        key_str = key.value if isinstance(key, Enum) else str(key)
        value = self.data.get(key_str, 0)
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return 0
        return int(value)

    def get_double(self, key) -> float:
        """Get float value from config."""
        key_str = key.value if isinstance(key, Enum) else str(key)
        value = self.data.get(key_str, 0.0)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return 0.0
        return float(value)

    def get_string(self, key) -> str:
        """Get string value from config."""
        key_str = key.value if isinstance(key, Enum) else str(key)
        value = self.data.get(key_str, "")
        return str(value)

    def get_bool(self, key) -> bool:
        """Get boolean value from config."""
        key_str = key.value if isinstance(key, Enum) else str(key)
        value = self.data.get(key_str, False)
        return bool(value)

    def get_enum(self, key, enum_class):
        """Get enum value from config."""
        key_str = key.value if isinstance(key, Enum) else str(key)
        value = self.data.get(key_str)
        if isinstance(value, enum_class):
            return value
        # Try to convert string to enum
        if isinstance(value, str):
            try:
                return enum_class(value)
            except ValueError:
                return list(enum_class)[0]  # Return first enum value as default
        return list(enum_class)[0]  # Default to first enum value

    def get(self, key: str, default=None):
        """Get raw value from config."""
        return self.data.get(key, default)

    def apply_overrides(self, overrides: dict[str, Any]):
        """Apply configuration overrides to this section."""
        self.data.update(overrides)


class MockAwesomeConfigManager:
    """Mock implementation of AwesomeConfigManager for testing."""

    def __init__(self, configs: dict[str, dict[str, Any]] = None):
        """Initialize with optional predefined configurations."""
        self.configs = configs or {}
        self.schemas = {}

    def register_enum_config(self, section_name, schema):
        """Register an enum-based configuration schema."""
        section_key = section_name.value if isinstance(section_name, Enum) else str(section_name)
        self.schemas[section_key] = schema
        # Create default config if not provided
        if section_key not in self.configs:
            self.configs[section_key] = {}

    def register_logging_config(self, module_name: str, default_level: str = "INFO"):
        """Register logging configuration for a module."""
        # For testing, we just store this - real implementation would create schema
        logging_key = f"application.logging.{module_name}"
        if logging_key not in self.configs:
            self.configs[logging_key] = {"level": default_level}

    def get_section(self, section_name) -> MockConfigSection:
        """Get a config section."""
        section_key = section_name.value if isinstance(section_name, Enum) else str(section_name)
        config_data = self.configs.get(section_key, {})
        return MockConfigSection(config_data)


def create_signal_config_manager(
    frequency_hz: int = 600,
    threshold: float = 0.3,
    bandwidth_hz: int = 50,
    sample_rate_hz: int = 44100,
    mode: str = "AUTO",
) -> MockAwesomeConfigManager:
    """Create a mock config manager with signal processor configuration."""
    configs = {
        "signal": {
            # Core parameters
            "frequency_hz": frequency_hz,
            "signal_threshold_norm": threshold,
            "bandwidth_hz": bandwidth_hz,
            "sample_rate_hz": sample_rate_hz,
            "mode": mode,
            "adaptive_frequency": True,
            # Advanced signal processing parameters (from schema)
            "cutoff_hz": 15.0,
            "cw_mag_thresh_seconds": 0.1,
            "cw_peak_ratio_threshold": 4,
            "n_move_avg_elements": 6,
            "rolling_buffer_seconds": 3.0,
            "freq_range_min": 200,
            "freq_range_max": 1000,
            # FFT and noise parameters (newly added)
            "fft_window_size": 1024,
            "noise_floor_db": -40,
        },
        "global": {
            "debug": False,
            "timeout_ms": 30000,
        },
    }
    return MockAwesomeConfigManager(configs)


def create_audio_config_manager(
    sample_rate_hz: int = 44100,
    wav_filename: str = "test.wav",
    auto_gain_control: bool = False,
    chunk_size_ms: int = 50,
) -> MockAwesomeConfigManager:
    """Create a mock config manager with audio HAL configuration."""
    configs = {
        "audio": {
            "sample_rate": sample_rate_hz,
            "wav_filename": wav_filename,
            "auto_gain_control": auto_gain_control,
            "chunk_size_ms": chunk_size_ms,
        },
        "global": {
            "debug": False,
            "timeout_ms": 30000,
        },
    }
    return MockAwesomeConfigManager(configs)


def create_decoder_config_manager(
    wpm: int = 20, dot_duration_ms: float = 60.0, tolerance: float = 0.3
) -> MockAwesomeConfigManager:
    """Create a mock config manager with morse decoder configuration."""
    configs = {
        "decoder": {
            "wpm": wpm,
            "dot_duration_ms": dot_duration_ms,
            "timing_tolerance_norm": tolerance,
            "min_silence_ms": 200.0,
        },
        "global": {
            "debug": False,
            "timeout_ms": 30000,
        },
    }
    return MockAwesomeConfigManager(configs)
