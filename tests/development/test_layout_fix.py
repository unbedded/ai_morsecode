#!/usr/bin/env python3
"""Test that the layout error is fixed."""

import sys

sys.path.insert(0, "src")

from morsecode.components.graphics.graphics_display import GraphicsDisplay
from util.config import AwesomeConfigManager


def test_layout_fix():
    """Test that the display layout builds without errors."""
    print("🧪 Testing Layout Fix")
    print("=" * 30)

    cfg_mgr = AwesomeConfigManager()
    overrides = {"display_width_chars": 80, "display_height_chars": 25, "enable_debug_logging": False}

    try:
        debug_display = GraphicsDisplay(cfg_mgr, overrides)

        # Try to build the layout
        layout = debug_display._build_display_layout()

        if layout is not None:
            print("✅ SUCCESS: Layout built without errors")
            print(f"   Layout type: {type(layout)}")

            # Check if it's using fallback mode
            header_content = str(layout["header"].renderable.renderable)
            if "Fallback Mode" in header_content:
                print("❌ Still using fallback mode")
                return False
            else:
                print("✅ Using normal layout mode")
                return True
        else:
            print("❌ Layout returned None")
            return False

    except Exception as e:
        print(f"❌ Layout error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_layout_fix()
    if success:
        print("\n🎉 Layout error fixed!")
    else:
        print("\n⚠️ Layout still has issues")
