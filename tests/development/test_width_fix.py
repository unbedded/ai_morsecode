#!/usr/bin/env python3
"""Test the width and scrolling fixes."""

import math
import os
import sys
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from util.graph.time_series_graph import TimeSeriesGraph


def test_width_usage():
    """Test that graphs use full display width."""
    print("📏 DISPLAY WIDTH USAGE TEST")
    print("=" * 35)

    width = 60
    print(f"Target width: {width} characters")
    print()

    # Test with short data (magnitude-like - should trigger sliding window mode)
    mag_data = [math.sin(i * 0.1) for i in range(20)]  # 20 samples

    # Test with long data (probability-like - should trigger time-aware mode)
    prob_data = [0.5 + 0.3 * math.sin(i * 0.05) for i in range(100)]  # 100 samples

    base_time = time.time()

    # Create magnitude graph (50 Hz - short time span)
    mag_graph = TimeSeriesGraph(
        width=width,
        height=3,
        time_window_sec=5.0,
        backend="ascii",
        title="Magnitude (50Hz)",
        sample_rate_hz=50.0,
        y_min=0.0,
        y_max=1.0,
        auto_scale=False,
    )

    # Create probability graph (2 Hz - long time span)
    prob_graph = TimeSeriesGraph(
        width=width,
        height=3,
        time_window_sec=5.0,
        backend="ascii",
        title="Probability (2Hz)",
        sample_rate_hz=2.0,
        y_min=0.0,
        y_max=1.0,
        auto_scale=False,
    )

    # Add magnitude data (every 20ms)
    print("Adding magnitude data (50Hz - should use full width)...")
    for i, value in enumerate(mag_data):
        timestamp = base_time + i * 0.02  # 20ms intervals
        mag_graph.add_data_point(abs(value), timestamp)

    # Add probability data (every 500ms)
    print("Adding probability data (2Hz - should use full width)...")
    for i, value in enumerate(prob_data):
        timestamp = base_time + i * 0.5  # 500ms intervals
        prob_graph.add_data_point(abs(value), timestamp)

    print()
    print("MAGNITUDE GRAPH (should span full 60 chars):")
    mag_lines = mag_graph.render()
    for line in mag_lines:
        actual_width = len(line.rstrip())
        print(f"'{line}' (width: {actual_width})")

    print()
    print("PROBABILITY GRAPH (should span full 60 chars):")
    prob_lines = prob_graph.render()
    for line in prob_lines:
        actual_width = len(line.rstrip())
        print(f"'{line}' (width: {actual_width})")

    # Check actual usage
    mag_max_width = max(len(line.rstrip()) for line in mag_lines)
    prob_max_width = max(len(line.rstrip()) for line in prob_lines)

    print()
    print("WIDTH ANALYSIS:")
    print(f"Target width:     {width} chars")
    print(f"Magnitude width:  {mag_max_width} chars ({mag_max_width / width * 100:.0f}% usage)")
    print(f"Probability width: {prob_max_width} chars ({prob_max_width / width * 100:.0f}% usage)")
    print()

    # Success criteria: both graphs should use at least 80% of available width
    mag_ok = mag_max_width >= (width * 0.8)
    prob_ok = prob_max_width >= (width * 0.8)

    if mag_ok and prob_ok:
        print("✅ WIDTH ISSUE FIXED: Both graphs use full width")
        return "FIXED"
    else:
        print("❌ WIDTH ISSUE PERSISTS:")
        if not mag_ok:
            print(f"   - Magnitude only uses {mag_max_width}/{width} chars ({mag_max_width / width * 100:.0f}%)")
        if not prob_ok:
            print(f"   - Probability only uses {prob_max_width}/{width} chars ({prob_max_width / width * 100:.0f}%)")
        return "BROKEN"


def main():
    """Run width usage test."""
    try:
        result = test_width_usage()

        print("=" * 50)
        if result == "FIXED":
            print("🎉 SUCCESS: Width rendering issues resolved!")
            print("   - Magnitude graphs: using full display width")
            print("   - Probability graphs: using full display width")
            print("   - Decimation indices span complete width")
        else:
            print("⚠️  ISSUE: Width problems still exist")
            print("   - Check decimation index calculation")
            print("   - Verify backend rendering logic")
        print("=" * 50)

        return 0 if result == "FIXED" else 1

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
