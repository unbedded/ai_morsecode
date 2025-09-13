"""Signal processing protocols and interfaces.

This module defines the contracts for signal processing components that
analyze audio data and detect tones or other signal characteristics.
"""

from typing import Protocol
import numpy as np


class SignalProcessor(Protocol):
    """Protocol for signal processing components.

    This protocol defines the interface for components that analyze audio
    data to detect tones, frequencies, or other signal characteristics.
    Examples of implementations:
    - FFT-based tone detectors
    - Correlation-based detectors
    - Machine learning classifiers
    - Bandpass filter + envelope detectors

    The protocol focuses on the core functionality needed by the Morse
    decoder pipeline while allowing for different detection algorithms.
    """

    def detect_tone(self, audio_data: np.ndarray) -> bool:
        """Detect if the target tone is present in audio data.

        Args:
            audio_data: Audio samples as numpy array. The shape and dtype
                       should match what the processor expects.

        Returns:
            True if the target tone is detected, False otherwise.
            The decision threshold is implementation-specific.

        Example:
            ```python
            chunk = audio_source.get_next_chunk(20)
            is_tone_present = processor.detect_tone(chunk)
            if is_tone_present:
                print("Tone detected!")
            ```
        """
        ...

    def get_dominant_frequency(self, audio_data: np.ndarray) -> float:
        """Get the dominant frequency in the audio data.

        Args:
            audio_data: Audio samples as numpy array.

        Returns:
            Dominant frequency in Hz. Returns 0.0 if no significant
            frequency can be determined.

        Example:
            ```python
            freq = processor.get_dominant_frequency(chunk)
            print(f"Dominant frequency: {freq:.1f} Hz")
            ```
        """
        ...

    def get_signal_strength(self, audio_data: np.ndarray) -> float:
        """Get the signal strength/amplitude.

        Args:
            audio_data: Audio samples as numpy array.

        Returns:
            Signal strength as a normalized value between 0.0 and 1.0.
            0.0 indicates no signal, 1.0 indicates maximum signal.

        Example:
            ```python
            strength = processor.get_signal_strength(chunk)
            if strength > 0.5:
                print("Strong signal detected")
            ```
        """
        ...

    def get_detection_confidence(self, audio_data: np.ndarray) -> float:
        """Get confidence level of the last tone detection.

        Args:
            audio_data: Audio samples as numpy array.

        Returns:
            Confidence level between 0.0 and 1.0.
            0.0 indicates no confidence, 1.0 indicates high confidence.
            This can be used for adaptive thresholding or quality metrics.

        Example:
            ```python
            detected = processor.detect_tone(chunk)
            confidence = processor.get_detection_confidence(chunk)
            if detected and confidence > 0.8:
                print("High-confidence tone detection")
            ```
        """
        ...

    def get_target_frequency(self) -> float:
        """Get the target frequency this processor is configured for.

        Returns:
            Target frequency in Hz that this processor is designed to detect.

        Example:
            ```python
            target_freq = processor.get_target_frequency()
            print(f"Listening for {target_freq} Hz tone")
            ```
        """
        ...