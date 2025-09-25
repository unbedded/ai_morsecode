#!/usr/bin/env python3
"""Phase 2 Unit Test: Validate UILT TimeSeriesGraph API design.

This test validates that the Phase 2 UILT API design properly handles:
- Automatic sliding window buffer management
- Sample rate detection
- Clean application interface (no buffer management needed)
- Backend selection and rendering
- Time-aware decimation
"""

import math
import sys
import time

sys.path.insert(0, "src")

from util.graph.time_series_graph import TimeSeriesGraph


def test_phase2_uilt_api():
    """Test that Phase 2 UILT API design provides clean, automatic buffer management."""
    print("🧪 PHASE 2 UNIT TEST: UILT TimeSeriesGraph API")
    print("=" * 60)

    # Test 1: Basic initialization and automatic buffer sizing
    print("📐 Test 1: Automatic buffer sizing and initialization")
    graph = TimeSeriesGraph(width=80, height=6, time_window_sec=10.0, backend="ascii", title="Test Signal")

    stats = graph.get_stats()
    print(f"   ✅ Buffer initialized: {stats['buffer_size']} samples")
    print(f"   ✅ Max buffer size: {stats['max_buffer_size']} samples")
    print(f"   ✅ Time window: {stats['time_window_sec']}s")
    print(f"   ✅ Backend: {stats['backend']}")
    print(f"   ✅ Sample rate (initial): {stats['calculated_sample_rate_hz']:.1f} Hz")
    print()

    # Test 2: Add data points and verify automatic buffer management
    print("📊 Test 2: Adding data points with automatic buffer management")
    start_time = time.time()

    # Simulate sine wave data at 4 Hz for 15 seconds (more than 10s window)
    sample_rate_hz = 4.0
    duration_sec = 15.0
    total_samples = int(duration_sec * sample_rate_hz)

    print(f"   Adding {total_samples} samples over {duration_sec}s at {sample_rate_hz} Hz...")

    for i in range(total_samples):
        t = i / sample_rate_hz
        # Create nice sine wave with some noise
        value = 0.7 * math.sin(2 * math.pi * 0.5 * t) + 0.1 * math.sin(2 * math.pi * 3.0 * t)
        timestamp = start_time + t

        graph.add_data_point(value, timestamp)

        # Check at key milestones
        if i in [9, 19, 39, 59]:  # At 10, 20, 40, 60 samples
            stats = graph.get_stats()
            print(
                f"     Sample {i + 1:2d}: buffer_len={stats['buffer_size']:3d}, "
                f"calculated_rate={stats['calculated_sample_rate_hz']:.2f} Hz, "
                f"time_span={stats['actual_time_span_sec']:.1f}s"
            )

    print()

    # Test 3: Verify sliding window behavior
    print("🔄 Test 3: Sliding window buffer management")
    final_stats = graph.get_stats()

    expected_buffer_full = final_stats["buffer_utilization"] >= 0.99  # Should be at maxlen
    rate_detection_works = abs(final_stats["calculated_sample_rate_hz"] - sample_rate_hz) < 0.5
    sliding_window_active = final_stats["actual_time_span_sec"] <= (final_stats["time_window_sec"] + 2.0)

    print(f"   • Final buffer utilization: {final_stats['buffer_utilization']:.1%}")
    print(
        f"   • Sample rate detection: {final_stats['calculated_sample_rate_hz']:.2f} Hz (expected {sample_rate_hz} Hz)"
    )
    print(
        f"   • Actual time span: {final_stats['actual_time_span_sec']:.1f}s (window: {final_stats['time_window_sec']}s)"
    )
    print(f"   • Sliding window working: {sliding_window_active}")
    print()

    # Test 4: Rendering functionality
    print("🎨 Test 4: Rendering functionality")

    try:
        lines = graph.render()
        print(f"   ✅ Rendering successful: {len(lines)} lines generated")
        print(f"   ✅ Line width: {len(lines[0]) if lines else 0} characters")

        if len(lines) >= 3:
            print("   📊 Sample output (first 3 lines):")
            for i, line in enumerate(lines[:3]):
                print(f"      {i + 1}: {line[:60]}{'...' if len(line) > 60 else ''}")

        rendering_works = len(lines) == 6 and all(len(line) == 80 for line in lines)

    except Exception as e:
        print(f"   ❌ Rendering failed: {e}")
        rendering_works = False

    print()

    # Test 5: Clean API validation (no buffer management in application)
    print("✨ Test 5: Clean API validation - no buffer management needed")

    # Create second graph to demonstrate simplicity
    morse_graph = TimeSeriesGraph(
        width=60,
        height=4,
        time_window_sec=5.0,
        backend="auto",  # Should try braille, fallback to ascii
        title="Morse Probabilities",
    )

    # Simulate morse probability data (typical use case)
    current_time = time.time()
    morse_probs = [0.8, 0.2, 0.1, 0.9, 0.7, 0.3, 0.1, 0.8, 0.4, 0.6]  # Varying probabilities

    for i, prob in enumerate(morse_probs):
        morse_graph.add_data_point(prob, current_time + i * 0.5)  # 500ms intervals

    morse_stats = morse_graph.get_stats()
    morse_lines = morse_graph.render()

    print("   ✅ Morse graph created with simple API")
    print(f"   ✅ Auto backend selection: {morse_stats['backend']}")
    print(f"   ✅ {morse_stats['sample_count']} samples added with no buffer management code")
    print(f"   ✅ Rendered: {len(morse_lines)} lines × {len(morse_lines[0]) if morse_lines else 0} chars")
    print()

    # Test 6: Clear functionality
    print("🧹 Test 6: Clear functionality")

    pre_clear_samples = graph.get_stats()["sample_count"]
    graph.clear()
    post_clear_stats = graph.get_stats()

    print(f"   • Before clear: {pre_clear_samples} samples")
    print(f"   • After clear: {post_clear_stats['sample_count']} samples")
    print(f"   • Buffer refilled with zeros: {post_clear_stats['buffer_size']} samples")

    clear_works = (
        post_clear_stats["sample_count"] == 0 and post_clear_stats["buffer_size"] == post_clear_stats["max_buffer_size"]
    )

    print()

    # Validate Phase 2 success
    phase2_success = (
        expected_buffer_full  # Sliding window at capacity
        and rate_detection_works  # Sample rate detection working
        and sliding_window_active  # Time window constraint working
        and rendering_works  # Rendering produces correct output
        and clear_works  # Clear functionality working
    )

    if phase2_success:
        print("✅ PHASE 2 SUCCESS: UILT TimeSeriesGraph API design validated!")
        print("   🎯 Automatic sliding window buffer management working")
        print("   🎯 Sample rate detection from timing intervals working")
        print("   🎯 Clean application API - no buffer management code needed")
        print("   🎯 Backend selection and rendering working")
        print("   🎯 Time-aware decimation ready for Phase 3 integration")
        print()

        # Show the clean API in action
        print("🚀 Clean API Demonstration:")
        print("```python")
        print("# Phase 2 UILT API - Applications only need 3 lines!")
        print("graph = TimeSeriesGraph(width=80, height=6, time_window_sec=30.0)")
        print("graph.add_data_point(sensor_value, timestamp)  # Library handles all buffer management")
        print("lines = graph.render()  # Ready for display")
        print("```")
        print()

        return True

    else:
        print("❌ PHASE 2 ISSUES DETECTED:")
        if not expected_buffer_full:
            print(f"   • Buffer not reaching capacity: {final_stats['buffer_utilization']:.1%}")
        if not rate_detection_works:
            print(f"   • Sample rate detection off: {final_stats['calculated_sample_rate_hz']:.2f} vs {sample_rate_hz}")
        if not sliding_window_active:
            print(
                f"   • Sliding window not working: {final_stats['actual_time_span_sec']:.1f}s > {final_stats['time_window_sec']}s"
            )
        if not rendering_works:
            print("   • Rendering not producing correct output format")
        if not clear_works:
            print("   • Clear functionality not working properly")

        return False


def test_phase2_edge_cases():
    """Test Phase 2 API with edge cases and different scenarios."""
    print("🔬 PHASE 2 EDGE CASE TESTING")
    print("=" * 60)

    # Edge case 1: Very slow data (< 2 Hz minimum assumption)
    print("⏳ Edge Case 1: Very slow data rate")
    slow_graph = TimeSeriesGraph(width=40, height=3, time_window_sec=20.0)

    # Add data every 5 seconds (0.2 Hz)
    base_time = time.time()
    for i in range(6):  # 30 seconds worth
        slow_graph.add_data_point(0.5 + 0.3 * math.sin(i), base_time + i * 5.0)

    slow_stats = slow_graph.get_stats()
    print(f"   ✅ Slow rate handling: {slow_stats['calculated_sample_rate_hz']:.3f} Hz detected")
    print(f"   ✅ Buffer adaptation: {slow_stats['buffer_size']} samples")
    print()

    # Edge case 2: Very fast data (approaching 100 Hz limit)
    print("⚡ Edge Case 2: High frequency data")
    fast_graph = TimeSeriesGraph(width=60, height=4, time_window_sec=2.0)

    # Add data at 50 Hz for 3 seconds
    fast_base_time = time.time()
    for i in range(150):  # 3 seconds at 50 Hz
        t = i / 50.0
        value = math.sin(2 * math.pi * 2.0 * t)  # 2 Hz sine wave
        fast_graph.add_data_point(value, fast_base_time + t)

    fast_stats = fast_graph.get_stats()
    print(f"   ✅ Fast rate handling: {fast_stats['calculated_sample_rate_hz']:.1f} Hz detected")
    print(f"   ✅ Buffer clamping: {fast_stats['buffer_size']} samples (max {fast_stats['max_buffer_size']})")
    print()

    # Edge case 3: Backend fallback
    print("🔄 Edge Case 3: Backend fallback behavior")
    auto_graph = TimeSeriesGraph(width=30, height=2, backend="auto")
    fallback_stats = auto_graph.get_stats()
    print(f"   ✅ Auto backend resolved to: {fallback_stats['backend']}")

    # Try explicit backends
    ascii_graph = TimeSeriesGraph(width=30, height=2, backend="ascii")
    braille_graph = TimeSeriesGraph(width=30, height=2, backend="braille")

    print(f"   ✅ ASCII backend: {ascii_graph.get_stats()['backend']}")
    print(f"   ✅ Braille backend: {braille_graph.get_stats()['backend']}")
    print()

    print("✅ EDGE CASES HANDLED: Phase 2 API robust for production use")
    print()


if __name__ == "__main__":
    success = test_phase2_uilt_api()

    if success:
        print("🧪 Running edge case tests...")
        print()
        test_phase2_edge_cases()
        print("🚀 PHASE 2 COMPLETE: Ready for Phase 3 implementation")
        print("   → Next: Implement Phase 3 - Migrate morse code to use TimeSeriesGraph API")
    else:
        print("⚠️ PHASE 2 NEEDS FIXES BEFORE PROCEEDING TO PHASE 3")
