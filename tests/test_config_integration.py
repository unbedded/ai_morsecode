"""
Integration tests for config system with morsecode components.

Tests the config system integration with actual morsecode component schemas.
These tests verify that the util.config system works correctly with real
morsecode components and their specific configuration requirements.
"""

import tempfile
from pathlib import Path

import pytest
import yaml

from util.config import AwesomeConfigManager


class TestConfigMorseCodeIntegration:
    """Integration tests for config system with morsecode components."""

    def test_real_component_schemas(self):
        """Test config generation with actual morsecode component schemas."""
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

    def test_all_morsecode_components_have_log_level(self):
        """Test that all morsecode components include log_level configuration."""
        from morsecode.components.graphics.schema import GraphicsSchema
        from morsecode.components.decoder.schema import ConfigSchema as DecoderSchema
        from morsecode.components.audio.schema import ConfigSchema as AudioSchema
        from morsecode.components.signal.signal_config_schema import SignalConfigSchema

        # Verify each component schema has log_level field
        schemas = [
            ("graphics", GraphicsSchema),
            ("decoder", DecoderSchema),
            ("audio", AudioSchema),
            ("signal", SignalConfigSchema)
        ]

        for name, schema in schemas:
            # Check the schema has log_level attribute
            assert hasattr(schema, 'log_level'), f"{name} schema missing log_level field"

            # Check it's a proper config field
            log_level_field = getattr(schema, 'log_level')
            assert hasattr(log_level_field, 'default'), f"{name} log_level not a proper CfgField"
            assert hasattr(log_level_field, 'choices'), f"{name} log_level missing choices"

            # Check it has expected log level choices
            choices = log_level_field.choices
            assert "DEBUG" in choices, f"{name} log_level missing DEBUG choice"
            assert "INFO" in choices, f"{name} log_level missing INFO choice"
            assert log_level_field.default == "INFO", f"{name} log_level default should be INFO"

    def test_component_level_logging_integration(self):
        """Test that component-level log configuration works with logging system."""
        from morsecode.components.graphics.schema import GraphicsSchema

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            # Create config with DEBUG log level for graphics
            config_data = {
                "graphics": {
                    "mode": "disabled",
                    "log_level": "DEBUG"
                }
            }
            yaml.dump(config_data, f)
            config_file = f.name

        try:
            cfg_mgr = AwesomeConfigManager(config_file)
            cfg_mgr.register_enum_config("graphics", GraphicsSchema)

            # Get graphics config section
            graphics_section = cfg_mgr.get_section("graphics")

            # Verify log_level is accessible and set correctly
            assert graphics_section.get_string("log_level") == "DEBUG"

            # Test that we can override log levels per component
            assert graphics_section.get_string("mode") == "disabled"

        finally:
            Path(config_file).unlink(missing_ok=True)