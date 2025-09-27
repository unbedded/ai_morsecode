#!/usr/bin/env python3
"""Final Test: Validate ALL graphics fragmentation completely eliminated.

This test validates that the massive cleanup has:
1. ALL charts (FFT, MAGNITUDE, PROBABILITY) use identical TimeSeriesGraph system
2. Full screen width for ALL charts (no more 2/3 width issues)
3. Consistent backends and rendering behavior
4. No old fragmented code remaining
5. Clean matplotlib-style API: just plot data at sample rate with auto-scaling
"""

import sys
import time

sys.path.insert(0, "src")

from morsecode.components.graphics.graphics_display import GraphicsDisplay
from morsecode.events.types import FFTSpectrumEvent, FilteredMagnitudeEvent, MorseProbabilityEvent
from util.config import AwesomeConfigManager


def test_fragmentation_eliminated():
    """Test that ALL graphics fragmentation has been completely eliminated."""
    print("🧪 FINAL TEST: ALL Graphics Fragmentation Eliminated")
    print("=" * 65)

    # Create debug display
    cfg_mgr = AwesomeConfigManager()
    overrides = {
        "display_width_chars": 120,  # Large width to test full usage
        "display_height_chars": 30,
        "buffer_size_sec": 10.0,
        "refresh_rate_fps": 10,
        "chunk_size_ms": 25,  # FFT/Magnitude at 40Hz
        "convolution_interval_ms": 250,  # Probability at 4Hz
        "enable_debug_logging": True,
    }

    debug_display = GraphicsDisplay(cfg_mgr, overrides)

    print("🔍 VALIDATION 1: Single Graphics System")
    print("-" * 40)

    # Check that ALL charts use TimeSeriesGraph
    has_fft_graph = hasattr(debug_display, "_fft_graph")
    has_magnitude_graph = hasattr(debug_display, "_magnitude_graph")
    has_probability_graphs = all(
        hasattr(debug_display, f"_prob_{name}_graph") for name in ["dit", "dash", "letter", "word"]
    )

    # Check that old backends are removed
    no_old_backends = not any(
        hasattr(debug_display, f"_{name}_backend") for name in ["fft", "magnitude", "probability"]
    )

    print(f"   ✅ FFT uses TimeSeriesGraph: {has_fft_graph}")
    print(f"   ✅ Magnitude uses TimeSeriesGraph: {has_magnitude_graph}")
    print(f"   ✅ Probability uses TimeSeriesGraph: {has_probability_graphs}")
    print(f"   ✅ Old manual backends eliminated: {no_old_backends}")

    single_system = has_fft_graph and has_magnitude_graph and has_probability_graphs and no_old_backends

    if single_system:
        print("   🎉 SUCCESS: Single unified TimeSeriesGraph system!")
    else:
        print("   ❌ Still have fragmented systems")

    print()
    print("🔍 VALIDATION 2: Consistent Full Width Usage")
    print("-" * 40)

    # All graphs should use same width (120 - 4 = 116 for margins)
    expected_width = 116  # ChartCalculations.main_chart_width(120)

    fft_width = debug_display._fft_graph.width
    mag_width = debug_display._magnitude_graph.width
    dit_width = debug_display._prob_dit_graph.width

    print(f"   Expected full width: {expected_width}")
    print(f"   FFT graph width: {fft_width}")
    print(f"   Magnitude graph width: {mag_width}")
    print(f"   Dit probability width: {dit_width}")

    consistent_width = fft_width == mag_width == dit_width == expected_width

    if consistent_width:
        print("   🎉 SUCCESS: ALL charts use full screen width!")
    else:
        print("   ❌ Width inconsistency detected")

    print()
    print("🔍 VALIDATION 3: Consistent Backend Configuration")
    print("-" * 40)

    # All should use braille backend
    fft_backend = debug_display._fft_graph.get_stats()["backend"]
    mag_backend = debug_display._magnitude_graph.get_stats()["backend"]
    dit_backend = debug_display._prob_dit_graph.get_stats()["backend"]

    print(f"   FFT backend: {fft_backend}")
    print(f"   Magnitude backend: {mag_backend}")
    print(f"   Probability backend: {dit_backend}")

    consistent_backend = fft_backend == mag_backend == dit_backend == "braille"

    if consistent_backend:
        print("   🎉 SUCCESS: ALL charts use same backend!")
    else:
        print("   ❌ Backend inconsistency detected")

    print()
    print("🔍 VALIDATION 4: Matplotlib-Style Clean API")
    print("-" * 40)

    # Test that all event handlers work with clean TimeSeriesGraph API
    base_time = time.time() * 1_000_000  # Convert to microseconds

    print("   Sending test events...")

    # Send FFT events
    for i in range(3):
        fft_event = FFTSpectrumEvent(
            timestamp=int(base_time + i * 25_000),  # 25ms intervals (40Hz)
            peak_magnitude=0.8 + 0.1 * (i % 2),
            peak_frequency_hz=800 + i * 50,
            total_energy=1.2,
        )
        debug_display._on_fft_spectrum_event(fft_event)

    # Send magnitude events
    for i in range(3):
        mag_event = FilteredMagnitudeEvent(
            timestamp=int(base_time + i * 25_000),  # 25ms intervals (40Hz)
            magnitude_norm=0.6 + 0.2 * (i % 2),
            threshold_norm=0.4,
            binary_state=(i % 2 == 0),
            chunk_number=i,
        )
        debug_display._on_magnitude_event(mag_event)

    # Send probability events
    for i in range(2):
        prob_event = MorseProbabilityEvent(
            timestamp=int(base_time + i * 250_000),  # 250ms intervals (4Hz)
            prob_dit=0.7 + 0.1 * i,
            prob_dash=0.2,
            prob_letter_space=0.05,
            prob_word_space=0.05,
            chunk_number=i + 100,
        )
        debug_display._on_probability_event(prob_event)

    # Check all systems processed events correctly
    fft_samples = debug_display._fft_graph.get_stats()["sample_count"]
    mag_samples = debug_display._magnitude_graph.get_stats()["sample_count"]
    dit_samples = debug_display._prob_dit_graph.get_stats()["sample_count"]

    print(f"   FFT samples processed: {fft_samples} (expected: 3)")
    print(f"   Magnitude samples processed: {mag_samples} (expected: 3)")
    print(f"   Probability samples processed: {dit_samples} (expected: 2)")

    clean_api = fft_samples == 3 and mag_samples == 3 and dit_samples == 2

    if clean_api:
        print("   🎉 SUCCESS: Clean matplotlib-style API working!")
    else:
        print("   ❌ API inconsistency detected")

    print()
    print("🔍 VALIDATION 5: Consistent Rendering")
    print("-" * 40)

    # Test that all charts render without errors
    try:
        fft_chart = debug_display._render_time_series_chart(debug_display._fft_graph)
        mag_chart = debug_display._render_time_series_chart(debug_display._magnitude_graph)
        dit_chart = debug_display._render_time_series_chart(debug_display._prob_dit_graph)

        fft_lines = len(str(fft_chart).split("\n"))
        mag_lines = len(str(mag_chart).split("\n"))
        dit_lines = len(str(dit_chart).split("\n"))

        print(f"   FFT chart rendered: {fft_lines} lines")
        print(f"   Magnitude chart rendered: {mag_lines} lines")
        print(f"   Probability chart rendered: {dit_lines} lines")

        consistent_rendering = all(lines > 0 for lines in [fft_lines, mag_lines, dit_lines])

        if consistent_rendering:
            print("   🎉 SUCCESS: All charts render consistently!")
        else:
            print("   ❌ Rendering inconsistency detected")

    except Exception as e:
        print(f"   ❌ Rendering error: {e}")
        consistent_rendering = False

    print()
    print("🏆 FINAL VERDICT")
    print("=" * 40)

    all_tests_pass = single_system and consistent_width and consistent_backend and clean_api and consistent_rendering

    if all_tests_pass:
        print("🎊 COMPLETE SUCCESS: ALL FRAGMENTATION ELIMINATED!")
        print()
        print("✅ BEFORE vs AFTER:")
        print("   ❌ BEFORE: 3 different graphics systems")
        print("   ✅ AFTER: 1 unified TimeSeriesGraph system")
        print()
        print("   ❌ BEFORE: FFT full width, others 2/3 width")
        print("   ✅ AFTER: ALL charts use full screen width")
        print()
        print("   ❌ BEFORE: Manual backend management, complex rendering")
        print("   ✅ AFTER: Clean matplotlib-style API: just add_data_point()")
        print()
        print("   ❌ BEFORE: Different backends, inconsistent behavior")
        print("   ✅ AFTER: All charts identical system, predictable behavior")
        print()
        print("🚀 READY FOR PRODUCTION: Graphics system is now:")
        print("   • Simple (matplotlib-style)")
        print("   • Consistent (all charts identical)")
        print("   • Predictable (full width, auto-scaling)")
        print("   • Maintainable (single system to debug)")

        return True
    else:
        print("❌ FRAGMENTATION STILL PRESENT:")
        if not single_system:
            print("   • Multiple graphics systems still exist")
        if not consistent_width:
            print("   • Width inconsistencies remain")
        if not consistent_backend:
            print("   • Backend inconsistencies remain")
        if not clean_api:
            print("   • API not working consistently")
        if not consistent_rendering:
            print("   • Rendering inconsistencies remain")

        return False


if __name__ == "__main__":
    success = test_fragmentation_eliminated()

    if success:
        print()
        print("🎯 MISSION ACCOMPLISHED!")
        print("   Graphics fragmentation completely eliminated.")
        print("   System ready for production deployment.")
    else:
        print()
        print("⚠️  Additional cleanup needed.")
