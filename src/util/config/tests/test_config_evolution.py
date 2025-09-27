"""
Tests for configuration schema evolution and user edit preservation.

This test module verifies critical configuration management behaviors:
- Schema evolution when new fields are added
- User edit preservation during software updates
- Config file migration and backwards compatibility
- File persistence and write-back behavior

These tests address gaps identified in config management testing.
"""

import tempfile
from enum import Enum
from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import BaseModel

from util.config import AwesomeConfigManager, CfgField, CfgType


class TestCfgKey(Enum):
    """Test configuration keys for schema evolution testing."""

    FREQUENCY = "frequency_hz"
    THRESHOLD = "threshold"
    ENABLED = "enabled"


class TestCfgKeyV2(Enum):
    """Extended test configuration keys (simulating schema evolution)."""

    FREQUENCY = "frequency_hz"
    THRESHOLD = "threshold"
    ENABLED = "enabled"
    NEW_FIELD = "new_field"  # Added in v2
    BANDWIDTH = "bandwidth_hz"  # Added in v2


class TestSchemaV1(BaseModel):
    """Original test schema."""

    frequency_hz: int = CfgField(CfgType.INT, default=600, min=100, max=2000, description="Test frequency in Hz")
    threshold: float = CfgField(CfgType.DOUBLE, default=0.5, min=0.0, max=1.0, description="Test threshold value")
    enabled: bool = CfgField(CfgType.BOOL, default=True, description="Enable test component")


class TestSchemaV2(BaseModel):
    """Evolved test schema with new fields."""

    frequency_hz: int = CfgField(CfgType.INT, default=600, min=100, max=2000, description="Test frequency in Hz")
    threshold: float = CfgField(CfgType.DOUBLE, default=0.5, min=0.0, max=1.0, description="Test threshold value")
    enabled: bool = CfgField(CfgType.BOOL, default=True, description="Enable test component")
    new_field: str = CfgField(CfgType.STRING, default="default_value", description="New field added in v2")
    bandwidth_hz: int = CfgField(CfgType.INT, default=50, min=10, max=200, description="Bandwidth in Hz")


class TestConfigEvolution:
    """Test cases for configuration schema evolution and user edit preservation."""

    def create_test_config_file(self, config_path: Path, config_data: dict[str, Any]) -> None:
        """Create a test configuration file with user data."""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f, default_flow_style=False)

    def read_config_file(self, config_path: Path) -> dict[str, Any]:
        """Read configuration from YAML file."""
        with open(config_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def test_user_edits_preserved_during_schema_registration(self):
        """Test that manual user edits are preserved when new schemas are registered."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "test_config.yaml"

            # Create initial config with user customizations
            user_config = {
                "test_component": {
                    "frequency_hz": 800,  # User customized from default 600
                    "threshold": 0.75,  # User customized from default 0.5
                    "enabled": False,  # User customized from default True
                },
                "application": {
                    "debug": True,  # User customization
                    "log_level": "DEBUG",  # User customization
                },
            }
            self.create_test_config_file(config_path, user_config)

            # Load with original schema
            cfg_mgr = AwesomeConfigManager(config_file=str(config_path))
            cfg_mgr.register_enum_config("test_component", TestSchemaV1)

            # Verify user edits are preserved
            section = cfg_mgr.get_section("test_component")
            assert section.get_int(TestCfgKey.FREQUENCY) == 800  # User value preserved
            assert section.get_double(TestCfgKey.THRESHOLD) == 0.75  # User value preserved
            assert section.get_bool(TestCfgKey.ENABLED) is False  # User value preserved

    def test_schema_evolution_provides_defaults_for_new_fields(self):
        """Test that new schema fields provide defaults without overwriting existing values."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "test_config.yaml"

            # Create initial config with v1 schema data
            v1_config = {
                "test_component": {
                    "frequency_hz": 1000,  # User customization
                    "threshold": 0.8,  # User customization
                    "enabled": False,  # User customization
                }
            }
            self.create_test_config_file(config_path, v1_config)

            # Load with evolved v2 schema (has new fields)
            cfg_mgr = AwesomeConfigManager(config_file=str(config_path))
            cfg_mgr.register_enum_config("test_component", TestSchemaV2)

            section = cfg_mgr.get_section("test_component")

            # Existing fields should preserve user values
            assert section.get_int(TestCfgKeyV2.FREQUENCY) == 1000  # User value preserved
            assert section.get_double(TestCfgKeyV2.THRESHOLD) == 0.8  # User value preserved
            assert section.get_bool(TestCfgKeyV2.ENABLED) is False  # User value preserved

            # New fields should use schema defaults
            assert section.get_string(TestCfgKeyV2.NEW_FIELD) == "default_value"  # Schema default
            assert section.get_int(TestCfgKeyV2.BANDWIDTH) == 50  # Schema default

    def test_missing_config_sections_get_schema_defaults(self):
        """Test that completely missing config sections are populated with schema defaults."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "test_config.yaml"

            # Create config with no test_component section
            minimal_config = {"application": {"debug": False, "log_level": "INFO"}}
            self.create_test_config_file(config_path, minimal_config)

            # Load and register schema for missing section
            cfg_mgr = AwesomeConfigManager(config_file=str(config_path))
            cfg_mgr.register_enum_config("test_component", TestSchemaV1)

            section = cfg_mgr.get_section("test_component")

            # All values should come from schema defaults
            assert section.get_int(TestCfgKey.FREQUENCY) == 600  # Schema default
            assert section.get_double(TestCfgKey.THRESHOLD) == 0.5  # Schema default
            assert section.get_bool(TestCfgKey.ENABLED) is True  # Schema default

    def test_partial_config_sections_preserve_user_values(self):
        """Test that partially configured sections preserve user values and fill missing with defaults."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "test_config.yaml"

            # Create config with only some fields configured
            partial_config = {
                "test_component": {
                    "frequency_hz": 1500,  # User value
                    # threshold missing - should get default
                    "enabled": False,  # User value
                }
            }
            self.create_test_config_file(config_path, partial_config)

            cfg_mgr = AwesomeConfigManager(config_file=str(config_path))
            cfg_mgr.register_enum_config("test_component", TestSchemaV1)

            section = cfg_mgr.get_section("test_component")

            # User values preserved
            assert section.get_int(TestCfgKey.FREQUENCY) == 1500  # User value
            assert section.get_bool(TestCfgKey.ENABLED) is False  # User value

            # Missing field gets schema default
            assert section.get_double(TestCfgKey.THRESHOLD) == 0.5  # Schema default

    def test_invalid_user_values_fallback_to_schema_defaults(self):
        """Test that invalid user values fall back to schema defaults gracefully."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "test_config.yaml"

            # Create config with invalid values
            invalid_config = {
                "test_component": {
                    "frequency_hz": "invalid_number",  # Invalid type
                    "threshold": None,  # Null/None value
                    "enabled": "maybe",  # Invalid boolean
                }
            }
            self.create_test_config_file(config_path, invalid_config)

            cfg_mgr = AwesomeConfigManager(config_file=str(config_path))
            cfg_mgr.register_enum_config("test_component", TestSchemaV1)

            section = cfg_mgr.get_section("test_component")

            # All should fall back to schema defaults
            assert section.get_int(TestCfgKey.FREQUENCY) == 600  # Schema default
            assert section.get_double(TestCfgKey.THRESHOLD) == 0.5  # Schema default
            assert section.get_bool(TestCfgKey.ENABLED) is True  # Schema default

    def test_config_file_not_modified_on_read_only_access(self):
        """Test that config files are not modified during read-only operations."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "test_config.yaml"

            # Create initial config
            original_config = {
                "test_component": {"frequency_hz": 800, "threshold": 0.75},
                "user_comment": "This is my custom configuration",
            }
            self.create_test_config_file(config_path, original_config)

            # Record original modification time
            original_mtime = config_path.stat().st_mtime

            # Load config and access values (read-only operations)
            cfg_mgr = AwesomeConfigManager(config_file=str(config_path))
            cfg_mgr.register_enum_config("test_component", TestSchemaV1)
            section = cfg_mgr.get_section("test_component")

            # Access multiple values
            _ = section.get_int(TestCfgKey.FREQUENCY)
            _ = section.get_double(TestCfgKey.THRESHOLD)
            _ = section.get_bool(TestCfgKey.ENABLED)

            # Verify file was not modified
            current_mtime = config_path.stat().st_mtime
            assert current_mtime == original_mtime, "Config file should not be modified during read-only access"

            # Verify content unchanged
            current_config = self.read_config_file(config_path)
            assert current_config == original_config, "Config file content should be unchanged"

    def test_multiple_schema_registrations_preserve_user_data(self):
        """Test that multiple schema registrations don't overwrite user data."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "test_config.yaml"

            # Create config with user data for multiple components
            multi_component_config = {
                "component_a": {"frequency_hz": 700, "enabled": False},
                "component_b": {"frequency_hz": 900, "threshold": 0.9},
            }
            self.create_test_config_file(config_path, multi_component_config)

            cfg_mgr = AwesomeConfigManager(config_file=str(config_path))

            # Register multiple schemas
            cfg_mgr.register_enum_config("component_a", TestSchemaV1)
            cfg_mgr.register_enum_config("component_b", TestSchemaV1)

            # Verify both components preserve user data
            section_a = cfg_mgr.get_section("component_a")
            section_b = cfg_mgr.get_section("component_b")

            assert section_a.get_int(TestCfgKey.FREQUENCY) == 700
            assert section_a.get_bool(TestCfgKey.ENABLED) is False

            assert section_b.get_int(TestCfgKey.FREQUENCY) == 900
            assert section_b.get_double(TestCfgKey.THRESHOLD) == 0.9

    def test_config_comments_and_formatting_preserved(self):
        """Test that YAML comments and formatting are preserved during config loading."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "test_config.yaml"

            # Create config with comments and formatting
            config_with_comments = """# User's custom configuration
test_component:
  frequency_hz: 800  # User's preferred frequency
  threshold: 0.75    # Optimized for my setup
  enabled: false     # Disabled for testing

# User's application settings
application:
  debug: true        # Enable debugging
  log_level: "DEBUG" # Verbose logging
"""
            config_path.write_text(config_with_comments, encoding="utf-8")

            # Load config
            cfg_mgr = AwesomeConfigManager(config_file=str(config_path))
            cfg_mgr.register_enum_config("test_component", TestSchemaV1)

            # Access config values (this loads the file)
            section = cfg_mgr.get_section("test_component")
            _ = section.get_int(TestCfgKey.FREQUENCY)

            # Read file content back
            current_content = config_path.read_text(encoding="utf-8")

            # Comments should still be present (basic check)
            assert "# User's custom configuration" in current_content
            assert "# User's preferred frequency" in current_content
            assert "# Enable debugging" in current_content

    def test_schema_evolution_backwards_compatibility(self):
        """Test that newer software versions work with older config files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "test_config.yaml"

            # Simulate old config file from v1 software
            old_config = {"test_component": {"frequency_hz": 1200, "threshold": 0.6, "enabled": True}}
            self.create_test_config_file(config_path, old_config)

            # Load with new v2 schema (simulating software upgrade)
            cfg_mgr = AwesomeConfigManager(config_file=str(config_path))
            cfg_mgr.register_enum_config("test_component", TestSchemaV2)

            section = cfg_mgr.get_section("test_component")

            # Old fields should work
            assert section.get_int(TestCfgKeyV2.FREQUENCY) == 1200
            assert section.get_double(TestCfgKeyV2.THRESHOLD) == 0.6
            assert section.get_bool(TestCfgKeyV2.ENABLED) is True

            # New fields should get defaults
            assert section.get_string(TestCfgKeyV2.NEW_FIELD) == "default_value"
            assert section.get_int(TestCfgKeyV2.BANDWIDTH) == 50

    def test_config_file_creation_preserves_existing_sections(self):
        """Test that config file creation doesn't overwrite existing user sections."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "test_config.yaml"

            # Create config with existing user data
            existing_config = {
                "my_custom_section": {"custom_setting": "user_value"},
                "application": {"debug": True, "custom_field": "user_data"},
            }
            self.create_test_config_file(config_path, existing_config)

            # Create new config manager (simulates first run with existing file)
            cfg_mgr = AwesomeConfigManager(config_file=str(config_path))

            # Verify existing sections are preserved
            raw_config = cfg_mgr._raw_config
            assert "my_custom_section" in raw_config
            assert raw_config["my_custom_section"]["custom_setting"] == "user_value"
            assert raw_config["application"]["custom_field"] == "user_data"

    def test_schema_field_removal_triggers_automatic_cleanup(self):
        """Test that removed schema fields trigger automatic cleanup of stale entries."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "test_config.yaml"

            # Create config with v2 schema (has all fields)
            v2_config = {
                "test_component": {
                    "frequency_hz": 800,
                    "threshold": 0.75,
                    "enabled": True,
                    "new_field": "user_value",  # This will be removed in v3
                    "bandwidth_hz": 100,  # This will also be removed
                }
            }
            self.create_test_config_file(config_path, v2_config)

            # Load with v1 schema (missing new_field and bandwidth_hz - simulating field removal)
            cfg_mgr = AwesomeConfigManager(config_file=str(config_path))
            cfg_mgr.register_enum_config("test_component", TestSchemaV1)  # v1 schema has fewer fields

            section = cfg_mgr.get_section("test_component")

            # Fields that still exist in v1 schema should work
            assert section.get_int(TestCfgKey.FREQUENCY) == 800
            assert section.get_double(TestCfgKey.THRESHOLD) == 0.75
            assert section.get_bool(TestCfgKey.ENABLED) is True

            # Read back the config file to check for automatic cleanup
            current_config = self.read_config_file(config_path)

            # NEW BEHAVIOR: Stale fields are automatically removed
            assert "new_field" not in current_config["test_component"], "Stale field should be automatically removed"
            assert "bandwidth_hz" not in current_config["test_component"], "Stale field should be automatically removed"

            # Valid fields should be preserved
            assert current_config["test_component"]["frequency_hz"] == 800
            assert current_config["test_component"]["threshold"] == 0.75
            assert current_config["test_component"]["enabled"] is True

    def test_schema_field_removal_with_profiles_removes_orphaned_entries(self):
        """Test that removed fields with profile overrides get their orphaned profile entries cleaned up."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "test_config.yaml"

            # Create config with profile overrides for fields that will be removed
            config_with_profiles = {
                "test_component": {
                    "frequency_hz": 600,
                    "threshold": 0.5,
                    "enabled": True,
                    # Fields that will be removed in schema downgrade
                    "new_field": "default_value",
                    "new_field_debug": "debug_override",  # Profile override for removed field
                    "new_field_production": "prod_override",  # Profile override for removed field
                    "bandwidth_hz": 50,
                    "bandwidth_hz_debug": 25,  # Profile override for removed field
                    "bandwidth_hz_production": 100,  # Profile override for removed field
                }
            }
            self.create_test_config_file(config_path, config_with_profiles)

            # Load with v1 schema (no new_field or bandwidth_hz)
            cfg_mgr = AwesomeConfigManager(config_file=str(config_path), profile="debug")
            cfg_mgr.register_enum_config("test_component", TestSchemaV1)

            # Fields that exist should work with profiles
            section = cfg_mgr.get_section("test_component")
            assert section.get_int(TestCfgKey.FREQUENCY) == 600

            # Read back config to check for orphaned profile entries cleanup
            current_config = self.read_config_file(config_path)

            # NEW BEHAVIOR: Orphaned profile entries are automatically removed
            assert "new_field_debug" not in current_config["test_component"], "Orphaned profile entry should be removed"
            assert "bandwidth_hz_production" not in current_config["test_component"], (
                "Orphaned profile entry should be removed"
            )

    def test_accessing_removed_field_after_cleanup_raises_error(self):
        """Test that accessing removed fields raises clear error messages after automatic cleanup."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "test_config.yaml"

            # Create config with field that will be "removed" by using older schema
            config_with_new_field = {
                "test_component": {
                    "frequency_hz": 800,
                    "new_field": "user_value",  # Present in config but not in v1 schema
                }
            }
            self.create_test_config_file(config_path, config_with_new_field)

            # Load with v1 schema (doesn't have new_field)
            cfg_mgr = AwesomeConfigManager(config_file=str(config_path))
            cfg_mgr.register_enum_config("test_component", TestSchemaV1)

            section = cfg_mgr.get_section("test_component")

            # NEW BEHAVIOR: Fields that are removed from schema are automatically cleaned up
            # Attempting to access them should raise an error since they're no longer in the config
            with pytest.raises(KeyError, match="not found"):
                section.get_string("new_field")  # Field was cleaned up when schema was registered

    def test_config_file_auto_cleanup_prevents_stale_accumulation(self):
        """Test that automatic cleanup prevents config files from accumulating stale entries."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "test_config.yaml"

            # Start with minimal config
            initial_config = {"test_component": {"frequency_hz": 600, "threshold": 0.5}}
            self.create_test_config_file(config_path, initial_config)

            # Simulate v1 -> v2 upgrade: Add fields
            cfg_mgr_v2 = AwesomeConfigManager(config_file=str(config_path))
            cfg_mgr_v2.register_enum_config("test_component", TestSchemaV2)
            section_v2 = cfg_mgr_v2.get_section("test_component")

            # Access new fields to populate them with defaults
            _ = section_v2.get_string(TestCfgKeyV2.NEW_FIELD)
            _ = section_v2.get_int(TestCfgKeyV2.BANDWIDTH)

            # Manually update config to simulate user adding new fields
            current_config = self.read_config_file(config_path)
            current_config["test_component"]["new_field"] = "user_added_value"
            current_config["test_component"]["bandwidth_hz"] = 75
            current_config["test_component"]["temporary_field"] = "will_be_orphaned"
            self.create_test_config_file(config_path, current_config)

            # Simulate v2 -> v1 downgrade: Remove fields by using older schema
            cfg_mgr_v1 = AwesomeConfigManager(config_file=str(config_path))
            cfg_mgr_v1.register_enum_config("test_component", TestSchemaV1)

            # Read final config state
            final_config = self.read_config_file(config_path)

            # NEW BEHAVIOR: Stale entries are automatically cleaned up
            test_section = final_config["test_component"]
            assert "new_field" not in test_section, "v2 field should be automatically cleaned"
            assert "bandwidth_hz" not in test_section, "v2 field should be automatically cleaned"
            assert "temporary_field" not in test_section, "User-added field should be automatically cleaned"

            # Valid fields should remain accessible
            section_v1 = cfg_mgr_v1.get_section("test_component")
            assert section_v1.get_int(TestCfgKey.FREQUENCY) == 600
            assert section_v1.get_double(TestCfgKey.THRESHOLD) == 0.5
