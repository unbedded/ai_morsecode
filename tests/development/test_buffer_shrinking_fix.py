#!/usr/bin/env python3
"""Test that the buffer shrinking fix works correctly."""

import sys
import time

sys.path.insert(0, "src")

from morsecode.components.graphics.graphics_display import GraphicsDisplay
from util.config import AwesomeConfigManager


def test_buffer_adjustment():
    """Test that buffer size adjusts correctly for different sample rates."""
    print("🧪 Testing Buffer Size Adjustment Fix")
    print("=" * 60)

    # Create graphics display
    cfg_mgr = AwesomeConfigManager()
    overrides = {
        "enabled": True,
        "backend": "ascii",
        "width": 40,
        "height": 3,
        "update_rate_hz": 10.0,
        "buffer_size": 1000,  # Default large buffer
    }

    gd = GraphicsDisplay(cfg_mgr, overrides)
    print(f"Initial buffer maxlen: {gd._signal_buffer.maxlen}")
    print()

    # Simulate 2 Hz probability data (500ms intervals)
    print("📊 Simulating 2 Hz probability data (like convolution decoder)...")
    current_time = 0.0

    for i in range(25):  # 25 events × 0.5s = 12.5 seconds
        # Add probability data point
        prob_value = 0.5 + 0.3 * (i % 3 - 1)  # Varying probability values
        gd.add_signal_data(prob_value, confidence=0.8, timing=current_time)

        print(
            f"  Event {i + 1:2d}: t={current_time:5.1f}s, prob={prob_value:.2f}, "
            f"buffer_len={len(gd._signal_buffer):3d}, "
            f"maxlen={gd._signal_buffer.maxlen:3d}, "
            f"rate={gd._calculated_sample_rate_hz:.1f}Hz"
        )

        current_time += 0.5  # 500ms intervals = 2 Hz
        time.sleep(0.01)  # Small delay for demonstration

        # Check for buffer adjustments
        if i == 5:  # After a few samples, rate should stabilize
            print(f"    └─ After 5 samples: Calculated rate = {gd._calculated_sample_rate_hz:.1f} Hz")

    print()
    print("📈 Final Statistics:")
    print(f"   • Calculated sample rate: {gd._calculated_sample_rate_hz:.2f} Hz")
    print(f"   • Final buffer size: {gd._signal_buffer.maxlen} samples")
    print(f"   • Data time span: {len(gd._signal_buffer) / gd._calculated_sample_rate_hz:.1f} seconds")
    print(f"   • Buffer utilization: {len(gd._signal_buffer)}/{gd._signal_buffer.maxlen} samples")

    # Expected results
    expected_rate = 2.0
    expected_buffer_size = int(2.0 * 15.0)  # 2 Hz × 15 sec window = 30 samples

    print()
    print("🎯 Expected vs Actual:")
    print(f"   • Rate: {expected_rate} Hz vs {gd._calculated_sample_rate_hz:.1f} Hz")
    print(f"   • Buffer size: ~{expected_buffer_size} vs {gd._signal_buffer.maxlen}")

    # Validation
    rate_ok = abs(gd._calculated_sample_rate_hz - expected_rate) < 0.5
    buffer_reasonable = 20 <= gd._signal_buffer.maxlen <= 50  # Should be around 30

    if rate_ok and buffer_reasonable:
        print("✅ SUCCESS: Buffer automatically adjusted for 2 Hz data rate!")
        print("   • No more 'shrinking waveform' effect")
        print("   • Buffer maintains reasonable time window")
        print("   • Automatic adjustment prevents infinite accumulation")
    else:
        print("❌ Issues detected:")
        if not rate_ok:
            print(f"   • Rate calculation off: {gd._calculated_sample_rate_hz:.1f} Hz (expected ~2 Hz)")
        if not buffer_reasonable:
            print(f"   • Buffer size not adjusted: {gd._signal_buffer.maxlen} (expected ~30)")

    print()
    print("🔍 Buffer Contents (last 10 values):")
    recent_signals = list(gd._signal_buffer)[-10:]
    recent_timings = list(gd._timing_buffer)[-10:]

    for i, (sig, timing) in enumerate(zip(recent_signals, recent_timings, strict=False)):
        print(f"   [{len(recent_signals) - 10 + i:2d}] signal={sig:.2f}, timing={timing:.1f}s")


if __name__ == "__main__":
    test_buffer_adjustment()
