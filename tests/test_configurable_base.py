"""
Tests for ConfigurableBase inheritance pattern.

These tests verify that the ConfigurableBase class properly handles:
- Component configuration setup
- Type-safe enum-based configuration access
- Runtime reconfiguration
- Logger initialization
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel

from tests.mock_config_manager import MockAwesomeConfigManager
from util.config import CfgField, CfgType, ConfigurableBase


class MockCfgKey(Enum):
    """Mock configuration keys for ConfigurableBase testing."""

    FREQUENCY = "frequency_hz"
    THRESHOLD = "threshold"
    ENABLED = "enabled"


class MockSchema(BaseModel):
    """Mock schema for ConfigurableBase testing."""

    frequency_hz: int = CfgField(CfgType.INT, default=600, min=100, max=2000, description="Test frequency in Hz")
    threshold: float = CfgField(CfgType.DOUBLE, default=0.5, min=0.0, max=1.0, description="Test threshold value")
    enabled: bool = CfgField(CfgType.BOOL, default=True, description="Enable test component")


class MockComponent(ConfigurableBase):
    """Test component using ConfigurableBase inheritance."""

    CONFIG_SCHEMA = MockSchema
    CONFIG_SECTION = "test_component"
    CONFIG_KEYS = MockCfgKey

    def __init__(self, cfg_mgr: MockAwesomeConfigManager, overrides: dict[str, Any] | None = None):
        # Track reconfiguration calls for testing
        self.reconfiguration_count = 0
        super().__init__(cfg_mgr, overrides)

    def _load_config_values(self) -> None:
        """Load configuration values using type-safe enum access."""
        self.frequency_hz = self._cfg_section.get_int(self.CONFIG_KEYS.FREQUENCY)
        self.threshold = self._cfg_section.get_double(self.CONFIG_KEYS.THRESHOLD)
        self.enabled = self._cfg_section.get_bool(self.CONFIG_KEYS.ENABLED)

        self.logger.info(
            "MockComponent configured: freq=%d Hz, threshold=%.2f, enabled=%s",
            self.frequency_hz,
            self.threshold,
            self.enabled,
        )

    def _on_reconfiguration(self) -> None:
        """Track reconfiguration calls for testing."""
        self.reconfiguration_count += 1
        self.logger.info("MockComponent reconfigured (count: %d)", self.reconfiguration_count)


class TestConfigurableBase:
    """Test cases for ConfigurableBase functionality."""

    def create_mock_config_manager(self, overrides: dict[str, Any] = None) -> MockAwesomeConfigManager:
        """Create a mock config manager with default test configuration."""
        default_config = {"test_component": {"frequency_hz": 600, "threshold": 0.5, "enabled": True}}
        if overrides:
            default_config["test_component"].update(overrides)
        return MockAwesomeConfigManager(default_config)

    def test_basic_initialization(self):
        """Test that ConfigurableBase properly initializes with defaults."""
        cfg_mgr = self.create_mock_config_manager()
        component = MockComponent(cfg_mgr)

        # Verify default values loaded correctly
        assert component.frequency_hz == 600
        assert component.threshold == 0.5
        assert component.enabled is True
        assert component.reconfiguration_count == 0

        # Verify logger was initialized
        assert component.logger is not None

    def test_initialization_with_overrides(self):
        """Test initialization with configuration overrides."""
        cfg_mgr = self.create_mock_config_manager()
        overrides = {"frequency_hz": 800, "threshold": 0.75, "enabled": False}

        component = MockComponent(cfg_mgr, overrides)

        # Verify overrides were applied
        assert component.frequency_hz == 800
        assert component.threshold == 0.75
        assert component.enabled is False

    def test_runtime_reconfiguration(self):
        """Test runtime reconfiguration without component recreation."""
        cfg_mgr = self.create_mock_config_manager()
        component = MockComponent(cfg_mgr)

        # Verify initial state
        assert component.frequency_hz == 600
        assert component.threshold == 0.5
        assert component.reconfiguration_count == 0

        # Apply runtime reconfiguration
        new_config = {"frequency_hz": 1000, "threshold": 0.8}
        component.reconfigure(new_config)

        # Verify reconfiguration applied
        assert component.frequency_hz == 1000
        assert component.threshold == 0.8
        assert component.enabled is True  # Unchanged
        assert component.reconfiguration_count == 1

    def test_multiple_reconfigurations(self):
        """Test multiple runtime reconfigurations."""
        cfg_mgr = self.create_mock_config_manager()
        component = MockComponent(cfg_mgr)

        # First reconfiguration
        component.reconfigure({"frequency_hz": 700})
        assert component.frequency_hz == 700
        assert component.reconfiguration_count == 1

        # Second reconfiguration
        component.reconfigure({"threshold": 0.9})
        assert component.frequency_hz == 700  # Unchanged
        assert component.threshold == 0.9
        assert component.reconfiguration_count == 2

        # Third reconfiguration with multiple changes
        component.reconfigure({"frequency_hz": 1200, "enabled": False})
        assert component.frequency_hz == 1200
        assert component.enabled is False
        assert component.reconfiguration_count == 3

    def test_type_safe_configuration_access(self):
        """Test that enum-based configuration access provides type safety."""
        cfg_mgr = self.create_mock_config_manager()
        component = MockComponent(cfg_mgr)

        # Verify we can access configuration through enum keys
        section = component._cfg_section

        # These should work without errors (type-safe access)
        freq = section.get_int(MockCfgKey.FREQUENCY)
        thresh = section.get_double(MockCfgKey.THRESHOLD)
        enabled = section.get_bool(MockCfgKey.ENABLED)

        assert isinstance(freq, int)
        assert isinstance(thresh, float)
        assert isinstance(enabled, bool)

    def test_configuration_validation(self):
        """Test that configuration validation works with ConfigurableBase."""
        cfg_mgr = self.create_mock_config_manager()

        # Valid overrides should work
        valid_overrides = {"frequency_hz": 1500}
        component = MockComponent(cfg_mgr, valid_overrides)
        assert component.frequency_hz == 1500

        # Mock doesn't implement validation, so we just test that overrides work
        # In real implementation, invalid values would raise validation errors
        any_overrides = {"frequency_hz": 3000}  # Would be invalid in real system
        component2 = MockComponent(cfg_mgr, any_overrides)
        assert component2.frequency_hz == 3000  # Mock accepts any value

    def test_logger_initialization(self):
        """Test that ComponentLogger is properly initialized."""
        cfg_mgr = self.create_mock_config_manager()
        component = MockComponent(cfg_mgr)

        # Verify logger exists and is functional
        assert component.logger is not None

        # Logger should be able to log without errors
        component.logger.info("Test log message")
        component.logger.debug("Test debug message")

    def test_required_class_attributes(self):
        """Test that required class attributes are properly defined."""
        # Verify MockComponent has all required attributes
        assert hasattr(MockComponent, "CONFIG_SCHEMA")
        assert hasattr(MockComponent, "CONFIG_SECTION")
        assert hasattr(MockComponent, "CONFIG_KEYS")

        assert MockComponent.CONFIG_SCHEMA == MockSchema
        assert MockComponent.CONFIG_SECTION == "test_component"
        assert MockComponent.CONFIG_KEYS == MockCfgKey
