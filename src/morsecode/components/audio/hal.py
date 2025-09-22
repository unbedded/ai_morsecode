"""Hardware Abstraction Layer (HAL) for reading chunks of audio data.

This module provides functionality to read and process audio data from a WAV file.
It supports configuration management and logging for debugging and error handling.

Example usage:
    ```python
    from morsecode.components.audio.hal import HardwareAbstractionLayer
    from util.config import AwesomeConfigManager

    config_manager = AwesomeConfigManager()
    hal = HardwareAbstractionLayer(config_manager)
    audio_chunk = hal.get_next_chunk(update_interval_ms=100)
    ```
"""

from pathlib import Path
from typing import Any

import numpy as np
from scipy.io import wavfile

from morsecode.components.audio.keys import CfgKey, CfgSection
from morsecode.components.audio.schema import ConfigSchema
from morsecode.events.bus import get_global_event_bus
from morsecode.events.types import AudioChunkEvent
from util.config import ConfigurableBase

# Constants
DEFAULT_WAV_FILENAME = None
DEFAULT_AUDIO_RATE_HZ = 44100


class HardwareAbstractionLayer(ConfigurableBase):
    """A class to handle audio data processing from a WAV file.

    This class provides methods to load audio files and retrieve chunks of audio data
    for real-time processing. It maintains internal state for continuous chunk reading.

    Uses ConfigurableBase inheritance pattern for type-safe configuration access
    and runtime reconfiguration support.

    Attributes:
        audio_data: The audio data loaded from the WAV file.
        audio_rate_hz: The sampling rate of the audio data in Hz.
        wav_filename: Path to the WAV file being processed.
    """

    # ConfigurableBase requirements
    CONFIG_SCHEMA = ConfigSchema
    CONFIG_SECTION = CfgSection.AUDIO.value
    CONFIG_KEYS = CfgKey

    def __init__(self, cfg_mgr, overrides=None) -> None:
        """Initialize the HardwareAbstractionLayer with ConfigurableBase pattern.

        Args:
            cfg_mgr: Config manager for enum-based configuration.
            overrides: Optional configuration overrides for testing/tuning.
        """
        # Call ConfigurableBase constructor (handles all config/logging boilerplate)
        super().__init__(cfg_mgr, overrides)

        # Initialize audio processing state after configuration is loaded
        self.audio_data: np.ndarray = np.array([])
        self._chunk_counter: int = 0

        # Get global event bus for publishing events
        self._event_bus = get_global_event_bus()

        self.load_audio_file()
        self.logger.info(
            "HardwareAbstractionLayer initialized with file=%s, rate=%d Hz", self.wav_filename, self.audio_rate_hz
        )

    def _load_config_values(self) -> None:
        """Load configuration values using type-safe enum access.

        This method is called by ConfigurableBase during initialization and reconfiguration.
        Only method we need to implement - all boilerplate handled by base class.
        """
        # STEP 1: Load core configuration with type safety
        self.audio_rate_hz: int = self._cfg_section.get_int(CfgKey.SAMPLE_RATE)
        self.wav_filename: str | None = self._cfg_section.get_string(CfgKey.WAV_FILENAME)
        self.auto_gain_control: bool = self._cfg_section.get_bool(CfgKey.AUTO_GAIN_CONTROL)
        self.chunk_size_ms: int = self._cfg_section.get_int(CfgKey.CHUNK_SIZE_MS)

        # STEP 2: Global config for cross-cutting concerns (recommended pattern)
        try:
            global_cfg = self._cfg_mgr.get_section("global")
            self.debug = global_cfg.get_bool("debug")
            self.timeout_ms = global_cfg.get_int("timeout_ms")
        except (KeyError, ValueError):
            # Global config section may not exist or have values
            self.debug = False
            self.timeout_ms = 30000

        # STEP 3: Log completion with lazy % formatting (CRITICAL!)
        self.logger.info(
            "HardwareAbstractionLayer configured: rate=%d Hz, file=%s, agc=%s, chunk=%d ms",
            self.audio_rate_hz,
            self.wav_filename,
            self.auto_gain_control,
            self.chunk_size_ms,
        )

        # STEP 4: Debug logging controlled by config (not code!)
        self.logger.debug("Internal state: ready for audio processing")

    def _on_reconfiguration(self) -> None:
        """Handle reconfiguration side effects.

        Called by ConfigurableBase after configuration values are reloaded.
        Reload audio file if the filename changed.
        """
        # Reset audio processing state
        self.audio_data = np.array([])
        self._chunk_counter = 0

        # Reload audio file with new configuration
        try:
            self.load_audio_file()
            self.logger.info(
                "HardwareAbstractionLayer reconfigured with file=%s, rate=%d Hz", self.wav_filename, self.audio_rate_hz
            )
        except Exception as e:
            self.logger.exception("Error during HardwareAbstractionLayer reconfiguration: %s", str(e))
            raise RuntimeError(f"Failed to reconfigure audio HAL: {e}") from e

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

            # Simple, clean logging
            self.logger.info("Audio file loaded: %s @ %dHz", self.wav_filename, self.audio_rate_hz)
            self.logger.info(
                "Audio data length: %d samples (%.2f seconds)",
                len(self.audio_data),
                len(self.audio_data) / self.audio_rate_hz,
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
        has_data = len(self.audio_data) > 0
        self.logger.debug("has_data() check: audio_data length=%d, result=%s", len(self.audio_data), has_data)
        return has_data

    def _generate_synthetic_audio(self) -> None:
        """Generate synthetic audio data for testing purposes."""
        # Generate 1 second of synthetic audio at the configured sample rate
        duration_seconds = 1.0
        sample_count = int(self.audio_rate_hz * duration_seconds)

        # Generate a simple sine wave at the configured signal frequency for testing
        t = np.linspace(0, duration_seconds, sample_count, endpoint=False)

        # Get the target frequency from signal configuration for realistic test audio
        try:
            signal_cfg = self._cfg_mgr.get_section("signal")
            frequency = float(signal_cfg.get_int("frequency_hz"))
        except (KeyError, ValueError, AttributeError):
            frequency = 600.0  # Safe fallback for test audio

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
