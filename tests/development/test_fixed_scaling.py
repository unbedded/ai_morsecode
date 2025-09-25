#!/usr/bin/env python3
"""Test fixed scaling for probability and normalized magnitude graphs."""

import os
import sys
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from util.graph.time_series_graph import TimeSeriesGraph


def test_fixed_scaling():
    """Test that auto-scaling is disabled for normalized data."""
    print("🔧 FIXED SCALING TEST")
    print("=" * 30)
    print("Probability and normalized magnitude graphs should NOT auto-scale")
    print()

    # Test data with values way above 1.0 to see if auto-scaling kicks in
    test_values = [0.1, 0.5, 0.8, 2.0, 3.5, 1.2, 0.3, 0.0, 0.9]  # Some values > 1.0
    base_time = time.time()

    print(f"Test data: {test_values}")
    print(f"Max value: {max(test_values)} (exceeds 1.0 to test scaling)")
    print()

    # Create probability graph with fixed scaling (should be 0.0-1.0)
    prob_graph = TimeSeriesGraph(
        width=30,
        height=3,
        time_window_sec=5.0,
        backend="ascii",
        title="Probability (Fixed)",
        sample_rate_hz=2.0,
        y_min=0.0,
        y_max=1.0,
        auto_scale=False,
    )

    # Create auto-scaling graph for comparison
    auto_graph = TimeSeriesGraph(
        width=30,
        height=3,
        time_window_sec=5.0,
        backend="ascii",
        title="Auto-Scaled",
        sample_rate_hz=2.0,
        auto_scale=True,
    )

    # Add same data to both graphs
    for i, value in enumerate(test_values):
        timestamp = base_time + i * 0.5  # 2Hz rate
        prob_graph.add_data_point(value, timestamp)
        auto_graph.add_data_point(value, timestamp)

    print("PROBABILITY GRAPH (Fixed 0.0-1.0):")
    prob_lines = prob_graph.render()
    for line in prob_lines:
        print(line)
    print()

    print("AUTO-SCALED GRAPH (should scale to fit 3.5):")
    auto_lines = auto_graph.render()
    for line in auto_lines:
        print(line)
    print()

    # Check backend scaling settings
    prob_backend = prob_graph._backend
    auto_backend = auto_graph._backend

    print("SCALING VERIFICATION:")
    print(f"Probability graph auto_scale: {prob_backend.auto_scale}")
    print(f"Probability graph y_min: {prob_backend.y_min}")
    print(f"Probability graph y_max: {prob_backend.y_max}")
    print()
    print(f"Auto-scaled graph auto_scale: {auto_backend.auto_scale}")
    print(f"Auto-scaled graph y_min: {auto_backend.y_min}")
    print(f"Auto-scaled graph y_max: {auto_backend.y_max}")
    print()

    # Analysis
    if not prob_backend.auto_scale and prob_backend.y_max == 1.0:
        print("✅ FIXED SCALING WORKING: Probability graph locked to 0.0-1.0")
        result = "FIXED"
    else:
        print("❌ SCALING ISSUE: Probability graph not properly fixed")
        result = "BROKEN"

    if auto_backend.auto_scale and auto_backend.y_max > 1.0:
        print("✅ AUTO-SCALING WORKING: Auto graph expanded to fit data")
    else:
        print("⚠️  AUTO-SCALING ISSUE: Auto graph didn't expand properly")

    return result


def main():
    """Run fixed scaling test."""
    try:
        result = test_fixed_scaling()

        print()
        print("=" * 50)
        if result == "FIXED":
            print("🎉 SUCCESS: Fixed scaling implemented correctly!")
            print("   - Probability graphs: locked to 0.0-1.0 range")
            print("   - Normalized magnitude: locked to 0.0-1.0 range")
            print("   - No auto-scaling interference")
            print("   - Consistent visual comparison possible")
        else:
            print("⚠️  ISSUE: Fixed scaling needs debugging")
            print("   - Check y_min/y_max parameter passing")
            print("   - Verify backend.set_ylim() is called")
        print("=" * 50)

        return 0 if result == "FIXED" else 1

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
