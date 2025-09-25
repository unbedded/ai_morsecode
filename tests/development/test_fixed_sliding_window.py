#!/usr/bin/env python3
"""Test the fixed sliding window fix."""

import sys
import time

sys.path.insert(0, "src")

from morsecode.components.graphics.graphics_display import GraphicsDisplay
from util.config import AwesomeConfigManager


def test_fixed_sliding_window():
    """Test that fixed sliding window eliminates shrinking waveform bug."""
    print("🧪 Testing Fixed Sliding Window Solution")
    print("=" * 60)

    # Create graphics display
    cfg_mgr = AwesomeConfigManager()
    overrides = {
        "enabled": True,
        "backend": "ascii",
        "width": 40,
        "height": 3,
        "update_rate_hz": 10.0,
        "buffer_size": 1000,  # This is now ignored - we use fixed window
    }

    gd = GraphicsDisplay(cfg_mgr, overrides)
    print(f"✅ Fixed window size: {gd._fixed_window_size} samples")
    print(f"✅ Buffer starts pre-filled: {len(gd._signal_buffer)} samples")
    print(f"✅ Initial maxlen: {gd._signal_buffer.maxlen}")
    print()

    # Test that it starts with zeros for immediate full-width display
    initial_data = list(gd._signal_buffer)
    all_zeros = all(x == 0.0 for x in initial_data)
    print(f"✅ Pre-filled with zeros: {all_zeros}")
    print()

    # Simulate probability data and check for consistent behavior
    print("📊 Adding probability data to sliding window...")
    current_time = 0.0

    for i in range(75):  # More than window size to test sliding behavior
        # Add varying probability data
        prob_value = 0.3 + 0.4 * ((i % 10) / 10.0)  # 0.3 to 0.7 range
        gd.add_signal_data(prob_value, confidence=0.8, timing=current_time)

        if i in [0, 10, 25, 49, 50, 74]:  # Key checkpoints
            print(
                f"  Sample {i + 1:2d}: prob={prob_value:.2f}, "
                f"buffer_len={len(gd._signal_buffer):2d}, "
                f"maxlen={gd._signal_buffer.maxlen:2d}, "
                f"rate={gd._calculated_sample_rate_hz:.1f}Hz"
            )

            if i == 49:
                print("    └─ At window size limit")
            elif i == 50:
                print("    └─ Sliding window starts here - oldest data removed")

        current_time += 0.5  # 500ms intervals = 2 Hz
        time.sleep(0.001)  # Tiny delay

    print()
    print("📈 Final Statistics:")
    print(f"   • Window size: {gd._signal_buffer.maxlen} samples (FIXED)")
    print(f"   • Buffer length: {len(gd._signal_buffer)} samples (should equal maxlen)")
    print(f"   • Calculated sample rate: {gd._calculated_sample_rate_hz:.2f} Hz")
    print(f"   • Time span: {len(gd._signal_buffer) / gd._calculated_sample_rate_hz:.1f} seconds")

    # Test the sliding window behavior
    buffer_data = list(gd._signal_buffer)
    timing_data = list(gd._timing_buffer)

    print()
    print("🔍 Sliding Window Validation:")
    print(f"   • Buffer always full: {len(buffer_data) == gd._fixed_window_size}")
    print(f"   • Oldest timing: {timing_data[0]:.1f}s")
    print(f"   • Newest timing: {timing_data[-1]:.1f}s")
    print(f"   • Time span: {timing_data[-1] - timing_data[0]:.1f}s")

    # Check for no more shrinking waveform effect
    expected_time_span = gd._fixed_window_size / gd._calculated_sample_rate_hz
    actual_time_span = timing_data[-1] - timing_data[0]

    print()
    print("🎯 Shrinking Waveform Check:")
    print(f"   • Expected time span: {expected_time_span:.1f}s")
    print(f"   • Actual time span: {actual_time_span:.1f}s")

    span_matches = abs(expected_time_span - actual_time_span) < 2.0
    always_full = len(buffer_data) == gd._fixed_window_size

    if span_matches and always_full:
        print("✅ SUCCESS: Fixed sliding window works perfectly!")
        print("   • No more shrinking waveform effect")
        print("   • Consistent time span regardless of accumulated data")
        print("   • Immediate full-width display at startup")
        print("   • Automatic sliding window behavior")
    else:
        print("❌ Issues detected:")
        if not span_matches:
            print(f"   • Time span mismatch: {actual_time_span:.1f}s vs {expected_time_span:.1f}s")
        if not always_full:
            print(f"   • Buffer not full: {len(buffer_data)}/{gd._fixed_window_size}")

    print()
    print("🔍 Recent Buffer Contents (last 5 values):")
    for i in range(-5, 0):
        print(f"   [{i}] signal={buffer_data[i]:.3f}, timing={timing_data[i]:.1f}s")


if __name__ == "__main__":
    test_fixed_sliding_window()
