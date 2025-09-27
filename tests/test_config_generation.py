"""
Unit tests for config generation and formatting functionality.

Tests the new schema-driven config generation system including:
- Field comment formatting from schema metadata
- YAML value formatting with proper quoting
- Complete config file generation with rich comments
- Helper functions for string choice fields
"""

import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import pytest
import yaml

from util.config import AwesomeConfigManager, CfgField, CfgType
from util.config.types import string_choices_field


class TestMode(Enum):
    """Test enum for config testing."""

    AUTO = "AUTO"
    MANUAL = "MANUAL"
    ADAPTIVE = "ADAPTIVE"


@dataclass
class TestSchema:
    """Test schema for config generation testing."""

    # String field with choices
    log_level = string_choices_field(
        choices=["DEBUG", "INFO", "WARN", "ERROR"],
        default="INFO",
        description_prefix="Component log level override"
    )

    # Basic types with constraints
    frequency_hz = CfgField(
        type=CfgType.INT,
        default=600,
        min=200,
        max=2000,
        unit="Hz",
        description="Target frequency for processing"
    )

    threshold_norm = CfgField(
        type=CfgType.DOUBLE,
        default=0.25,
        min=0.0,
        max=1.0,
        unit="norm",
        description="Detection threshold"
    )

    enabled = CfgField(
        type=CfgType.BOOL,
        default=True,
        description="Enable this component"
    )

    # Enum field
    mode = CfgField(
        type=CfgType.ENUM,
        default=TestMode.AUTO,
        choices=list(TestMode),
        description="Processing mode selection"
    )

    # String with nullable
    output_file = CfgField(
        type=CfgType.STRING,
        default=None,
        nullable=True,
        description="Output file path"
    )


class TestStringChoicesField:
    """Test the string_choices_field helper function."""

    def test_basic_creation(self):
        """Test basic string choices field creation."""
        field = string_choices_field(
            choices=["A", "B", "C"],
            default="B",
            description_prefix="Test field"
        )

        assert field.type == CfgType.STRING
        assert field.default == "B"
        assert field.choices == ["A", "B", "C"]
        assert field.description == "Test field"

    def test_log_level_field(self):
        """Test typical log level field creation."""
        field = string_choices_field(
            choices=["DEBUG", "INFO", "WARN", "ERROR"],
            default="INFO",
            description_prefix="Override app log level if more verbose"
        )

        assert field.type == CfgType.STRING
        assert field.default == "INFO"
        assert field.choices == ["DEBUG", "INFO", "WARN", "ERROR"]
        assert "Override app log level if more verbose" in field.description


class TestFieldCommentFormatting:
    """Test the _format_field_comment method."""

    def setup_method(self):
        """Set up test config manager."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("test:\n  dummy: value\n")
            self.config_file = f.name

        self.cfg_mgr = AwesomeConfigManager(self.config_file)

    def teardown_method(self):
        """Clean up test files."""
        Path(self.config_file).unlink(missing_ok=True)

    def test_basic_field_comment(self):
        """Test basic field comment generation."""
        field = CfgField(
            type=CfgType.INT,
            default=42,
            description="Test integer field"
        )

        comment = self.cfg_mgr._format_field_comment(field, "test_field")

        assert "Test integer field" in comment
        assert "INT" in comment
        assert "default: 42" in comment

    def test_field_with_constraints(self):
        """Test field comment with min/max constraints."""
        field = CfgField(
            type=CfgType.DOUBLE,
            default=0.5,
            min=0.0,
            max=1.0,
            unit="norm",
            description="Normalized value"
        )

        comment = self.cfg_mgr._format_field_comment(field, "threshold")

        assert "Normalized value" in comment
        assert "DOUBLE" in comment
        assert "0.0-1.0 norm" in comment
        assert "default: 0.5" in comment

    def test_field_with_choices(self):
        """Test field comment with choices."""
        field = CfgField(
            type=CfgType.STRING,
            default="INFO",
            choices=["DEBUG", "INFO", "WARN", "ERROR"],
            description="Log level"
        )

        comment = self.cfg_mgr._format_field_comment(field, "log_level")

        assert "Log level" in comment
        assert "STRING" in comment
        assert "{DEBUG,INFO,WARN,ERROR}" in comment
        assert 'default: "INFO"' in comment

    def test_field_with_enum_default(self):
        """Test field comment with enum default value."""
        field = CfgField(
            type=CfgType.ENUM,
            default=TestMode.AUTO,
            choices=list(TestMode),
            description="Processing mode"
        )

        comment = self.cfg_mgr._format_field_comment(field, "mode")

        assert "Processing mode" in comment
        assert "ENUM" in comment
        assert "default: AUTO" in comment

    def test_field_with_null_default(self):
        """Test field comment with null default."""
        field = CfgField(
            type=CfgType.STRING,
            default=None,
            nullable=True,
            description="Optional file path"
        )

        comment = self.cfg_mgr._format_field_comment(field, "output_file")

        assert "Optional file path" in comment
        assert "default: null" in comment


class TestYamlValueFormatting:
    """Test the _format_yaml_value method."""

    def setup_method(self):
        """Set up test config manager."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("test:\n  dummy: value\n")
            self.config_file = f.name

        self.cfg_mgr = AwesomeConfigManager(self.config_file)

    def teardown_method(self):
        """Clean up test files."""
        Path(self.config_file).unlink(missing_ok=True)

    def test_boolean_formatting(self):
        """Test boolean value formatting."""
        assert self.cfg_mgr._format_yaml_value(True) == "true"
        assert self.cfg_mgr._format_yaml_value(False) == "false"

    def test_null_formatting(self):
        """Test null value formatting."""
        assert self.cfg_mgr._format_yaml_value(None) == "null"

    def test_string_formatting(self):
        """Test string value formatting with proper quoting."""
        # Normal strings
        assert self.cfg_mgr._format_yaml_value("hello") == "hello"
        assert self.cfg_mgr._format_yaml_value("test_value") == "test_value"

        # Strings that need quoting
        assert self.cfg_mgr._format_yaml_value("true") == '"true"'
        assert self.cfg_mgr._format_yaml_value("false") == '"false"'
        assert self.cfg_mgr._format_yaml_value("null") == '"null"'
        assert self.cfg_mgr._format_yaml_value("123") == '"123"'

    def test_enum_formatting(self):
        """Test enum value formatting."""
        formatted = self.cfg_mgr._format_yaml_value(TestMode.AUTO)
        assert formatted == '"AUTO"'

    def test_numeric_formatting(self):
        """Test numeric value formatting."""
        assert self.cfg_mgr._format_yaml_value(42) == "42"
        assert self.cfg_mgr._format_yaml_value(3.14) == "3.14"


class TestSchemaBasedConfigGeneration:
    """Test complete schema-driven config generation."""

    def setup_method(self):
        """Set up test config manager with temp file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("# Initial config\n")
            self.config_file = f.name

        self.cfg_mgr = AwesomeConfigManager(self.config_file)

    def teardown_method(self):
        """Clean up test files."""
        Path(self.config_file).unlink(missing_ok=True)
        # Clean up any backup files
        for backup in Path(self.config_file).parent.glob(f"{Path(self.config_file).name}.backup-*"):
            backup.unlink(missing_ok=True)

    def test_update_config_file_from_schemas(self):
        """Test complete config file generation from schemas."""
        # Register a test schema
        self.cfg_mgr.register_enum_config("test_section", TestSchema)

        # Update config file
        self.cfg_mgr.update_config_file_from_schemas()

        # Verify the generated config
        with open(self.config_file, 'r') as f:
            content = f.read()

        # Check header
        assert "Morse Code Decoder Configuration" in content
        assert "Generated:" in content

        # Check section exists
        assert "test_section:" in content

        # Check all fields present
        assert "log_level:" in content
        assert "frequency_hz:" in content
        assert "threshold_norm:" in content
        assert "enabled:" in content
        assert "mode:" in content
        assert "output_file:" in content

        # Check inline comments present
        assert "# Component log level override" in content
        assert "# Target frequency for processing" in content
        assert "# Detection threshold" in content

        # Check proper value formatting
        assert "log_level: INFO" in content
        assert "frequency_hz: 600" in content
        assert "threshold_norm: 0.25" in content
        assert "enabled: true" in content
        assert "mode: AUTO" in content
        assert "output_file: null" in content

    def test_create_sample_config(self):
        """Test sample config generation."""
        # Register test schema
        self.cfg_mgr.register_enum_config("sample_section", TestSchema)

        # Create sample config in temp file
        sample_file = self.config_file + ".sample"
        self.cfg_mgr.create_sample_config(sample_file)

        try:
            # Verify sample config
            with open(sample_file, 'r') as f:
                content = f.read()

            # Check basic structure
            assert "sample_section:" in content
            assert "log_level: INFO" in content
            assert "frequency_hz: 600" in content

            # Check it's valid YAML
            parsed = yaml.safe_load(content)
            assert "sample_section" in parsed
            assert parsed["sample_section"]["log_level"] == "INFO"
            assert parsed["sample_section"]["frequency_hz"] == 600

        finally:
            Path(sample_file).unlink(missing_ok=True)

    def test_config_preservation_during_update(self):
        """Test that user customizations are preserved during config updates."""
        # Create initial config with user customizations
        initial_config = {
            "test_section": {
                "log_level": "DEBUG",  # User changed from INFO to DEBUG
                "frequency_hz": 800,   # User changed from 600 to 800
                "enabled": False       # User changed from True to False
            }
        }

        with open(self.config_file, 'w') as f:
            yaml.dump(initial_config, f)

        # Create a fresh config manager to properly load the user config
        cfg_mgr = AwesomeConfigManager(self.config_file)

        # Register schema and update
        cfg_mgr.register_enum_config("test_section", TestSchema)
        cfg_mgr.update_config_file_from_schemas()

        # Verify user values preserved
        with open(self.config_file, 'r') as f:
            content = f.read()

        assert "log_level: DEBUG" in content  # User value preserved
        assert "frequency_hz: 800" in content  # User value preserved
        assert "enabled: false" in content     # User value preserved

        # But new fields get defaults
        assert "threshold_norm: 0.25" in content  # New field gets default

    def test_backup_creation(self):
        """Test that backups are created during updates."""
        # Write initial content
        with open(self.config_file, 'w') as f:
            f.write("initial_content: true\n")

        # Register schema and update
        self.cfg_mgr.register_enum_config("test_section", TestSchema)
        self.cfg_mgr.update_config_file_from_schemas()

        # Check backup was created
        backup_files = list(Path(self.config_file).parent.glob(f"{Path(self.config_file).name}.backup-*"))
        assert len(backup_files) == 1

        # Verify backup contains original content
        with open(backup_files[0], 'r') as f:
            backup_content = f.read()
        assert "initial_content: true" in backup_content


class TestConfigGenerationIntegration:
    """Integration tests for the complete config generation system."""

    def test_real_component_schemas(self):
        """Test with actual component schemas from the codebase."""
        from morsecode.components.graphics.schema import GraphicsSchema
        from morsecode.components.decoder.schema import ConfigSchema as DecoderSchema

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("# Test config\n")
            config_file = f.name

        try:
            cfg_mgr = AwesomeConfigManager(config_file)

            # Register real schemas
            cfg_mgr.register_enum_config("graphics", GraphicsSchema)
            cfg_mgr.register_enum_config("decoder", DecoderSchema)

            # Generate config
            cfg_mgr.update_config_file_from_schemas()

            # Verify config loads and is valid
            with open(config_file, 'r') as f:
                content = f.read()

            # Check both sections present
            assert "graphics:" in content
            assert "decoder:" in content

            # Check log_level fields present (our new addition)
            graphics_log_count = content.count("log_level:")
            assert graphics_log_count >= 2  # At least graphics and decoder

            # Verify it's valid YAML
            parsed = yaml.safe_load(content)
            assert "graphics" in parsed
            assert "decoder" in parsed
            assert "log_level" in parsed["graphics"]
            assert "log_level" in parsed["decoder"]

        finally:
            Path(config_file).unlink(missing_ok=True)
            # Clean up any backups
            for backup in Path(config_file).parent.glob(f"{Path(config_file).name}.backup-*"):
                backup.unlink(missing_ok=True)