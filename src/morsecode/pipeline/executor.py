"""Pipeline executor for Morse code processing.

This module provides the main execution engine for processing audio through
the signal processing and decoding pipeline.
"""

import logging
from collections.abc import Iterator
from typing import Any

from util.config.models import MorseConfig

from ..interfaces.audio import AudioSource
from ..interfaces.decoder import MorseDecoder
from ..interfaces.signal import SignalProcessor

logger = logging.getLogger(__name__)


class PipelineExecutor:
    """Executes the Morse code processing pipeline.

    This class coordinates the flow of data through the processing pipeline,
    from audio input through signal processing to final decoded output.

    Example:
        ```python
        executor = PipelineExecutor(audio_source, signal_processor, decoder)

        # Process in real-time
        for decoded_text in executor.process_stream():
            print(f"Decoded: {decoded_text}")

        # Process entire stream
        result = executor.process_complete()
        print(f"Complete result: {result}")
        ```
    """

    def __init__(
        self,
        audio_source: AudioSource,
        signal_processor: SignalProcessor,
        decoder: MorseDecoder,
        config: MorseConfig | None = None,
    ):
        """Initialize the pipeline executor.

        Args:
            audio_source: Audio input source
            signal_processor: Signal processing component
            decoder: Morse code decoder
            config: Optional configuration object
        """
        self.logger = logging.getLogger(__name__)
        self.audio_source = audio_source
        self.signal_processor = signal_processor
        self.decoder = decoder
        self.config = config

        self.logger.info("Pipeline executor initialized")
        self.logger.debug("Audio source: %s", type(audio_source).__name__)
        self.logger.debug("Signal processor: %s", type(signal_processor).__name__)
        self.logger.debug("Decoder: %s", type(decoder).__name__)

    def process_stream(self) -> Iterator[str]:
        """Process audio stream and yield decoded text as it becomes available.

        Yields:
            Decoded text fragments as they are identified

        Example:
            ```python
            for text_fragment in executor.process_stream():
                print(f"Decoded: {text_fragment}")
            ```
        """
        self.logger.info("Starting stream processing")

        try:
            chunk_size_ms = self.config.audio.chunk_size_ms if self.config else 50

            while self.audio_source.has_data():
                # Get audio chunk
                audio_chunk = self.audio_source.get_next_chunk(chunk_size_ms)

                # Process signal
                tone_detected = self.signal_processor.detect_tone(audio_chunk)

                # Decode Morse patterns
                self.decoder.process_detection(tone_detected, chunk_size_ms)

                # Yield any available decoded text
                decoded_text = self.decoder.get_decoded_text()
                if decoded_text:
                    self.logger.debug("Decoded text: %s", decoded_text)
                    yield decoded_text

        except Exception as e:
            self.logger.error("Error during stream processing: %s", e)
            raise

        self.logger.info("Stream processing completed")

    def process_complete(self) -> str:
        """Process the complete audio stream and return final decoded text.

        Returns:
            Complete decoded text from the entire audio stream

        Example:
            ```python
            result = executor.process_complete()
            print(f"Complete message: {result}")
            ```
        """
        self.logger.info("Starting complete processing")

        decoded_fragments = []

        try:
            for fragment in self.process_stream():
                decoded_fragments.append(fragment)

            # Get any remaining decoded text
            final_text = self.decoder.get_decoded_text()
            if final_text:
                decoded_fragments.append(final_text)

        except Exception as e:
            self.logger.error("Error during complete processing: %s", e)
            raise

        complete_result = "".join(decoded_fragments)
        self.logger.info("Complete processing finished. Result length: %d characters", len(complete_result))
        return complete_result

    def reset(self) -> None:
        """Reset the pipeline to process a new stream.

        This resets all components to their initial state for processing
        a fresh audio stream.
        """
        self.logger.info("Resetting pipeline")

        # Reset decoder state
        if hasattr(self.decoder, "reset"):
            self.decoder.reset()

        # Reset signal processor if needed
        if hasattr(self.signal_processor, "reset"):
            self.signal_processor.reset()

        self.logger.debug("Pipeline reset completed")

    def get_statistics(self) -> dict[str, Any]:
        """Get processing statistics from pipeline components.

        Returns:
            Dictionary containing processing statistics and metrics
        """
        stats: dict[str, Any] = {
            "audio_source": type(self.audio_source).__name__,
            "signal_processor": type(self.signal_processor).__name__,
            "decoder": type(self.decoder).__name__,
        }

        # Collect component-specific statistics if available
        if hasattr(self.signal_processor, "get_statistics"):
            stats["signal_stats"] = self.signal_processor.get_statistics()

        if hasattr(self.decoder, "get_statistics"):
            stats["decoder_stats"] = self.decoder.get_statistics()

        return stats
