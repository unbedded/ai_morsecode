"""Morse code decoding protocols and interfaces.

This module defines the contracts for Morse code decoding components that
convert tone detection events into text characters.
"""

from typing import Protocol


class MorseDecoder(Protocol):
    """Protocol for Morse code decoding components.

    This protocol defines the interface for components that process tone
    detection events and convert them into decoded text. Examples:
    - Timing-based decoders
    - Machine learning decoders
    - Adaptive WPM decoders
    - Pattern recognition decoders

    The protocol supports both streaming (real-time) and batch processing
    of Morse code signals.
    """

    def process_detection(self, tone_detected: bool, duration_ms: float) -> None:
        """Process a tone detection event.

        This method is called for each audio chunk to inform the decoder
        whether a tone was detected and for how long the detection state
        has been active.

        Args:
            tone_detected: True if tone is currently detected, False if silence.
            duration_ms: Duration in milliseconds that this detection state
                        has been active. For streaming processing, this is
                        typically the chunk duration.

        Example:
            ```python
            # Process 20ms chunks
            while audio_source.has_data():
                chunk = audio_source.get_next_chunk(20)
                detected = signal_processor.detect_tone(chunk)
                decoder.process_detection(detected, 20.0)
            ```
        """
        ...

    def get_decoded_text(self) -> str:
        """Get the currently decoded text.

        Returns:
            Decoded Morse code text as a string. May include partial
            characters or words if decoding is still in progress.
            Empty string if no text has been decoded yet.

        Example:
            ```python
            # After processing audio
            text = decoder.get_decoded_text()
            print(f"Decoded: '{text}'")
            ```
        """
        ...

    def finalize(self) -> None:
        """Finalize the decoding process.

        This method should be called when no more audio data will be
        processed. It allows the decoder to:
        - Complete any partial character decoding
        - Flush internal buffers
        - Apply final processing rules

        Should be called before getting the final decoded text.

        Example:
            ```python
            # Process all audio...
            decoder.finalize()
            final_text = decoder.get_decoded_text()
            ```
        """
        ...

    def reset(self) -> None:
        """Reset the decoder to initial state.

        Clears all internal state, decoded text, and buffers.
        After calling reset(), the decoder should behave as if
        it was just created.

        Example:
            ```python
            decoder.reset()
            assert decoder.get_decoded_text() == ""
            ```
        """
        ...

    def get_statistics(self) -> dict[str, int | float]:
        """Get decoding statistics.

        Returns:
            Dictionary containing statistics about the decoding process.
            Common keys include:
            - 'characters_decoded': Number of complete characters decoded
            - 'dots_detected': Number of dots detected
            - 'dashes_detected': Number of dashes detected
            - 'words_decoded': Number of complete words decoded
            - 'estimated_wpm': Current WPM estimate (if available)

        Example:
            ```python
            stats = decoder.get_statistics()
            print(f"Decoded {stats['characters_decoded']} characters")
            print(f"Estimated WPM: {stats.get('estimated_wpm', 'unknown')}")
            ```
        """
        ...

    def set_wpm_estimate(self, wpm: float) -> None:
        """Update the WPM estimate for timing calculations.

        Args:
            wpm: Words per minute estimate. Should be positive.

        Raises:
            ValueError: If wpm is not positive.

        Example:
            ```python
            decoder.set_wpm_estimate(15.0)  # Set to 15 WPM
            ```
        """
        ...
