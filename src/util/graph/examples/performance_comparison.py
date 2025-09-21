#!/usr/bin/env python3
"""Performance comparison examples for UILT library.

This example demonstrates the performance characteristics and advantages
of backend-aware decimation in the UILT library.
"""

import math
import sys
import os
import time
from typing import List

# Add src to path for util imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from util.graph import (
    ASCIIBackend,
    BrailleBackend,
    SmartDecimation,
    Backend,
    plot_signal_ascii,
    plot_signal_braille,
)


def generate_test_signal(num_samples: int, signal_type: str = "mixed") -> List[float]:
    """Generate test signals of various types for performance testing."""
    signal = []

    for i in range(num_samples):
        t = i / 1000.0  # 1kHz sample rate

        if signal_type == "sine":
            sample = math.sin(2 * math.pi * 50 * t)
        elif signal_type == "mixed":
            # Mixed frequency content
            sample = (
                math.sin(2 * math.pi * 25 * t) +
                0.5 * math.sin(2 * math.pi * 75 * t) +
                0.3 * math.sin(2 * math.pi * 150 * t) +
                0.1 * math.sin(2 * math.pi * 300 * t)
            )
        elif signal_type == "impulse":
            # Impulse train
            sample = 1.0 if i % 100 == 0 else 0.0
        elif signal_type == "noise":
            # Pseudo-random noise
            sample = math.sin(i * 0.1) + 0.5 * math.sin(i * 0.13) + 0.3 * math.sin(i * 0.17)
        else:
            sample = 0.0

        signal.append(sample)

    return signal


def benchmark_decimation_performance():
    """Benchmark decimation performance for different data sizes."""
    print("⚡ Decimation Performance Benchmark")
    print("=" * 45)

    data_sizes = [100, 500, 1000, 5000, 10000]
    display_width = 80
    display_height = 6

    print(f"{'Data Size':<10} {'ASCII Time':<12} {'Braille Time':<14} {'Speedup':<8}")
    print("-" * 50)

    for size in data_sizes:
        test_data = generate_test_signal(size, "mixed")

        # Benchmark ASCII decimation
        start_time = time.perf_counter()
        for _ in range(100):  # Multiple runs for accurate timing
            SmartDecimation.decimate(test_data, Backend.ASCII, display_width, display_height)
        ascii_time = (time.perf_counter() - start_time) / 100

        # Benchmark Braille decimation
        start_time = time.perf_counter()
        for _ in range(100):  # Multiple runs for accurate timing
            SmartDecimation.decimate(test_data, Backend.BRAILLE, display_width, display_height)
        braille_time = (time.perf_counter() - start_time) / 100

        speedup = ascii_time / braille_time if braille_time > 0 else float('inf')

        print(f"{size:<10} {ascii_time*1000:<8.3f} ms  {braille_time*1000:<10.3f} ms  {speedup:<6.2f}x")

    print("\n💡 Note: Times may vary based on data characteristics and hardware")


def demonstrate_resolution_advantage():
    """Demonstrate the resolution advantage of Braille backend."""
    print("\n🔍 Resolution Advantage Demonstration")
    print("=" * 42)

    # Generate high-frequency signal with sharp transitions
    sample_rate = 2000.0
    duration = 0.1  # 100ms
    num_samples = int(sample_rate * duration)

    high_freq_signal = []
    for i in range(num_samples):
        t = i / sample_rate
        # Sharp square wave with high frequency components
        fundamental = 1.0 if math.sin(2 * math.pi * 25 * t) > 0 else -1.0
        noise = 0.2 * math.sin(2 * math.pi * 200 * t)
        high_freq_signal.append(fundamental + noise)

    print(f"Test signal: {num_samples} samples at {sample_rate} Hz")
    print(f"Contains: 25 Hz square wave + 200 Hz noise component\n")

    display_width = 40

    # Show decimation information
    ascii_resolution = SmartDecimation.calculate_effective_resolution(Backend.ASCII, display_width, 4)
    braille_resolution = SmartDecimation.calculate_effective_resolution(Backend.BRAILLE, display_width, 4)

    print(f"Display width: {display_width} characters")
    print(f"ASCII effective resolution: {ascii_resolution} data points")
    print(f"Braille effective resolution: {braille_resolution} data points")
    print(f"Braille advantage: {braille_resolution / ascii_resolution:.1f}x more data points\n")

    # ASCII rendering
    print("ASCII Backend (lower resolution):")
    ascii_backend = ASCIIBackend(display_width, 4, "ASCII")
    ascii_backend.plot(high_freq_signal, sample_rate_hz=sample_rate)
    ascii_result = ascii_backend.render_sparkline()
    for line in ascii_result:
        print(line)

    print("\nBraille Backend (2x resolution):")
    braille_backend = BrailleBackend(display_width, 3, "Braille")
    braille_backend.plot(high_freq_signal, sample_rate_hz=sample_rate)
    braille_result = braille_backend.render_braille()
    for line in braille_result:
        print(line)

    print("\n💡 Braille shows more timing detail and transitions")


def analyze_decimation_quality():
    """Analyze how well different decimation preserves signal characteristics."""
    print("\n📈 Decimation Quality Analysis")
    print("=" * 32)

    # Test signals with different characteristics
    test_cases = [
        ("Smooth sine", "sine"),
        ("Sharp impulses", "impulse"),
        ("Mixed frequencies", "mixed"),
        ("Broadband noise", "noise"),
    ]

    for signal_name, signal_type in test_cases:
        print(f"\n{signal_name}:")
        print("-" * len(signal_name))

        # Generate test signal
        original_data = generate_test_signal(400, signal_type)
        display_width = 20

        # Apply decimation
        ascii_decimated = SmartDecimation.decimate(original_data, Backend.ASCII, display_width, 4)
        braille_decimated = SmartDecimation.decimate(original_data, Backend.BRAILLE, display_width, 4)

        # Show decimation ratios
        ascii_ratio = len(original_data) / len(ascii_decimated)
        braille_ratio = len(original_data) / len(braille_decimated)

        print(f"Original samples: {len(original_data)}")
        print(f"ASCII decimated: {len(ascii_decimated)} (ratio: {ascii_ratio:.1f}:1)")
        print(f"Braille decimated: {len(braille_decimated)} (ratio: {braille_ratio:.1f}:1)")

        # Calculate signal preservation metrics
        def signal_energy(data):
            return sum(x*x for x in data) / len(data)

        def peak_preservation(original, decimated):
            orig_max = max(abs(x) for x in original)
            dec_max = max(abs(x) for x in decimated) if decimated else 0
            return dec_max / orig_max if orig_max > 0 else 0

        ascii_energy = signal_energy(ascii_decimated)
        braille_energy = signal_energy(braille_decimated)
        original_energy = signal_energy(original_data)

        ascii_peak = peak_preservation(original_data, ascii_decimated)
        braille_peak = peak_preservation(original_data, braille_decimated)

        print(f"Energy preservation - ASCII: {ascii_energy/original_energy:.3f}, Braille: {braille_energy/original_energy:.3f}")
        print(f"Peak preservation - ASCII: {ascii_peak:.3f}, Braille: {braille_peak:.3f}")


def demonstrate_ssh_use_case():
    """Demonstrate typical SSH debugging use case."""
    print("\n🖥️  SSH Debugging Use Case")
    print("=" * 28)

    print("Scenario: Remote debugging of morse code decoder over SSH")
    print("Need: Real-time signal visualization with limited bandwidth\n")

    # Simulate typical morse code analysis scenario
    sample_rate = 1000.0  # 1 kHz audio sampling
    duration = 0.5  # 500ms of audio
    num_samples = int(sample_rate * duration)

    # Generate morse code-like signal
    morse_signal = []
    for i in range(num_samples):
        t = i / sample_rate
        # Simulate morse code with noise
        if (0.0 <= t < 0.1) or (0.15 <= t < 0.25) or (0.3 <= t < 0.4):  # Dots and dashes
            carrier = math.sin(2 * math.pi * 800 * t)  # 800 Hz carrier
            envelope = 1.0
        else:
            carrier = 0.0
            envelope = 0.0

        # Add noise and filtering artifacts
        noise = 0.1 * math.sin(2 * math.pi * 50 * t)  # 50 Hz hum
        high_freq = 0.05 * math.sin(2 * math.pi * 2000 * t)  # High frequency artifacts

        morse_signal.append(envelope * carrier + noise + high_freq)

    print(f"Signal characteristics:")
    print(f"  • Sample rate: {sample_rate} Hz")
    print(f"  • Duration: {duration*1000} ms")
    print(f"  • Samples: {num_samples}")
    print(f"  • Contains: Morse code + noise + artifacts\n")

    # Show terminal compatibility
    terminal_width = 60
    print(f"Terminal width: {terminal_width} characters")

    ascii_res = SmartDecimation.calculate_effective_resolution(Backend.ASCII, terminal_width, 5)
    braille_res = SmartDecimation.calculate_effective_resolution(Backend.BRAILLE, terminal_width, 5)

    print(f"ASCII mode: {ascii_res} time points ({sample_rate/ascii_res:.1f} samples per point)")
    print(f"Braille mode: {braille_res} time points ({sample_rate/braille_res:.1f} samples per point)")
    print(f"Time resolution improvement: {braille_res/ascii_res:.1f}x\n")

    # ASCII display
    print("ASCII mode (standard SSH compatibility):")
    ascii_lines = plot_signal_ascii(morse_signal, sample_rate_hz=sample_rate, width=terminal_width, height=4)
    for line in ascii_lines:
        print(line)

    print("\nBraille mode (UTF-8 SSH terminals):")
    braille_lines = plot_signal_braille(morse_signal, sample_rate_hz=sample_rate, width=terminal_width, height=3)
    for line in braille_lines:
        print(line)

    print("\n💡 Braille mode shows timing details critical for morse code analysis")
    print("   Better resolution helps identify dot vs dash timing")


def main():
    """Run all performance comparison examples."""
    print("📊 UILT Performance Analysis & Comparison\n")

    try:
        benchmark_decimation_performance()
        demonstrate_resolution_advantage()
        analyze_decimation_quality()
        demonstrate_ssh_use_case()

        print("\n" + "=" * 60)
        print("✅ Performance analysis completed!")
        print("\n🎯 Key Performance Insights:")
        print("   • Backend-aware decimation optimizes for each output format")
        print("   • Braille provides 2x horizontal resolution advantage")
        print("   • Smart decimation preserves signal characteristics")
        print("   • Perfect for real-time SSH debugging scenarios")
        print("   • Scales efficiently with large datasets")

    except Exception as e:
        print(f"\n❌ Error in performance analysis: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())