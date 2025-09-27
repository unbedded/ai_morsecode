"""
Integration tests for config system with morsecode components.

Tests the config system integration with actual morsecode component schemas.
"""

import tempfile
from pathlib import Path
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
            cfg_mgr.register_enum_config("graphics", GraphicsSchema)
            cfg_mgr.register_enum_config("decoder", DecoderSchema)
            cfg_mgr.update_config_file_from_schemas()

            with open(config_file, 'r') as f:
                content = f.read()

            assert "graphics:" in content
            assert "decoder:" in content
            assert content.count("log_level:") >= 2

            parsed = yaml.safe_load(content)
            assert "log_level" in parsed["graphics"]
            assert "log_level" in parsed["decoder"]

        finally:
            Path(config_file).unlink(missing_ok=True)
            for backup in Path(config_file).parent.glob(f"{Path(config_file).name}.backup-*"):
                backup.unlink(missing_ok=True)
