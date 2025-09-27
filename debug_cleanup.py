#!/usr/bin/env python3
"""Isolated test to debug auto-cleanup issue with graphics configuration."""

import os
import tempfile
from dataclasses import dataclass
from enum import Enum

from util.config import AwesomeConfigManager
from util.config.types import CfgField, CfgType


# Minimal test schema matching graphics structure
class TestGraphicsKey(Enum):
    """Test configuration keys."""

    ENABLED = "enabled"
    BACKEND = "backend"
    DISPLAY_WIDTH_CHARS = "display_width_chars"
    DISPLAY_HEIGHT_CHARS = "display_height_chars"


@dataclass
class TestGraphicsSchema:
    """Test configuration schema."""

    enabled = CfgField(type=CfgType.BOOL, default=True, description="Enable graphics")
    backend = CfgField(type=CfgType.STRING, default="ascii", description="Graphics backend")
    display_width_chars = CfgField(type=CfgType.INT, default=0, description="Display width")
    display_height_chars = CfgField(type=CfgType.INT, default=20, description="Display height")


def test_auto_cleanup_issue():
    """Test auto-cleanup behavior in isolation."""
    # Create temporary config file with graphics settings
    test_config = """
graphics:
  enabled: true
  backend: "ascii"
  display_width_chars: 80
  display_height_chars: 25
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(test_config.strip())
        config_file = f.name

    try:
        print("🧪 Testing auto-cleanup behavior...")
        print(f"📁 Using temp config: {config_file}")

        # Create config manager with the test file
        cfg_mgr = AwesomeConfigManager(config_file=config_file)

        print("\n1️⃣ BEFORE schema registration:")
        with open(config_file) as f:
            content = f.read()
            print(content)

        print("\n2️⃣ Registering graphics schema...")
        # Let's trace what happens during registration
        print("Schema fields being registered:")
        schema = TestGraphicsSchema()

        # Check if it's a dataclass
        if hasattr(schema, "__dataclass_fields__"):
            print("✅ Detected as dataclass")
            valid_fields = set(schema.__dataclass_fields__.keys())
            print(f"   Valid fields from __dataclass_fields__: {valid_fields}")
        else:
            print("❌ NOT detected as dataclass")

        # Manual inspection
        print("Manual field inspection:")
        for field_name in dir(schema):
            if not field_name.startswith("_"):
                field_obj = getattr(schema, field_name)
                if hasattr(field_obj, "type"):
                    print(f"   {field_name}: has .type attribute")

        cfg_mgr.register_enum_config("graphics", TestGraphicsSchema)

        print("\n3️⃣ AFTER schema registration:")
        with open(config_file) as f:
            content = f.read()
            print(content)

        print("\n4️⃣ Getting graphics section...")
        graphics_section = cfg_mgr.get_section("graphics")

        print("\n5️⃣ Reading values from section:")
        print(f"   enabled: {graphics_section.get_bool(TestGraphicsKey.ENABLED)}")
        print(f"   backend: {graphics_section.get_string(TestGraphicsKey.BACKEND)}")
        print(f"   width: {graphics_section.get_int(TestGraphicsKey.DISPLAY_WIDTH_CHARS)}")
        print(f"   height: {graphics_section.get_int(TestGraphicsKey.DISPLAY_HEIGHT_CHARS)}")

        print("\n6️⃣ FINAL config file state:")
        with open(config_file) as f:
            content = f.read()
            print(content)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Cleanup temp file
        os.unlink(config_file)


def test_schema_field_detection():
    """Test if schema fields are being detected correctly."""
    print("\n🔍 Testing schema field detection...")

    schema = TestGraphicsSchema()
    print("Schema fields:")
    for field_name in dir(schema):
        if not field_name.startswith("_"):
            field_obj = getattr(schema, field_name)
            if hasattr(field_obj, "type"):
                print(f"   {field_name}: {field_obj.type} (default: {field_obj.default})")


if __name__ == "__main__":
    test_schema_field_detection()
    test_auto_cleanup_issue()
