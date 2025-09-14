"""Dependency injection container for managing component lifecycle.

This module provides a simple dependency injection container that manages
the creation and lifecycle of components using the factory pattern.
"""

import logging
from typing import Any, TypeVar, cast

from ..components.factory import ComponentFactory
from ..config.manager import AwesomeConfigManager
from ..interfaces.audio import AudioSource
from ..interfaces.decoder import MorseDecoder
from ..interfaces.signal import SignalProcessor

logger = logging.getLogger(__name__)

T = TypeVar("T")


class Container:
    """Simple dependency injection container.

    This container manages component creation using factories and configuration.
    It provides a centralized way to resolve dependencies and manage component
    lifecycle while maintaining loose coupling between components.

    Example:
        ```python
        container = Container()
        container.configure_from_config("morse.yaml")

        # Resolve components
        audio_source = container.resolve(AudioSource)
        processor = container.resolve(SignalProcessor)
        decoder = container.resolve(MorseDecoder)
        ```
    """

    def __init__(self) -> None:
        """Initialize the dependency injection container."""
        self.logger = logging.getLogger(__name__)
        self._factory = ComponentFactory()
        self._config_manager: AwesomeConfigManager | None = None
        self._singletons: dict[type, Any] = {}
        self._registered_configs: dict[type, str] = {
            AudioSource: "audio",
            SignalProcessor: "signal",
            MorseDecoder: "decoder",
        }

    def configure_from_config(self, config_file: str, profile: str | None = None) -> None:
        """Configure container from YAML configuration file.

        Args:
            config_file: Path to YAML configuration file
            profile: Optional profile name for configuration overrides
        """
        self._config_manager = AwesomeConfigManager(config_file, profile)
        self.logger.info("Container configured from: %s (profile: %s)", config_file, profile)

    def configure_from_manager(self, config_manager: AwesomeConfigManager) -> None:
        """Configure container from existing config manager.

        Args:
            config_manager: Pre-configured AwesomeConfigManager instance
        """
        self._config_manager = config_manager
        self.logger.info("Container configured from existing config manager")

    def register_component_config(self, component_type: type, config_key: str) -> None:
        """Register which config section to use for a component type.

        Args:
            component_type: The protocol type (AudioSource, SignalProcessor, etc.)
            config_key: Configuration section name (audio, signal, decoder, etc.)
        """
        self._registered_configs[component_type] = config_key
        self.logger.debug(
            "Registered config mapping: %s -> %s", component_type.__name__, config_key
        )

    def resolve(self, component_type: type[T], *, singleton: bool = True) -> T:
        """Resolve a component instance by type.

        Args:
            component_type: The protocol type to resolve (AudioSource, SignalProcessor,
                MorseDecoder)
            singleton: Whether to reuse the same instance (default: True)

        Returns:
            Configured component instance implementing the requested protocol

        Raises:
            ValueError: If component type is not registered or config manager not set

        Example:
            ```python
            audio_source = container.resolve(AudioSource)
            processor = container.resolve(SignalProcessor, singleton=False)  # Always new instance
            ```
        """
        if self._config_manager is None:
            raise ValueError("Container not configured. Call configure_from_config() first.")

        if component_type not in self._registered_configs:
            raise ValueError(f"Unknown component type: {component_type.__name__}")

        # Return singleton if already created
        if singleton and component_type in self._singletons:
            self.logger.debug("Returning singleton instance of %s", component_type.__name__)
            return cast(T, self._singletons[component_type])

        # Get configuration for this component type
        config_key = self._registered_configs[component_type]
        config = self._config_manager.get_config(config_key)

        # Create instance using factory
        try:
            if component_type == AudioSource:
                instance = cast(T, self._factory.create_audio_source(config))
            elif component_type == SignalProcessor:
                instance = cast(T, self._factory.create_signal_processor(config))
            elif component_type == MorseDecoder:
                instance = cast(T, self._factory.create_decoder(config))
            else:
                raise ValueError(f"No factory method for {component_type.__name__}")

            self.logger.debug(
                "Created %s instance with config: %s", component_type.__name__, config_key
            )

            # Store as singleton if requested
            if singleton:
                self._singletons[component_type] = instance

            return instance

        except Exception as e:
            self.logger.error("Failed to resolve %s: %s", component_type.__name__, e)
            raise ValueError(f"Cannot resolve {component_type.__name__}: {e}") from e

    def clear_singletons(self) -> None:
        """Clear all singleton instances, forcing fresh creation on next resolve."""
        self._singletons.clear()
        self.logger.debug("Cleared all singleton instances")

    def get_config_manager(self) -> AwesomeConfigManager | None:
        """Get the current configuration manager.

        Returns:
            Current AwesomeConfigManager instance or None if not configured
        """
        return self._config_manager


# Global container instance for application use
_global_container: Container | None = None


def get_container() -> Container:
    """Get the global container instance, creating it if needed.

    Returns:
        Global Container instance

    Example:
        ```python
        from morsecode.pipeline.container import get_container

        container = get_container()
        audio_source = container.resolve(AudioSource)
        ```
    """
    global _global_container
    if _global_container is None:
        _global_container = Container()
    return _global_container


def configure_global_container(config_file: str, profile: str | None = None) -> None:
    """Configure the global container from a config file.

    Args:
        config_file: Path to YAML configuration file
        profile: Optional profile name for configuration overrides

    Example:
        ```python
        configure_global_container("morse.yaml", "debug")
        container = get_container()
        # Container is now configured and ready to use
        ```
    """
    container = get_container()
    container.configure_from_config(config_file, profile)
    logger.info("Global container configured from: %s", config_file)
