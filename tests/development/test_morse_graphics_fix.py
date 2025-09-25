#!/usr/bin/env python3
"""Test morse code graphics with fixed decimation."""

import sys

sys.path.insert(0, "src")

from morsecode.components.graphics.graphics_display import GraphicsDisplay
from util.config import AwesomeConfigManager


def test_graphics_with_simple_signal():
    """Test graphics display with our fixed decimation on simple signal."""
    print("🧪 Testing Morse Code Graphics with Fixed Decimation")
    print("=" * 60)

    # Create config manager with graphics enabled
    cfg_mgr = AwesomeConfigManager()

    # Create graphics display with overrides instead of separate config
    overrides = {
        "enabled": True,
        "backend": "ascii",  # Use ASCII backend to test our fix
        "width": 60,
        "height": 4,
        "update_rate_hz": 30.0,
        "buffer_size": 500,
    }
    gd = GraphicsDisplay(cfg_mgr, overrides)
    print(f"Graphics display created: enabled={gd.enabled}, backend={gd.backend_type}")

    # Test with 50% duty cycle square wave (same as our demo)
    print("\n📊 Testing with 50% duty cycle square wave...")

    # Generate test signal: 1 Hz square wave, 50% duty cycle
    test_signal = []
    # 100 samples = 1 cycle at 100 Hz "sample rate"
    for _ in range(4):  # 4 cycles = 4 seconds
        # High for 0.5 seconds (50 samples)
        test_signal.extend([1.0] * 50)
        # Low for 0.5 seconds (50 samples)
        test_signal.extend([-1.0] * 50)

    print(f"Generated signal: {len(test_signal)} samples, 4 cycles")

    # Add data points to graphics display
    for i, value in enumerate(test_signal):
        confidence = 0.8 + 0.2 * (value > 0)  # Higher confidence for high values
        timing = i / 100.0  # 100 Hz sample rate
        gd.add_signal_data(value, confidence, timing)

        # Print progress
        if i % 50 == 0:
            print(f"  Added {i + 1}/{len(test_signal)} samples...")

    print("\n✅ Test completed!")
    print("If the decimation fix worked, the display should show clean square wave patterns.")
    print("Check the terminal output above for the visualization.")


if __name__ == "__main__":
    test_graphics_with_simple_signal()
