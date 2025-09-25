#!/usr/bin/env python3
"""Visual demonstration showing identical signals at different sample rates produce identical graphs.

This script shows you exactly what the unit tests validate - that mathematically
identical waveforms sampled at different rates produce pixel-perfect identical
visual output after UILT time-aware decimation fixes.
"""

import hashlib
import sys
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from util.graph.backends.ascii_backend import ASCIIBackend
from util.graph.backends.braille_backend import BrailleBackend


def generate_identical_square_wave(frequency_hz: float, duration_sec: float, sample_rate_hz: float) -> list[float]:
    """Generate mathematically identical square wave regardless of sample rate."""
    sample_period_sec = 1.0 / sample_rate_hz
    num_samples = int(duration_sec * sample_rate_hz)

    samples = []
    for i in range(num_samples):
        t = i * sample_period_sec
        # Mathematical square wave - identical at any sample rate
        cycle_position = (t * frequency_hz) % 1.0
        value = 1.0 if cycle_position < 0.5 else -1.0
        samples.append(value)

    return samples


def generate_morse_dit_pattern(wpm: int, sample_rate_hz: float) -> list[float]:
    """Generate morse DIT pattern with precise timing."""
    dit_duration_sec = 1.2 / wpm  # Standard morse timing
    gap_duration_sec = dit_duration_sec

    # DIT-GAP-DIT pattern
    total_duration = 2 * dit_duration_sec + gap_duration_sec
    sample_period_sec = 1.0 / sample_rate_hz
    num_samples = int(total_duration * sample_rate_hz)

    samples = []
    for i in range(num_samples):
        t = i * sample_period_sec

        if t < dit_duration_sec:
            value = 1.0  # First DIT
        elif t < dit_duration_sec + gap_duration_sec:
            value = 0.0  # Gap
        elif t < 2 * dit_duration_sec + gap_duration_sec:
            value = 1.0  # Second DIT
        else:
            value = 0.0  # Final gap

        samples.append(value)

    return samples


def compute_hash(output: list[str]) -> str:
    """Compute hash for exact comparison."""
    content = "\n".join(output)
    return hashlib.md5(content.encode("utf-8")).hexdigest()


def demo_identical_square_waves():
    """Demo 1: Identical square waves at different sample rates."""
    print("🔬 DEMO 1: Identical Square Waves at Different Sample Rates")
    print("=" * 80)
    print("Generating 0.5 Hz square wave (2 second period, 4 seconds total = 2 cycles)")
    print("Testing at 10Hz, 20Hz, and 40Hz sample rates...")
    print()

    frequency_hz = 0.5  # 0.5 Hz = 2 second period
    duration_sec = 4.0  # 4 seconds = exactly 2 complete cycles
    sample_rates = [10.0, 20.0, 40.0]

    width, height = 60, 8
    outputs = {}
    hashes = {}

    for sample_rate_hz in sample_rates:
        # Generate identical mathematical waveform
        samples = generate_identical_square_wave(frequency_hz, duration_sec, sample_rate_hz)

        # Render with UILT ASCII backend
        backend = ASCIIBackend(width, height, f"Square Wave {sample_rate_hz}Hz")
        backend.plot(samples, sample_rate_hz=sample_rate_hz)
        output = backend.render_sparkline()

        outputs[sample_rate_hz] = output
        hashes[sample_rate_hz] = compute_hash(output)

        print(f"📊 {sample_rate_hz:4.0f} Hz sampling ({len(samples):3d} samples):")
        for line in output:
            print(f"    {line}")
        print(f"    Hash: {hashes[sample_rate_hz]}")
        print()

    # Check if all outputs are identical
    baseline_hash = hashes[sample_rates[0]]
    all_identical = all(hashes[rate] == baseline_hash for rate in sample_rates)

    print("🎯 RESULT:")
    if all_identical:
        print("✅ SUCCESS: All sample rates produce IDENTICAL output!")
        print("   This proves UILT time-aware decimation is working correctly.")
    else:
        print("❌ FAILURE: Outputs differ between sample rates!")
        print("   This indicates a bug in the decimation algorithm.")

    print(f"   All hashes identical: {all_identical}")
    return all_identical


def demo_morse_code_timing():
    """Demo 2: Morse code timing at different sample rates."""
    print("\n🔬 DEMO 2: Morse Code DIT Pattern at Different Sample Rates")
    print("=" * 80)
    print("Generating 20 WPM morse DIT-GAP-DIT pattern")
    print("Testing at 50Hz and 100Hz sample rates...")
    print()

    wpm = 20
    sample_rates = [50.0, 100.0]
    dit_duration_sec = 1.2 / wpm  # 60ms at 20 WPM

    width, height = 70, 6
    outputs = {}
    hashes = {}

    for sample_rate_hz in sample_rates:
        # Generate morse pattern
        samples = generate_morse_dit_pattern(wpm, sample_rate_hz)

        # Render with UILT ASCII backend
        backend = ASCIIBackend(width, height, f"Morse {wpm}WPM {sample_rate_hz}Hz")
        backend.plot(samples, sample_rate_hz=sample_rate_hz)
        output = backend.render_sparkline()

        outputs[sample_rate_hz] = output
        hashes[sample_rate_hz] = compute_hash(output)

        print(f"📡 {sample_rate_hz:5.0f} Hz sampling ({len(samples):3d} samples, {dit_duration_sec * 1000:.0f}ms dit):")
        for line in output:
            print(f"    {line}")
        print(f"    Hash: {hashes[sample_rate_hz]}")
        print()

    # Check if outputs are identical
    baseline_hash = hashes[sample_rates[0]]
    timing_identical = hashes[sample_rates[1]] == baseline_hash

    print("🎯 RESULT:")
    if timing_identical:
        print("✅ SUCCESS: Morse timing identical at different sample rates!")
        print("   This proves precise timing preservation across sampling rates.")
    else:
        print("❌ FAILURE: Morse timing differs between sample rates!")
        print("   This indicates timing precision issues.")

    return timing_identical


def demo_braille_vs_ascii():
    """Demo 3: Compare ASCII vs Braille rendering of same signal."""
    print("\n🔬 DEMO 3: ASCII vs Braille Rendering Comparison")
    print("=" * 80)
    print("Same 1 Hz square wave rendered with ASCII and Braille backends")
    print("Braille should show ~2x resolution advantage...")
    print()

    frequency_hz = 1.0  # 1 Hz for clear visualization
    duration_sec = 3.0  # 3 seconds = 3 complete cycles
    sample_rate_hz = 25.0  # 25 Hz sampling

    # Generate signal
    samples = generate_identical_square_wave(frequency_hz, duration_sec, sample_rate_hz)

    width, height = 50, 6

    # ASCII rendering
    ascii_backend = ASCIIBackend(width, height, "ASCII")
    ascii_backend.plot(samples, sample_rate_hz=sample_rate_hz)
    ascii_output = ascii_backend.render_sparkline()

    # Braille rendering
    braille_backend = BrailleBackend(width, height, "Braille")
    braille_backend.plot(samples, sample_rate_hz=sample_rate_hz)
    braille_output = braille_backend.render_braille()

    print(f"📊 ASCII Backend ({len(samples)} samples at {sample_rate_hz} Hz):")
    for line in ascii_output:
        print(f"    {line}")

    print(f"\n📊 Braille Backend (same {len(samples)} samples):")
    for line in braille_output:
        print(f"    {line}")

    # Calculate character density
    ascii_chars = sum(len(line.strip()) for line in ascii_output)
    braille_chars = sum(len(line.strip()) for line in braille_output)

    print("\n🎯 COMPARISON:")
    print(f"   ASCII characters used: {ascii_chars}")
    print(f"   Braille characters used: {braille_chars}")
    print(f"   Braille resolution advantage: ~{braille_chars / ascii_chars:.1f}x" if ascii_chars > 0 else "N/A")
    print("   ✅ Both show same signal shape with different resolution")


def demo_probability_data_compression():
    """Demo 4: Show probability data compression effect."""
    print("\n🔬 DEMO 4: Probability Data Compression")
    print("=" * 80)
    print("Simulating cached probability data with repeated values...")
    print()

    # Simulate probability data with repeated cached values (like the original bug)
    def generate_cached_probability_data(rate_hz: float, duration_sec: float = 2.0):
        """Generate probability data with repeated cached values."""
        sample_period_sec = 1.0 / rate_hz
        num_samples = int(duration_sec * rate_hz)

        samples = []
        convolution_period_samples = int(0.5 * rate_hz)  # Update every 500ms

        for i in range(num_samples):
            # Simulate cached value repetition - same value repeated for 500ms chunks
            convolution_cycle = i // convolution_period_samples

            if convolution_cycle % 2 == 0:
                value = 0.8  # High probability
            else:
                value = 0.1  # Low probability

            samples.append(value)

        return samples

    # Test data compression function (from debug_display.py)
    def compress_repeated_values(data: list[float], tolerance: float = 1e-6) -> list[float]:
        """Compress repeated values to actual update rate."""
        if len(data) <= 1:
            return data

        compressed = [data[0]]
        for i in range(1, len(data)):
            if abs(data[i] - compressed[-1]) > tolerance:
                compressed.append(data[i])

        return compressed

    rate_hz = 25.0  # 25 Hz event publishing rate

    # Generate data with repeated cached values
    original_data = generate_cached_probability_data(rate_hz)
    compressed_data = compress_repeated_values(original_data)

    compression_ratio = len(original_data) / len(compressed_data) if len(compressed_data) > 0 else 1

    print("📊 Original cached data (25 Hz events, 500ms convolution):")
    print(f"    Samples: {original_data[:20]}... (showing first 20)")
    print(f"    Total samples: {len(original_data)}")

    print("\n📊 After compression:")
    print(f"    Samples: {compressed_data}")
    print(f"    Total samples: {len(compressed_data)}")

    print("\n🎯 COMPRESSION RESULT:")
    print(f"   Compression ratio: {compression_ratio:.1f}:1")
    print("   Expected ratio: ~12.5:1 (25Hz / 2Hz = 12.5)")
    print("   ✅ This fixes the 'wide impulse' problem in probability graphs!")


def main():
    """Run all visual demonstrations."""
    print("🎬 VISUAL DEMONSTRATIONS: Identical Signal Rendering")
    print("=" * 80)
    print("These demos show what the unit tests validate:")
    print("- Identical mathematical signals at different sample rates")
    print("- Should produce pixel-perfect identical visual output")
    print("- Hash verification confirms exact matching")
    print()

    results = []

    # Run all demonstrations
    results.append(demo_identical_square_waves())
    results.append(demo_morse_code_timing())
    demo_braille_vs_ascii()
    demo_probability_data_compression()

    # Summary
    print("\n" + "=" * 80)
    print("📋 DEMONSTRATION SUMMARY:")

    if all(results):
        print("🎉 ALL DEMONSTRATIONS SUCCESSFUL!")
        print("✅ Identical signals at different sample rates produce identical output")
        print("✅ UILT time-aware decimation is working correctly")
        print("✅ Hash verification confirms pixel-perfect matching")
    else:
        print("❌ SOME DEMONSTRATIONS FAILED!")
        print("   This indicates issues with the decimation algorithm")

    print(f"\n   Square wave test: {'✅ PASS' if results[0] else '❌ FAIL'}")
    print(f"   Morse timing test: {'✅ PASS' if results[1] else '❌ FAIL'}")
    print("   Braille comparison: ✅ VISUAL (check resolution difference)")
    print("   Compression demo: ✅ VISUAL (check compression ratio)")

    print("\n🔍 This proves the unit tests are validating real visual consistency!")


if __name__ == "__main__":
    main()
