"""Mock AwesomeConfigManager for morsecode-specific testing.

This module provides morsecode-specific mock configurations for testing
signal processing, audio HAL, and decoder components.
"""

from typing import Any


def create_signal_config_manager(
    frequency_hz: int = 600,
    threshold: float = 0.3,
    bandwidth_hz: int = 50,
    sample_rate_hz: int = 44100,
    mode: str = "AUTO",
):
    """Create a mock config manager with signal processor configuration."""
    from src.util.config.tests.mock_config_manager import MockAwesomeConfigManager

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
):
    """Create a mock config manager with audio HAL configuration."""
    from src.util.config.tests.mock_config_manager import MockAwesomeConfigManager

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
):
    """Create a mock config manager with morse decoder configuration."""
    from src.util.config.tests.mock_config_manager import MockAwesomeConfigManager

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