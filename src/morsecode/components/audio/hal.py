"""Hardware Abstraction Layer (HAL) for reading chunks of audio data.

This module provides functionality to read and process audio data from a WAV file.
It supports configuration management and logging for debugging and error handling.

Example usage:
    ```python
    from morsecode.components.audio.hal import HardwareAbstractionLayer
    from util.config.models import AudioConfig

    config = AudioConfig(
        wav_filename='/path/to/audio.wav',
        sample_rate=48000
    )

    hal = HardwareAbstractionLayer(config=config)
    audio_chunk = hal.get_next_chunk(update_interval_ms=100)
    ```
"""

import logging
from pathlib import Path
from typing import Any

import numpy as np
from scipy.io import wavfile

from morsecode.components.audio.keys import CfgKey, CfgSection
from morsecode.components.audio.schema import ConfigSchema
from morsecode.events.bus import get_global_event_bus
from morsecode.events.types import AudioChunkEvent

# Constants
DEFAULT_WAV_FILENAME = None
DEFAULT_AUDIO_RATE_HZ = 44100


class HardwareAbstractionLayer:
    """A class to handle audio data processing from a WAV file.

    This class provides methods to load audio files and retrieve chunks of audio data
    for real-time processing. It maintains internal state for continuous chunk reading.

    Attributes:
        audio_data: The audio data loaded from the WAV file.
        audio_rate_hz: The sampling rate of the audio data in Hz.
        wav_filename: Path to the WAV file being processed.
    """

    def __init__(self, cfg_mgr) -> None:
        """Initialize the HardwareAbstractionLayer with enum-based configuration.

        Args:
            cfg_mgr: Config manager for enum-based configuration.
        """
        # Initialize logging as the first step in constructor
        self.logger = logging.getLogger(__name__)

        # STEP 1: Register schema (visible in constructor!)
        cfg_mgr.register_schema(CfgSection.AUDIO, ConfigSchema)

        # STEP 2: Get config section
        cfg = cfg_mgr.get_section(CfgSection.AUDIO)

        # STEP 3: Type-safe config access with auto-complete!
        self.audio_rate_hz: int = cfg.get_int(CfgKey.SAMPLE_RATE)
        self.wav_filename: str | None = cfg.get_string(CfgKey.WAV_FILENAME)
        self.auto_gain_control: bool = cfg.get_bool(CfgKey.AUTO_GAIN_CONTROL)
        self.chunk_size_ms: int = cfg.get_int(CfgKey.CHUNK_SIZE)

        self.logger.info(
            "Audio HAL initialized: sample_rate=%dHz, file=%s, agc=%s, chunk=%dms",
            self.audio_rate_hz,
            self.wav_filename,
            self.auto_gain_control,
            self.chunk_size_ms,
        )

        # Initialize audio processing state
        self.audio_data: np.ndarray = np.array([])
        self._chunk_counter: int = 0

        # Get global event bus for publishing events
        self._event_bus = get_global_event_bus()

        self.load_audio_file()

    def get_params(self) -> dict[str, Any]:
        """Return the current configuration parameters.

        Returns:
            Dictionary containing current configuration parameters.
        """
        return {"wav_filename": self.wav_filename, "audio_rate_hz": self.audio_rate_hz}

    def load_audio_file(self) -> None:
        """Read a WAV format file and extract audio data.

        Raises:
            FileNotFoundError: If the specified WAV file doesn't exist.
            ValueError: If the audio file format is unsupported.
            RuntimeError: If there's an error reading the audio file.
        """
        try:
            # Handle synthetic audio generation for testing
            if self.wav_filename is None:
                self._generate_synthetic_audio()
                return

            wav_path = Path(self.wav_filename)
            if not wav_path.exists():
                raise FileNotFoundError(f"Audio file '{self.wav_filename}' not found")

            self.audio_rate_hz, data = wavfile.read(self.wav_filename)

            # Handle stereo files by extracting first channel
            if data.ndim > 1:
                self.audio_data = data[:, 0]
            else:
                self.audio_data = data

            self.logger.info(
                "Audio file '%s' loaded successfully with rate %d Hz",
                self.wav_filename,
                self.audio_rate_hz,
            )

        except FileNotFoundError:
            self.logger.exception("Audio file '%s' not found", self.wav_filename)
            raise
        except Exception as e:
            self.logger.exception("Error loading audio file: %s", str(e))
            raise RuntimeError(f"Failed to load audio file: {e}") from e

    def get_next_chunk(self, update_interval_ms: int) -> np.ndarray:
        """Retrieve the next chunk of audio data.

        Args:
            update_interval_ms: Duration of the chunk in milliseconds.

        Returns:
            Array containing the next audio chunk. Returns zeros if no data available.

        Raises:
            ValueError: If update_interval_ms is invalid.
        """
        try:
            if update_interval_ms <= 0:
                raise ValueError("update_interval_ms must be positive")

            # Increment chunk counter
            self._chunk_counter += 1

            samples_per_chunk = int((update_interval_ms / 1000) * self.audio_rate_hz)

            if len(self.audio_data) == 0:
                self.logger.warning("No audio data available. Returning zeros")
                chunk = np.zeros(samples_per_chunk)
                has_more_data = False

                # Publish audio chunk event for empty data
                audio_event = AudioChunkEvent(
                    chunk_data=chunk,
                    chunk_size_ms=update_interval_ms,
                    sample_rate=self.audio_rate_hz,
                    chunk_number=self._chunk_counter,
                    has_more_data=has_more_data,
                )
                self._event_bus.publish(audio_event)

                return chunk

            # Extract chunk and update remaining data
            chunk = self.audio_data[:samples_per_chunk]
            self.audio_data = self.audio_data[samples_per_chunk:]

            # Pad with zeros if chunk is shorter than requested
            if len(chunk) < samples_per_chunk:
                padded_chunk = np.zeros(samples_per_chunk)
                padded_chunk[: len(chunk)] = chunk
                chunk = padded_chunk

            # Check if more data is available after processing this chunk
            has_more_data = len(self.audio_data) > 0

            # Publish audio chunk event
            audio_event = AudioChunkEvent(
                chunk_data=chunk,
                chunk_size_ms=update_interval_ms,
                sample_rate=self.audio_rate_hz,
                chunk_number=self._chunk_counter,
                has_more_data=has_more_data,
            )
            self._event_bus.publish(audio_event)

            return chunk

        except Exception as e:
            self.logger.exception("Error retrieving audio chunk: %s", str(e))
            raise

    def get_audio_rate_hz(self) -> int:
        """Return the sampling rate of the audio signal in Hz.

        Returns:
            The audio sampling rate in Hz.
        """
        return self.audio_rate_hz

    def get_cfg(self) -> dict[str, Any]:
        """Return the updated configuration dictionary.

        Returns:
            Dictionary containing current configuration parameters.
        """
        return self.get_params()

    def has_data(self) -> bool:
        """Check if there's still audio data available.

        Returns:
            True if audio data is available, False otherwise.
        """
        return len(self.audio_data) > 0

    def _generate_synthetic_audio(self) -> None:
        """Generate synthetic audio data for testing purposes."""
        # Generate 1 second of synthetic audio at the configured sample rate
        duration_seconds = 1.0
        sample_count = int(self.audio_rate_hz * duration_seconds)

        # Generate a simple sine wave at 600 Hz for testing
        t = np.linspace(0, duration_seconds, sample_count, endpoint=False)
        frequency = 600.0  # Hz
        amplitude = 0.5

        # Create synthetic Morse-like pattern: tone, silence, tone, silence
        pattern_length = sample_count // 4
        audio_data: list[np.ndarray] = []

        for i in range(4):
            if i % 2 == 0:
                # Tone segments
                segment = amplitude * np.sin(2 * np.pi * frequency * t[i * pattern_length : (i + 1) * pattern_length])
            else:
                # Silence segments
                segment = np.zeros(pattern_length)
            audio_data.extend(segment)

        self.audio_data = np.array(audio_data, dtype=np.float32)
        self.logger.info(
            "Generated synthetic audio data: %d samples at %d Hz",
            len(self.audio_data),
            self.audio_rate_hz,
        )
