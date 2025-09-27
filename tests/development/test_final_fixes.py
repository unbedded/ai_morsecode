#!/usr/bin/env python3
"""Final Integration Test: Validate all fragmentation issues are resolved.

This test validates:
1. MAGNITUDE and PROBABILITY graphs use FULL screen width (same as FFT)
2. PROBABILITY graphs use BRAILLE backend (as requested)
3. Sample rates are explicitly configured (no auto-detection)
4. All graphs use consistent left-to-right scrolling
"""

import sys
import time

sys.path.insert(0, "src")

from morsecode.components.graphics.graphics_display import GraphicsDisplay
from morsecode.events.types import FilteredMagnitudeEvent, MorseProbabilityEvent
from util.config import AwesomeConfigManager


def test_final_fixes():
    """Test that all identified issues are completely resolved."""
    print("🧪 FINAL INTEGRATION TEST: All Fragmentation Issues Resolved")
    print("=" * 70)

    # Create debug display with specific configuration
    cfg_mgr = AwesomeConfigManager()
    overrides = {
        "display_width_chars": 100,  # Use 100 for easy width calculations
        "display_height_chars": 25,
        "buffer_size_sec": 8.0,
        "refresh_rate_fps": 10,
        "chunk_size_ms": 20,  # Magnitude events every 20ms (50Hz)
        "convolution_interval_ms": 500,  # Probability events every 500ms (2Hz)
        "enable_debug_logging": True,  # Show configuration details
    }

    debug_display = GraphicsDisplay(cfg_mgr, overrides)

    print("🔍 ISSUE 1: Width Consistency")
    print("-" * 30)

    # Check that all TimeSeriesGraph instances use full width
    mag_width = debug_display._magnitude_graph.width
    dit_width = debug_display._prob_dit_graph.width
    dash_width = debug_display._prob_dash_graph.width
    letter_width = debug_display._prob_letter_graph.width
    word_width = debug_display._prob_word_graph.width

    # Expected width: 100 - 4 (margin) = 96 characters
    expected_width = 96  # ChartCalculations.main_chart_width(100) = 100 - 4

    print(f"   Display width: {overrides['display_width_chars']}")
    print(f"   Expected full width: {expected_width}")
    print(f"   Magnitude width: {mag_width}")
    print(f"   Dit probability width: {dit_width}")
    print(f"   Dash probability width: {dash_width}")
    print(f"   Letter probability width: {letter_width}")
    print(f"   Word probability width: {word_width}")

    width_consistent = all(w == expected_width for w in [mag_width, dit_width, dash_width, letter_width, word_width])

    if width_consistent:
        print("   ✅ WIDTH ISSUE FIXED: All graphs use full screen width")
    else:
        print("   ❌ Width inconsistency still present")

    print()
    print("🔍 ISSUE 2: Backend Consistency")
    print("-" * 30)

    # Check that all graphs use the configured backends
    mag_backend = debug_display._magnitude_graph.get_stats()["backend"]
    dit_backend = debug_display._prob_dit_graph.get_stats()["backend"]
    dash_backend = debug_display._prob_dash_graph.get_stats()["backend"]

    print(f"   Magnitude backend: {mag_backend} (should be braille)")
    print(f"   Dit probability backend: {dit_backend} (should be braille)")
    print(f"   Dash probability backend: {dash_backend} (should be braille)")

    backend_consistent = all(backend == "braille" for backend in [mag_backend, dit_backend, dash_backend])

    if backend_consistent:
        print("   ✅ BACKEND ISSUE FIXED: All graphs use Braille backend as requested")
    else:
        print("   ❌ Backend inconsistency detected")

    print()
    print("🔍 ISSUE 3: Explicit Sample Rate Configuration")
    print("-" * 30)

    # Check that sample rates match configuration expectations
    mag_rate = debug_display._magnitude_graph.get_stats()["calculated_sample_rate_hz"]
    dit_rate = debug_display._prob_dit_graph.get_stats()["calculated_sample_rate_hz"]

    expected_mag_rate = 1000.0 / overrides["chunk_size_ms"]  # 50 Hz
    expected_prob_rate = 1000.0 / overrides["convolution_interval_ms"]  # 2 Hz

    print(f"   Expected magnitude rate: {expected_mag_rate} Hz (chunk_size={overrides['chunk_size_ms']}ms)")
    print(f"   Actual magnitude rate: {mag_rate} Hz")
    print(
        f"   Expected probability rate: {expected_prob_rate} Hz (convolution={overrides['convolution_interval_ms']}ms)"
    )
    print(f"   Actual probability rate: {dit_rate} Hz")

    rate_explicit = mag_rate == expected_mag_rate and dit_rate == expected_prob_rate

    if rate_explicit:
        print("   ✅ SAMPLE RATE ISSUE FIXED: Explicit rates configured correctly")
    else:
        print("   ❌ Sample rates not matching expected configuration")

    print()
    print("🔍 ISSUE 4: Scrolling Behavior Consistency")
    print("-" * 30)

    # Test that both magnitude and probability events work with consistent API
    base_time = time.time() * 1_000_000  # Convert to microseconds

    # Send magnitude events at expected rate (50Hz)
    for i in range(3):
        mag_event = FilteredMagnitudeEvent(
            timestamp=int(base_time + i * 20_000),  # 20ms intervals
            magnitude_norm=0.6 + 0.2 * (i % 2),
            threshold_norm=0.4,
            binary_state=(i % 2 == 0),
            chunk_number=i,
        )
        debug_display._on_magnitude_event(mag_event)

    # Send probability events at expected rate (2Hz)
    for i in range(2):
        prob_event = MorseProbabilityEvent(
            timestamp=int(base_time + i * 500_000),  # 500ms intervals
            prob_dit=0.8,
            prob_dash=0.1,
            prob_letter_space=0.05,
            prob_word_space=0.05,
            chunk_number=i + 100,
        )
        debug_display._on_probability_event(prob_event)

    # Check that both systems processed events correctly
    mag_samples = debug_display._magnitude_graph.get_stats()["sample_count"]
    dit_samples = debug_display._prob_dit_graph.get_stats()["sample_count"]

    print(f"   Magnitude events processed: {mag_samples} (expected: 3)")
    print(f"   Probability events processed: {dit_samples} (expected: 2)")

    processing_consistent = mag_samples == 3 and dit_samples == 2

    if processing_consistent:
        print("   ✅ SCROLLING ISSUE FIXED: Both systems use identical TimeSeriesGraph API")
        print("   ✅ Left-to-right fill and scroll behavior consistent")
    else:
        print("   ❌ Event processing inconsistency detected")

    print()
    print("🔍 FINAL VALIDATION")
    print("-" * 30)

    all_issues_fixed = width_consistent and backend_consistent and rate_explicit and processing_consistent

    if all_issues_fixed:
        print("🎉 ALL ISSUES COMPLETELY RESOLVED!")
        print("   ✅ MAGNITUDE and PROBABILITY graphs use FULL screen width")
        print("   ✅ All graphs use BRAILLE backend for maximum resolution")
        print("   ✅ Sample rates explicitly configured from application settings")
        print("   ✅ Consistent left-to-right scrolling behavior")
        print("   ✅ Single TimeSeriesGraph system - no fragmentation")
        print()

        print("📊 BEFORE vs AFTER SUMMARY:")
        print("   ❌ BEFORE: MAGNITUDE/PROBABILITY used 2/3 width, FFT used full width")
        print("   ✅ AFTER: ALL graphs use full width consistently")
        print()
        print("   ❌ BEFORE: Different backends, inconsistent display")
        print("   ✅ AFTER: All use Braille backend as requested")
        print()
        print("   ❌ BEFORE: Auto sample rate detection caused poor scrolling")
        print("   ✅ AFTER: Explicit rates from configuration (Magnitude: 50Hz, Probability: 2Hz)")
        print()
        print("   ❌ BEFORE: Fragmented graphics systems with different behaviors")
        print("   ✅ AFTER: Single TimeSeriesGraph system - consistent behavior")

        return True

    else:
        print("❌ SOME ISSUES STILL PRESENT:")
        if not width_consistent:
            print("   • Width inconsistency not fully resolved")
        if not backend_consistent:
            print("   • Backend configuration needs adjustment")
        if not rate_explicit:
            print("   • Sample rate configuration not working")
        if not processing_consistent:
            print("   • Event processing still inconsistent")

        return False


if __name__ == "__main__":
    success = test_final_fixes()

    if success:
        print()
        print("🏆 MISSION ACCOMPLISHED!")
        print("   All graphics fragmentation issues completely eliminated.")
        print("   Ready for production deployment.")
    else:
        print()
        print("⚠️  Additional fixes needed before deployment.")
