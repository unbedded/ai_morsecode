"""Audio processing protocols and interfaces.

This module defines the contracts that audio-related components must implement,
enabling flexible audio source implementations and easy testing.
"""

from typing import Protocol
import numpy as np


class AudioSource(Protocol):
    """Protocol for audio data sources.

    This protocol defines the interface that any audio source must implement
    to work with the Morse decoder pipeline. Examples of implementations:
    - WAV file readers
    - Microphone input
    - Network audio streams
    - Test data generators

    The protocol uses structural typing - any class that implements these
    methods will be compatible, regardless of inheritance.
    """

    def has_data(self) -> bool:
        """Check if more audio data is available.

        Returns:
            True if more audio data can be retrieved, False otherwise.

        Example:
            ```python
            while audio_source.has_data():
                chunk = audio_source.get_next_chunk(50)
                process(chunk)
            ```
        """
        ...

    def get_next_chunk(self, duration_ms: int) -> np.ndarray:
        """Get the next chunk of audio data.

        Args:
            duration_ms: Duration of audio to retrieve in milliseconds.
                        Must be positive.

        Returns:
            Audio data as numpy array. Shape and dtype depend on the
            implementation but should be consistent for a given source.

        Raises:
            RuntimeError: If no more data is available (has_data() returned False).
            ValueError: If duration_ms is not positive.

        Example:
            ```python
            chunk = audio_source.get_next_chunk(20)  # 20ms of audio
            assert isinstance(chunk, np.ndarray)
            ```
        """
        ...

    def get_sample_rate(self) -> int:
        """Get the audio sample rate in Hz.

        Returns:
            Sample rate in Hz (e.g., 44100, 48000).
            Must be positive and consistent for the lifetime of the source.

        Example:
            ```python
            rate = audio_source.get_sample_rate()
            assert rate > 0
            # rate might be 44100, 48000, etc.
            ```
        """
        ...

    def get_total_duration_ms(self) -> float | None:
        """Get total duration of audio in milliseconds.

        Returns:
            Total duration in milliseconds, or None if duration is unknown
            (e.g., for live streams, infinite sources).

        Example:
            ```python
            duration = audio_source.get_total_duration_ms()
            if duration is not None:
                print(f"Audio is {duration/1000:.1f} seconds long")
            ```
        """
        ...