#!/usr/bin/env python3
"""Test morse code graphics with detailed frame-by-frame output."""

import sys

sys.path.insert(0, "src")

import time

from morsecode.components.graphics.pattern_display import PatternDisplay
from util.config import AwesomeConfigManager


def test_graphics_detailed():
    """Test graphics display with detailed output showing decimation effects."""
    print("🧪 Detailed Morse Code Graphics Test")
    print("=" * 60)

    # Create graphics display
    cfg_mgr = AwesomeConfigManager()
    overrides = {
        "enabled": True,
        "backend": "ascii",
        "width": 40,  # Smaller for clearer output
        "height": 3,
        "update_rate_hz": 5.0,  # Slower updates to see changes
        "buffer_size": 200,
    }
    gd = PatternDisplay(cfg_mgr, overrides)

    # Disable automatic screen clearing for this test
    gd._update_display = create_frame_by_frame_display(gd)

    print(f"Graphics: enabled={gd.enabled}, backend={gd.backend_type}")
    print(f"Size: {gd.width}x{gd.height}, update rate: {gd.update_rate_hz} Hz")
    print()

    # Test 1: Build up a 50% duty cycle square wave gradually
    print("📊 Test 1: Building 50% duty cycle square wave gradually")
    print("─" * 60)

    # Generate square wave: 20 samples high, 20 samples low
    for cycle in range(3):  # 3 cycles
        print(f"\n🔄 Cycle {cycle + 1}:")

        # High phase (1.0)
        for _ in range(20):
            gd.add_signal_data(1.0, 0.9, time.time())
            time.sleep(0.01)  # Small delay to see progression

        # Low phase (-1.0)
        for _ in range(20):
            gd.add_signal_data(-1.0, 0.9, time.time())
            time.sleep(0.01)

    print("\n" + "=" * 60)
    print("✅ Test completed!")
    print("The graphs above should show our fixed decimation producing clean square waves.")


def create_frame_by_frame_display(gd):
    """Create a custom display function that shows frames without clearing."""
    frame_count = [0]  # Use list for closure

    def frame_by_frame_display():
        if not gd.enabled or not gd._signal_buffer:
            return

        signal_data = list(gd._signal_buffer)
        frame_count[0] += 1

        try:
            if gd._backend:
                # Use direct backend
                gd._backend.clear()
                gd._backend.plot(signal_data, sample_rate_hz=gd.update_rate_hz)
                lines = gd._backend.render_sparkline()
            else:
                return

            # Display frame with header
            print(f"\n📸 Frame {frame_count[0]} - Buffer: {len(signal_data)} samples")
            print("─" * gd.width)
            for line in lines:
                print(line)

        except Exception as e:
            print(f"Display error: {e}")

    return frame_by_frame_display


if __name__ == "__main__":
    test_graphics_detailed()
