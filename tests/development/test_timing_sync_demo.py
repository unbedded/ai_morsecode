#!/usr/bin/env python3
"""Test timing synchronization with same data at different sample rates.

This directly tests the root cause issue: same data with different sample rates
should scroll proportionally to their update rates.
"""

import math
import os
import sys
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from util.graph.time_series_graph import TimeSeriesGraph


def test_timing_synchronization():
    """Test the core timing synchronization issue."""
    print("🔍 TIMING SYNCHRONIZATION TEST")
    print("=" * 40)
    print("Same data, different sample rates should scroll proportionally")
    print()

    # Generate identical signal data
    signal_data = []
    for i in range(100):
        # Simple sine wave
        value = math.sin(i * 0.1) + 0.5 * math.sin(i * 0.3)
        signal_data.append(value)

    print(f"Test data: {len(signal_data)} identical samples")
    print()

    # Create graphs with different sample rates (like magnitude vs probability)
    magnitude_rate = 50.0  # 50 Hz (like magnitude updates every 20ms)
    probability_rate = 2.0  # 2 Hz (like probability updates every 500ms)

    # Same time window for both
    time_window = 5.0

    print(f"Graph 1 (Magnitude): {magnitude_rate} Hz → updates every {1000 / magnitude_rate:.0f}ms")
    print(f"Graph 2 (Probability): {probability_rate} Hz → updates every {1000 / probability_rate:.0f}ms")
    print(f"Expected ratio: Probability should slide {magnitude_rate / probability_rate:.0f}x MORE per update")
    print()

    # Create TimeSeriesGraphs
    mag_graph = TimeSeriesGraph(
        width=40,
        height=3,
        time_window_sec=time_window,
        backend="ascii",
        title="Magnitude (50Hz)",
        sample_rate_hz=magnitude_rate,
    )

    prob_graph = TimeSeriesGraph(
        width=40,
        height=3,
        time_window_sec=time_window,
        backend="ascii",
        title="Probability (2Hz)",
        sample_rate_hz=probability_rate,
    )

    # Add same data with different timing
    base_time = time.time()

    print("Adding data with proper timing...")

    # Add data at magnitude rate (every 20ms)
    for i, value in enumerate(signal_data):
        timestamp = base_time + i * (1.0 / magnitude_rate)  # 20ms intervals
        mag_graph.add_data_point(value, timestamp)

    # Add same data at probability rate (every 500ms)
    for i, value in enumerate(signal_data):
        timestamp = base_time + i * (1.0 / probability_rate)  # 500ms intervals
        prob_graph.add_data_point(value, timestamp)

    print("Rendering graphs...")
    print()

    # Get buffer stats to verify timing
    mag_stats = mag_graph.get_stats()
    prob_stats = prob_graph.get_stats()

    print("BUFFER ANALYSIS:")
    print(f"Magnitude buffer: {mag_stats['buffer_size']} samples, {mag_stats['actual_time_span_sec']:.2f}s span")
    print(f"Probability buffer: {prob_stats['buffer_size']} samples, {prob_stats['actual_time_span_sec']:.2f}s span")
    print()

    # The key test: time span per sample should be different!
    mag_time_per_sample = (
        mag_stats["actual_time_span_sec"] / mag_stats["buffer_size"] if mag_stats["buffer_size"] > 0 else 0
    )
    prob_time_per_sample = (
        prob_stats["actual_time_span_sec"] / prob_stats["buffer_size"] if prob_stats["buffer_size"] > 0 else 0
    )

    print("TIME SCALING ANALYSIS:")
    print(f"Magnitude time per sample: {mag_time_per_sample:.3f}s")
    print(f"Probability time per sample: {prob_time_per_sample:.3f}s")
    print(f"Ratio: {prob_time_per_sample / mag_time_per_sample:.1f}x (should be 25x for proper scaling)")
    print()

    # Render the graphs
    print("MAGNITUDE GRAPH (50Hz updates):")
    mag_lines = mag_graph.render()
    for line in mag_lines:
        print(line)
    print()

    print("PROBABILITY GRAPH (2Hz updates - same data!):")
    prob_lines = prob_graph.render()
    for line in prob_lines:
        print(line)
    print()

    # Analysis
    print("ROOT CAUSE ANALYSIS:")
    if abs(prob_time_per_sample / mag_time_per_sample - 25.0) < 5.0:
        print("✅ TIMING FIXED: Probability samples have 25x longer time span")
        print("   This means probability graphs will slide 25x MORE per update")
        print("   - Magnitude updates every 20ms → slides 1 char")
        print("   - Probability updates every 500ms → slides 25 chars")
        result = "FIXED"
    else:
        print("❌ TIMING ISSUE PERSISTS: Time scaling not proportional")
        print("   Both graphs compressed to same visual time span")
        print("   This causes probability graphs to scroll too slowly")
        result = "BROKEN"

    return result


def main():
    """Run timing synchronization test."""
    try:
        result = test_timing_synchronization()

        print()
        print("=" * 50)
        if result == "FIXED":
            print("🎉 SUCCESS: Timing synchronization root cause FIXED!")
            print("   - Different sample rates now have proportional scrolling")
            print("   - TimeSeriesGraph handles time scaling correctly")
            print("   - Probability graphs should now scroll properly")
        else:
            print("⚠️  ISSUE: Timing synchronization still problematic")
            print("   - Need to investigate TimeSeriesGraph time scaling")
            print("   - May need fixes in decimation system")
        print("=" * 50)

        return 0 if result == "FIXED" else 1

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
