"""Integration tests using synthetic WAV files with ConfigurableBase architecture.

This module tests the complete pipeline using generated synthetic WAV files
to ensure the ConfigurableBase architecture works end-to-end.
"""

import json
from pathlib import Path

import pytest

from morsecode import decoder_app
from util.config import AwesomeConfigManager


class TestSyntheticWavIntegration:
    """Test complete pipeline using generated synthetic WAV files."""

    @classmethod
    def setup_class(cls):
        """Set up test class by checking for synthetic test data."""
        cls.test_data_dir = Path("tests/data/generated_data")
        cls.metadata_file = cls.test_data_dir / "test_suite_metadata.json"

        # Load test metadata if available
        if cls.metadata_file.exists():
            with open(cls.metadata_file) as f:
                cls.test_metadata = json.load(f)
        else:
            cls.test_metadata = {}

    def test_single_word_decoding_configurable(self):
        """Test decoding a single word using ConfigurableBase architecture."""
        # Use HELLO test file
        test_file = self.test_data_dir / "basic" / "Word_HELLO_15WPM.wav"

        if not test_file.exists():
            pytest.skip(f"Test file not found: {test_file}")

        # Create config manager and overrides
        config_manager = AwesomeConfigManager()
        overrides = {"audio": {"wav_filename": str(test_file)}, "decoder": {"wpm": 15}}

        # Run decoder with ConfigurableBase architecture
        result = decoder_app.run_decoder_configurable(config_manager=config_manager, overrides=overrides)

        # Should complete successfully
        assert result == 0

    def test_pattern_decoding_configurable(self):
        """Test decoding dot/dash patterns using ConfigurableBase architecture."""
        # Use EEEEE test file (5 dots)
        test_file = self.test_data_dir / "basic" / "Pattern_EEEEE_15WPM.wav"

        if not test_file.exists():
            pytest.skip(f"Test file not found: {test_file}")

        # Create config manager and overrides
        config_manager = AwesomeConfigManager()
        overrides = {"audio": {"wav_filename": str(test_file)}, "decoder": {"wpm": 15}}

        # Run decoder
        result = decoder_app.run_decoder_configurable(config_manager=config_manager, overrides=overrides)

        # Should complete successfully
        assert result == 0

    def test_nonexistent_file_error(self):
        """Test error handling with nonexistent WAV file."""
        config_manager = AwesomeConfigManager()
        overrides = {"audio": {"wav_filename": "/nonexistent/file.wav"}}

        # Should return error code
        result = decoder_app.run_decoder_configurable(config_manager=config_manager, overrides=overrides)

        assert result == 1

    def test_frequency_override_configurable(self):
        """Test frequency override functionality."""
        # Use any available test file
        test_file = self.test_data_dir / "basic" / "Word_HELLO_15WPM.wav"

        if not test_file.exists():
            pytest.skip(f"Test file not found: {test_file}")

        # Create config manager with signal overrides
        config_manager = AwesomeConfigManager()
        overrides = {
            "audio": {"wav_filename": str(test_file)},
            "signal": {"frequency_hz": 600},  # Override frequency
            "decoder": {"wpm": 15},
        }

        # Run decoder
        result = decoder_app.run_decoder_configurable(config_manager=config_manager, overrides=overrides)

        # Should complete successfully
        assert result == 0
