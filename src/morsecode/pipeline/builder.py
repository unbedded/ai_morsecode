"""Pipeline builder for constructing and configuring Morse code processing pipelines.

This module provides a fluent builder interface for creating processing pipelines
with customizable components, configuration, and execution strategies.
"""

import logging

from util.config.config_manager import AwesomeConfigManager
from util.config.models import MorseConfig

from ..interfaces.audio import AudioSource
from ..interfaces.decoder import MorseDecoder
from ..interfaces.signal import SignalProcessor
from .container import Container
from .executor import PipelineExecutor

logger = logging.getLogger(__name__)


class PipelineBuilder:
    """Fluent builder for creating Morse code processing pipelines.

    This builder allows step-by-step construction of processing pipelines with
    dependency injection, configuration management, and execution strategies.

    Example:
        ```python
        # Build pipeline from configuration file
        pipeline = (PipelineBuilder()
                   .from_config_file("morse.yaml", profile="debug")
                   .build())

        # Build pipeline with custom components
        pipeline = (PipelineBuilder()
                   .with_audio_source(custom_audio)
                   .with_signal_processor(custom_processor)
                   .with_decoder(custom_decoder)
                   .build())

        # Mixed configuration and custom components
        pipeline = (PipelineBuilder()
                   .from_config_file("morse.yaml")
                   .with_custom_decoder(my_decoder)  # Override config
                   .build())
        ```
    """

    def __init__(self) -> None:
        """Initialize the pipeline builder."""
        self.logger = logging.getLogger(__name__)
        self._container = Container()
        self._custom_audio: AudioSource | None = None
        self._custom_signal: SignalProcessor | None = None
        self._custom_decoder: MorseDecoder | None = None
        self._config: MorseConfig | None = None

    def from_config_file(self, config_file: str, profile: str | None = None) -> "PipelineBuilder":
        """Configure pipeline from YAML configuration file.

        Args:
            config_file: Path to YAML configuration file
            profile: Optional profile name for configuration overrides

        Returns:
            Self for method chaining
        """
        self._container.configure_from_config(config_file, profile)
        config_manager = self._container.get_config_manager()
        if config_manager:
            self._config = MorseConfig.from_config_manager(config_manager)
        self.logger.info("Pipeline configured from file: %s (profile: %s)", config_file, profile)
        return self

    def from_config_manager(self, config_manager: AwesomeConfigManager) -> "PipelineBuilder":
        """Configure pipeline from existing config manager.

        Args:
            config_manager: Pre-configured AwesomeConfigManager instance

        Returns:
            Self for method chaining
        """
        self._container.configure_from_manager(config_manager)
        self._config = MorseConfig.from_config_manager(config_manager)
        self.logger.info("Pipeline configured from config manager")
        return self

    def from_config(self, config: MorseConfig) -> "PipelineBuilder":
        """Configure pipeline from MorseConfig object.

        Args:
            config: Complete configuration object

        Returns:
            Self for method chaining
        """
        self._config = config
        # Create config manager from the structured config
        # This is simplified - in practice we might serialize back to YAML
        self.logger.info("Pipeline configured from MorseConfig object")
        return self

    def with_audio_source(self, audio_source: AudioSource) -> "PipelineBuilder":
        """Set custom audio source, overriding configuration.

        Args:
            audio_source: Custom AudioSource implementation

        Returns:
            Self for method chaining
        """
        self._custom_audio = audio_source
        self.logger.info("Custom audio source configured: %s", type(audio_source).__name__)
        return self

    def with_signal_processor(self, signal_processor: SignalProcessor) -> "PipelineBuilder":
        """Set custom signal processor, overriding configuration.

        Args:
            signal_processor: Custom SignalProcessor implementation

        Returns:
            Self for method chaining
        """
        self._custom_signal = signal_processor
        self.logger.info("Custom signal processor configured: %s", type(signal_processor).__name__)
        return self

    def with_decoder(self, decoder: MorseDecoder) -> "PipelineBuilder":
        """Set custom decoder, overriding configuration.

        Args:
            decoder: Custom MorseDecoder implementation

        Returns:
            Self for method chaining
        """
        self._custom_decoder = decoder
        self.logger.info("Custom decoder configured: %s", type(decoder).__name__)
        return self

    def build(self) -> PipelineExecutor:
        """Build and return the configured pipeline executor.

        Returns:
            Configured PipelineExecutor ready for processing

        Raises:
            ValueError: If pipeline is not properly configured
        """
        if not self._container.get_config_manager() and not any(
            [self._custom_audio, self._custom_signal, self._custom_decoder]
        ):
            raise ValueError("Pipeline must be configured from config file or have custom components")

        # Resolve or use custom components
        audio_source = self._custom_audio or self._container.resolve(AudioSource)  # type: ignore[type-abstract]
        signal_processor = self._custom_signal or self._container.resolve(SignalProcessor)  # type: ignore[type-abstract]
        decoder = self._custom_decoder or self._container.resolve(MorseDecoder)  # type: ignore[type-abstract]

        # Create and configure executor
        executor = PipelineExecutor(
            audio_source=audio_source,
            signal_processor=signal_processor,
            decoder=decoder,
            config=self._config,
        )

        self.logger.info("Pipeline built successfully")
        return executor
