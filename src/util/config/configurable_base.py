"""Configurable Component Base Classes.

This module provides the interface and base class for components that support
runtime configuration with type-safe enum-based access patterns.

The ConfigurableBase class eliminates boilerplate code by handling:
- Configuration manager registration
- Schema validation setup
- Logger initialization
- Runtime reconfiguration support

Example:
    ```python
    from util.config.configurable_base import ConfigurableBase
    from your_component.keys import YourCfgKey
    from your_component.schema import YourSchema

    class YourComponent(ConfigurableBase):
        CONFIG_SCHEMA = YourSchema
        CONFIG_SECTION = "your_section"
        CONFIG_KEYS = YourCfgKey

        def _load_config_values(self) -> None:
            self.frequency_hz = self._cfg_section.get_int(self.CONFIG_KEYS.FREQUENCY)
            self.threshold = self._cfg_section.get_double(self.CONFIG_KEYS.THRESHOLD)

            self.logger.info("Component configured: freq=%d Hz", self.frequency_hz)
    ```
"""

from abc import ABC, abstractmethod
from typing import Any

from util.config import AwesomeConfigManager
from util.logging import ComponentLogger


class IConfigurable(ABC):
    """Interface for components supporting runtime configuration.

    Components implementing this interface can be reconfigured at runtime
    without recreating the component instance. This is useful for:
    - Parameter tuning during operation
    - Dynamic configuration updates
    - A/B testing with different configurations
    """

    # Class attributes that concrete implementations must define
    CONFIG_SCHEMA: type[Any]  # Component's pydantic schema class
    CONFIG_SECTION: str  # Section name in YAML configuration
    CONFIG_KEYS: type[Any]  # Component's configuration keys enum

    @abstractmethod
    def reconfigure(self, overrides: dict[str, Any]) -> None:
        """Apply new configuration without recreating component.

        Args:
            overrides: Dictionary of configuration overrides to apply
                      Keys should match the configuration schema fields
        """
        pass


class ConfigurableBase(IConfigurable):
    """Base class eliminating configuration and logging boilerplate.

    This class provides a unified pattern for components that need:
    - Type-safe configuration access via enums
    - Automatic logger setup with ComponentLogger
    - Runtime reconfiguration support
    - Schema validation and registration

    Concrete components only need to implement _load_config_values() method
    and define the three class attributes: CONFIG_SCHEMA, CONFIG_SECTION, CONFIG_KEYS.

    The base class handles all the repetitive configuration and logging setup
    that every component would otherwise need to implement.
    """

    def __init__(self, cfg_mgr: AwesomeConfigManager, overrides: dict[str, Any] | None = None):
        """Initialize configurable component with automatic setup.

        Args:
            cfg_mgr: Configuration manager for schema registration and access
            overrides: Optional configuration overrides to apply
        """
        # STEP 1: Initialize logger FIRST (required by CLAUDE.md)
        self.logger = ComponentLogger(__name__, cfg_mgr)
        self.logger.info("%s initializing...", self.__class__.__name__)

        # STEP 2: Store config manager reference for reconfiguration
        self._cfg_mgr = cfg_mgr
        self._cfg_section: Any = None  # Will be populated in _configure()

        # STEP 3: Perform initial configuration setup
        self._configure(cfg_mgr, overrides)

    def reconfigure(self, overrides: dict[str, Any]) -> None:
        """Runtime reconfiguration without recreating component.

        This method allows components to be reconfigured dynamically:
        1. Apply new configuration overrides
        2. Reload configuration values
        3. Trigger any reconfiguration side effects

        Args:
            overrides: Dictionary of configuration overrides to apply
        """
        self.logger.info("%s reconfiguring with overrides: %s", self.__class__.__name__, list(overrides.keys()))

        self._cfg_section.apply_overrides(overrides)
        self._load_config_values()
        self._on_reconfiguration()

        self.logger.info("%s reconfiguration complete", self.__class__.__name__)

    def _configure(self, cfg_mgr: AwesomeConfigManager, overrides: dict[str, Any] | None = None):
        """Internal configuration setup method.

        This method handles the standard configuration setup pattern:
        1. Register component schema with configuration manager
        2. Register logging configuration for this component
        3. Get configuration section for type-safe access
        4. Apply any initial overrides
        5. Load configuration values into component attributes

        Args:
            cfg_mgr: Configuration manager for registration
            overrides: Optional initial configuration overrides
        """
        # Register component schema and logging configuration
        cfg_mgr.register_enum_config(self.CONFIG_SECTION, self.CONFIG_SCHEMA)
        cfg_mgr.register_logging_config(__name__, default_level="INFO")

        # Get type-safe configuration section
        self._cfg_section = cfg_mgr.get_section(self.CONFIG_SECTION)

        # Apply initial overrides if provided
        if overrides:
            self.logger.debug("Applying initial configuration overrides: %s", list(overrides.keys()))
            self._cfg_section.apply_overrides(overrides)

        # Load configuration values into component attributes
        self._load_config_values()

    @abstractmethod
    def _load_config_values(self) -> None:
        """Load configuration values into component attributes.

        This is the only method concrete components must implement.
        Use self._cfg_section.get_int(), get_double(), get_string(), etc.
        with self.CONFIG_KEYS enum values for type-safe access.

        Example:
            ```python
            def _load_config_values(self) -> None:
                self.frequency_hz = self._cfg_section.get_int(self.CONFIG_KEYS.FREQUENCY)
                self.threshold = self._cfg_section.get_double(self.CONFIG_KEYS.THRESHOLD)

                self.logger.info("Component configured: freq=%d Hz, threshold=%.2f",
                               self.frequency_hz, self.threshold)
            ```
        """
        pass

    def _on_reconfiguration(self) -> None:
        """Optional hook for reconfiguration side effects.

        Override this method if your component needs to perform additional
        actions when reconfigured, such as:
        - Restarting internal processes
        - Clearing caches
        - Reinitializing filters or algorithms
        - Notifying dependent components

        This method is called after _load_config_values() during reconfiguration.
        """
        pass
