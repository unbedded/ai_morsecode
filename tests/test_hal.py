"""Tests for the Hardware Abstraction Layer (HAL) module.

This test module provides comprehensive test coverage for the HAL functionality,
including audio file loading, chunk processing, and configuration management.
"""

import logging
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from scipy.io import wavfile

from morsecode.components.audio.hal import (
    DEFAULT_AUDIO_RATE_HZ,
    DEFAULT_WAV_FILENAME,
    HardwareAbstractionLayer,
)
from morsecode.components.audio.keys import CfgKey
from util.config.registry import AwesomeConfigManager


class TestHardwareAbstractionLayer:
    """Test cases for the HardwareAbstractionLayer class."""

    def create_mock_config_manager(self, config_overrides: dict = None) -> MagicMock:
        """Create a mock config manager with enum-based configuration.

        Args:
            config_overrides: Dict with CfgKey enum values to override defaults

        Returns:
            Mock config manager that provides enum-based configuration access
        """
        # Default audio configuration values
        default_config = {
            CfgKey.SAMPLE_RATE: 44100,
            CfgKey.WAV_FILENAME: None,
            CfgKey.AUTO_GAIN_CONTROL: True,
            CfgKey.CHUNK_SIZE: 50,
        }

        # Apply any overrides
        if config_overrides:
            config_values = {**default_config, **config_overrides}
        else:
            config_values = default_config

        # Create mock config manager
        mock_cfg_mgr = MagicMock(spec=AwesomeConfigManager)

        # Create mock config section
        mock_config_section = MagicMock()
        mock_config_section.get_int.side_effect = lambda key: config_values.get(key, 0)
        mock_config_section.get_double.side_effect = lambda key: config_values.get(key, 0.0)
        mock_config_section.get_bool.side_effect = lambda key: config_values.get(key, False)
        mock_config_section.get_string.side_effect = lambda key: config_values.get(key, "")

        # Mock the register_schema and get_section methods
        mock_cfg_mgr.register_schema.return_value = None
        mock_cfg_mgr.get_section.return_value = mock_config_section

        return mock_cfg_mgr

    def create_test_wav_file(
        self, temp_dir: Path, rate: int = 44100, duration_sec: float = 1.0, stereo: bool = False
    ) -> Path:
        """Create a temporary WAV file for testing.

        Args:
            temp_dir: Directory to create the test file in.
            rate: Sample rate in Hz.
            duration_sec: Duration in seconds.
            stereo: Whether to create stereo (True) or mono (False) audio.

        Returns:
            Path to the created test WAV file.
        """
        wav_path = temp_dir / "test_audio.wav"
        samples = int(rate * duration_sec)

        # Create simple sine wave test data
        t = np.linspace(0, duration_sec, samples)
        frequency = 440  # A4 note
        audio_data = (np.sin(2 * np.pi * frequency * t) * 32767).astype(np.int16)

        if stereo:
            # Create stereo by duplicating mono signal with slight phase shift
            left_channel = audio_data
            right_channel = (np.sin(2 * np.pi * frequency * t + np.pi / 4) * 32767).astype(np.int16)
            audio_data = np.column_stack((left_channel, right_channel))

        wavfile.write(wav_path, rate, audio_data)
        return wav_path

    def test_init_with_defaults(self, caplog: Any) -> None:
        """Test HAL initialization with default parameters."""
        with caplog.at_level(logging.INFO):
            # Mock the load_audio_file to avoid file dependency
            with patch.object(HardwareAbstractionLayer, "load_audio_file"):
                mock_cfg_mgr = self.create_mock_config_manager()
        hal = HardwareAbstractionLayer(mock_cfg_mgr)

        assert hal.audio_rate_hz == DEFAULT_AUDIO_RATE_HZ
        assert hal.wav_filename == DEFAULT_WAV_FILENAME

    def test_init_with_config(self, tmp_path: Path) -> None:
        """Test HAL initialization with custom configuration."""
        wav_file = self.create_test_wav_file(tmp_path, rate=48000)

        mock_cfg_mgr = self.create_mock_config_manager({
            CfgKey.WAV_FILENAME: str(wav_file),
            CfgKey.SAMPLE_RATE: 48000
        })
        hal = HardwareAbstractionLayer(mock_cfg_mgr)

        assert hal.audio_rate_hz == 48000
        assert hal.wav_filename == str(wav_file)
        assert len(hal.audio_data) > 0

    def test_load_audio_file_mono(self, tmp_path: Path) -> None:
        """Test loading a mono WAV file."""
        wav_file = self.create_test_wav_file(tmp_path, rate=22050, stereo=False)
        mock_cfg_mgr = self.create_mock_config_manager({CfgKey.WAV_FILENAME: str(wav_file)})
        hal = HardwareAbstractionLayer(mock_cfg_mgr)

        assert hal.audio_rate_hz == 22050
        assert hal.audio_data.ndim == 1  # Should be mono
        assert len(hal.audio_data) > 0

    def test_load_audio_file_stereo(self, tmp_path: Path) -> None:
        """Test loading a stereo WAV file (should extract first channel)."""
        wav_file = self.create_test_wav_file(tmp_path, rate=44100, stereo=True)
        mock_cfg_mgr = self.create_mock_config_manager({CfgKey.WAV_FILENAME: str(wav_file)})
        hal = HardwareAbstractionLayer(mock_cfg_mgr)

        assert hal.audio_rate_hz == 44100
        assert hal.audio_data.ndim == 1  # Should be mono after extraction
        assert len(hal.audio_data) > 0

    def test_load_audio_file_not_found(self) -> None:
        """Test loading a non-existent audio file."""
        mock_cfg_mgr = self.create_mock_config_manager({CfgKey.WAV_FILENAME: "/nonexistent/path/file.wav"})

        with pytest.raises(FileNotFoundError):
            HardwareAbstractionLayer(mock_cfg_mgr)

    def test_get_next_chunk_normal(self, tmp_path: Path) -> None:
        """Test getting normal audio chunks."""
        wav_file = self.create_test_wav_file(tmp_path, rate=44100, duration_sec=0.5)
        mock_cfg_mgr = self.create_mock_config_manager({CfgKey.WAV_FILENAME: str(wav_file)})
        hal = HardwareAbstractionLayer(mock_cfg_mgr)

        # Get 100ms chunk
        chunk = hal.get_next_chunk(100)
        expected_samples = int(0.1 * 44100)  # 100ms at 44100 Hz

        assert len(chunk) == expected_samples
        assert isinstance(chunk, np.ndarray)

    def test_get_next_chunk_invalid_interval(self, tmp_path: Path) -> None:
        """Test getting chunk with invalid interval."""
        wav_file = self.create_test_wav_file(tmp_path)
        mock_cfg_mgr = self.create_mock_config_manager({CfgKey.WAV_FILENAME: str(wav_file)})
        hal = HardwareAbstractionLayer(mock_cfg_mgr)

        with pytest.raises(ValueError, match="update_interval_ms must be positive"):
            hal.get_next_chunk(-100)

        with pytest.raises(ValueError, match="update_interval_ms must be positive"):
            hal.get_next_chunk(0)

    def test_get_next_chunk_no_data(self, tmp_path: Path) -> None:
        """Test getting chunk when no audio data is available."""
        wav_file = self.create_test_wav_file(tmp_path)
        mock_cfg_mgr = self.create_mock_config_manager({CfgKey.WAV_FILENAME: str(wav_file)})
        hal = HardwareAbstractionLayer(mock_cfg_mgr)

        # Exhaust all data
        hal.audio_data = np.array([])

        chunk = hal.get_next_chunk(100)
        expected_samples = int(0.1 * hal.audio_rate_hz)

        assert len(chunk) == expected_samples
        assert np.all(chunk == 0)  # Should be all zeros

    def test_get_next_chunk_partial_data(self, tmp_path: Path) -> None:
        """Test getting chunk when remaining data is less than requested."""
        wav_file = self.create_test_wav_file(tmp_path, duration_sec=0.05)  # 50ms of data
        mock_cfg_mgr = self.create_mock_config_manager({CfgKey.WAV_FILENAME: str(wav_file)})
        hal = HardwareAbstractionLayer(mock_cfg_mgr)

        # Request 100ms chunk (more than available)
        chunk = hal.get_next_chunk(100)
        expected_samples = int(0.1 * hal.audio_rate_hz)

        assert len(chunk) == expected_samples
        # Should be padded with zeros

    def test_get_audio_rate_hz(self, tmp_path: Path) -> None:
        """Test getting audio sample rate."""
        wav_file = self.create_test_wav_file(tmp_path, rate=48000)
        mock_cfg_mgr = self.create_mock_config_manager({CfgKey.WAV_FILENAME: str(wav_file)})
        hal = HardwareAbstractionLayer(mock_cfg_mgr)

        assert hal.get_audio_rate_hz() == 48000

    def test_get_params(self, tmp_path: Path) -> None:
        """Test getting configuration parameters."""
        wav_file = self.create_test_wav_file(tmp_path, rate=22050)
        mock_cfg_mgr = self.create_mock_config_manager({
            CfgKey.WAV_FILENAME: str(wav_file),
            CfgKey.SAMPLE_RATE: 22050
        })
        hal = HardwareAbstractionLayer(mock_cfg_mgr)

        params = hal.get_params()

        assert params["wav_filename"] == str(wav_file)
        assert params["audio_rate_hz"] == 22050

    def test_get_cfg(self, tmp_path: Path) -> None:
        """Test getting configuration dictionary."""
        wav_file = self.create_test_wav_file(tmp_path)
        mock_cfg_mgr = self.create_mock_config_manager({CfgKey.WAV_FILENAME: str(wav_file)})
        hal = HardwareAbstractionLayer(mock_cfg_mgr)

        config = hal.get_cfg()

        assert "wav_filename" in config
        assert "audio_rate_hz" in config
        assert config == hal.get_params()

    def test_has_data(self, tmp_path: Path) -> None:
        """Test checking if audio data is available."""
        wav_file = self.create_test_wav_file(tmp_path)
        mock_cfg_mgr = self.create_mock_config_manager({CfgKey.WAV_FILENAME: str(wav_file)})
        hal = HardwareAbstractionLayer(mock_cfg_mgr)

        # Should have data initially
        assert hal.has_data() is True

        # Exhaust all data
        hal.audio_data = np.array([])
        assert hal.has_data() is False

    def test_multiple_chunks(self, tmp_path: Path) -> None:
        """Test retrieving multiple consecutive chunks."""
        wav_file = self.create_test_wav_file(tmp_path, duration_sec=1.0)
        mock_cfg_mgr = self.create_mock_config_manager({CfgKey.WAV_FILENAME: str(wav_file)})
        hal = HardwareAbstractionLayer(mock_cfg_mgr)

        initial_length = len(hal.audio_data)
        chunk_size_ms = 100
        expected_samples = int(0.1 * hal.audio_rate_hz)

        # Get first chunk
        chunk1 = hal.get_next_chunk(chunk_size_ms)
        assert len(chunk1) == expected_samples
        assert len(hal.audio_data) == initial_length - expected_samples

        # Get second chunk
        chunk2 = hal.get_next_chunk(chunk_size_ms)
        assert len(chunk2) == expected_samples
        assert len(hal.audio_data) == initial_length - (2 * expected_samples)

        # Chunks should be different (different parts of the audio)
        assert not np.array_equal(chunk1, chunk2)

    @pytest.mark.parametrize(
        "rate,duration",
        [
            (8000, 0.1),  # Low rate, short duration
            (44100, 2.0),  # Standard rate, longer duration
            (96000, 0.5),  # High rate, medium duration
        ],
    )
    def test_different_audio_formats(self, tmp_path: Path, rate: int, duration: float) -> None:
        """Test HAL with different audio formats and parameters."""
        wav_file = self.create_test_wav_file(tmp_path, rate=rate, duration_sec=duration)
        mock_cfg_mgr = self.create_mock_config_manager({CfgKey.WAV_FILENAME: str(wav_file)})
        hal = HardwareAbstractionLayer(mock_cfg_mgr)

        assert hal.get_audio_rate_hz() == rate

        # Test chunk retrieval
        chunk = hal.get_next_chunk(50)  # 50ms chunk
        expected_samples = int(0.05 * rate)
        assert len(chunk) == expected_samples

    def test_logging_configuration(self, caplog: Any) -> None:
        """Test that logging is properly configured."""
        with caplog.at_level(logging.INFO):
            with patch.object(HardwareAbstractionLayer, "load_audio_file"):
                mock_cfg_mgr = self.create_mock_config_manager()
        hal = HardwareAbstractionLayer(mock_cfg_mgr)  # Use default config

        # Verify HAL was created successfully (basic logging validation)
        assert hal is not None
        assert isinstance(hal.logger, logging.Logger)

    @patch("morsecode.components.audio.hal.wavfile.read")
    def test_load_audio_file_error_handling(self, mock_read: Any, tmp_path: Path) -> None:
        """Test error handling during audio file loading."""
        wav_file = tmp_path / "test.wav"
        wav_file.touch()  # Create empty file

        # Mock wavfile.read to raise an exception
        mock_read.side_effect = Exception("Corrupted file")

        mock_cfg_mgr = self.create_mock_config_manager({CfgKey.WAV_FILENAME: str(wav_file)})

        with pytest.raises(RuntimeError, match="Failed to load audio file"):
            HardwareAbstractionLayer(mock_cfg_mgr)
