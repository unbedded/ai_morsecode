#!/usr/bin/env python3
"""Demo of Enum-Based Config Pattern for SignalProcessor.

This example shows how to use enum-based config keys for:
- Auto-complete friendly config access
- Type-safe configuration
- Single import instead of multiple constants
"""

import logging
from enum import Enum

from morsecode.components.signal.signal_config_keys import SignalCfgKey, SignalCfgSection
from morsecode.components.signal.signal_config_schema import SignalConfigSchema, SignalMode

# Import the new config utilities


# Mock ConfigManager for demo
class MockConfigManager:
    """Mock config manager for demonstration."""

    def __init__(self):
        """Initialize mock config manager with sample data."""
        self.schemas = {}
        self.configs = {
            "signal": {
                "frequency": 700,  # Override default
                "threshold": 0.25,  # Override default
                "bandwidth": 75,  # Override default
                "sample_rate": 48000,  # Override default
                "mode": "ADAPTIVE",  # Override default
            }
        }

    def register_enum_config(self, section_name, schema):
        """Register an enum-based configuration schema."""
        self.schemas[section_name.value if isinstance(section_name, Enum) else section_name] = schema
        section_display = section_name.value if isinstance(section_name, Enum) else section_name
        print(f"✅ Registered enum config for '{section_display}'")

    def get_section(self, section_name):
        """Get a config section."""
        section_key = section_name.value if isinstance(section_name, Enum) else section_name
        return MockConfigSection(self.configs.get(section_key, {}))


class MockConfigSection:
    """Mock config section with enum-friendly access."""

    def __init__(self, data):
        """Initialize config section with data dictionary."""
        self.data = data

    def get_int(self, key):
        """Get integer value using enum key."""
        key_str = key.value if isinstance(key, Enum) else key
        return self.data.get(key_str, 0)

    def get_double(self, key):
        """Get double value using enum key."""
        key_str = key.value if isinstance(key, Enum) else key
        return self.data.get(key_str, 0.0)

    def get_enum(self, key, enum_class):
        """Get enum value using enum key."""
        key_str = key.value if isinstance(key, Enum) else key
        value_str = self.data.get(key_str, "")

        # Convert string to enum
        for enum_val in enum_class:
            if enum_val.value == value_str:
                return enum_val
        return enum_class(list(enum_class)[0])  # Default to first enum value


class SignalProcessor:
    """Demo SignalProcessor using enum-based config pattern."""

    def __init__(self, config_mgr):
        """Initialize with enum-based config registration and access."""
        self.logger = logging.getLogger(__name__)

        # STEP 1: Register schema (visible in constructor!)
        config_mgr.register_enum_config(SignalCfgSection.SIGNAL, SignalConfigSchema)

        # STEP 2: Get config section
        cfg = config_mgr.get_section(SignalCfgSection.SIGNAL)

        # STEP 3: Type-safe config access with auto-complete!
        # Type "SignalCfgKey." and IDE shows all options
        self.target_frequency_hz = cfg.get_int(SignalCfgKey.FREQUENCY)
        self.detection_threshold = cfg.get_double(SignalCfgKey.THRESHOLD)
        self.filter_bandwidth_hz = cfg.get_int(SignalCfgKey.BANDWIDTH)
        self.sample_rate_hz = cfg.get_int(SignalCfgKey.SAMPLE_RATE)
        self.mode = cfg.get_enum(SignalCfgKey.MODE, SignalMode)

        self.logger.info(
            "SignalProcessor initialized: freq=%dHz, threshold=%.2f, bandwidth=%dHz, mode=%s",
            self.target_frequency_hz,
            self.detection_threshold,
            self.filter_bandwidth_hz,
            self.mode.value,
        )

    def process_signal(self, data):
        """Process signal with configured parameters."""
        if self.mode == SignalMode.ADAPTIVE:
            return f"Adaptive processing at {self.target_frequency_hz}Hz with threshold {self.detection_threshold}"
        elif self.mode == SignalMode.MANUAL:
            return f"Manual processing at {self.target_frequency_hz}Hz"
        else:
            return f"Auto processing at {self.target_frequency_hz}Hz"


def demo_enum_config_pattern():
    """Demonstrate enum-based config pattern benefits."""
    print("=== Enum-Based Config Pattern Demo ===\\n")

    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # Create mock config manager
    config_mgr = MockConfigManager()

    # Create SignalProcessor - automatically registers and configures
    print("Creating SignalProcessor with enum-based config...")
    processor = SignalProcessor(config_mgr)

    # Test processing
    result = processor.process_signal([1, 2, 3])
    print(f"\\nProcessing result: {result}")

    print("\\n=== Benefits Demonstrated ===")
    print("✅ Single import: from .signal_config_keys import SignalCfgKey, SignalCfgSection")
    print("✅ Auto-complete: SignalCfgKey.FREQUENCY, SignalCfgKey.THRESHOLD, etc.")
    print("✅ Type safety: MyPy catches SignalCfgKey.FREQUNCY typos")
    print("✅ Enum comparison: if mode == SignalMode.ADAPTIVE")
    print("✅ Clean registration: config_mgr.register_enum_config(SignalCfgSection.SIGNAL, SignalConfigSchema)")


if __name__ == "__main__":
    demo_enum_config_pattern()
