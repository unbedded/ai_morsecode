#!/usr/bin/env python3
"""Basic usage examples for the UILT graphing library.

This example demonstrates the fundamental capabilities of the Universal Interface
for Live Telemetry (UILT) library with both ASCII and Braille backends.
"""

import math
import sys
import os
import time

# Add src to path for util imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from util.graph import (
    plot_signal_ascii,
    plot_signal_braille,
    plot_signal_auto,
    compare_backends,
    ASCIIBackend,
    BrailleBackend,
)


def example_1_quick_plotting():
    """Example 1: Quick signal plotting with convenience functions."""
    print("📊 Example 1: Quick Signal Plotting\n")

    # Generate a test signal - damped sine wave
    sample_rate_hz = 1000.0
    duration_sec = 0.1  # 100ms of data
    num_samples = int(sample_rate_hz * duration_sec)

    signal = []
    for i in range(num_samples):
        t = i / sample_rate_hz
        # Damped sine wave with some noise
        amplitude = math.exp(-t * 10)  # Exponential decay
        sine_wave = math.sin(2 * math.pi * 50 * t)  # 50 Hz sine
        noise = 0.1 * math.sin(2 * math.pi * 200 * t)  # High-frequency noise
        signal.append(amplitude * sine_wave + noise)

    print(f"Generated {len(signal)} samples at {sample_rate_hz} Hz\n")

    # ASCII plot
    print("ASCII Backend:")
    ascii_lines = plot_signal_ascii(
        signal,
        sample_rate_hz=sample_rate_hz,
        title="Damped Sine Wave",
        width=60,
        height=6
    )
    for line in ascii_lines:
        print(line)

    print("\nBraille Backend (2x horizontal resolution):")
    braille_lines = plot_signal_braille(
        signal,
        sample_rate_hz=sample_rate_hz,
        title="Damped Sine Wave",
        width=60,
        height=4
    )
    for line in braille_lines:
        print(line)


def example_2_auto_backend_selection():
    """Example 2: Automatic backend selection based on terminal capabilities."""
    print("\n📊 Example 2: Auto Backend Selection\n")

    # Generate frequency sweep signal
    sample_rate_hz = 500.0
    duration_sec = 0.2  # 200ms
    num_samples = int(sample_rate_hz * duration_sec)

    sweep_signal = []
    for i in range(num_samples):
        t = i / sample_rate_hz
        # Frequency sweep from 10 Hz to 100 Hz
        freq = 10 + (100 - 10) * (t / duration_sec)
        sweep_signal.append(math.sin(2 * math.pi * freq * t))

    # Auto-select best backend
    lines, backend_used = plot_signal_auto(
        sweep_signal,
        sample_rate_hz=sample_rate_hz,
        title="Frequency Sweep",
        width=50,
        height=5,
        prefer_braille=True
    )

    print(f"Auto-selected backend: {backend_used}")
    print("Frequency sweep (10-100 Hz):")
    for line in lines:
        print(line)


def example_3_backend_comparison():
    """Example 3: Side-by-side backend comparison."""
    print("\n📊 Example 3: Backend Comparison\n")

    # Generate high-frequency signal to show resolution advantage
    sample_rate_hz = 2000.0
    duration_sec = 0.05  # 50ms - short burst
    num_samples = int(sample_rate_hz * duration_sec)

    high_freq_signal = []
    for i in range(num_samples):
        t = i / sample_rate_hz
        # Multiple frequency components
        fundamental = math.sin(2 * math.pi * 100 * t)
        harmonic1 = 0.5 * math.sin(2 * math.pi * 300 * t)
        harmonic2 = 0.3 * math.sin(2 * math.pi * 500 * t)
        high_freq_signal.append(fundamental + harmonic1 + harmonic2)

    comparison_lines = compare_backends(
        high_freq_signal,
        sample_rate_hz=sample_rate_hz,
        title="High-Frequency Signal Comparison",
        width=35,
        height=4
    )

    for line in comparison_lines:
        print(line)

    print("\n💡 Notice: Braille backend shows more detail due to 2x horizontal resolution")


def example_4_direct_backend_usage():
    """Example 4: Direct backend usage with configuration."""
    print("\n📊 Example 4: Direct Backend Usage\n")

    # Generate step signal to test different configurations
    step_signal = []
    steps = [0.0, 0.2, 0.8, 1.0, 0.6, -0.2, -0.8, -0.5, 0.1, 0.9]
    for step_value in steps:
        step_signal.extend([step_value] * 10)  # Hold each step for 10 samples

    print("Step Signal with Manual Y-limits:")

    # ASCII backend with manual scaling
    ascii_backend = ASCIIBackend(width=40, height=5, title="ASCII Step Response")
    ascii_backend.set_ylim(-1.0, 1.0)  # Manual Y-axis limits
    ascii_backend.plot(step_signal, sample_rate_hz=100.0)
    ascii_result = ascii_backend.render_sparkline()

    for line in ascii_result:
        print(line)

    print("\nBraille backend with auto-scaling:")

    # Braille backend with auto-scaling
    braille_backend = BrailleBackend(width=40, height=3, title="Braille Step Response")
    # Auto-scaling is enabled by default
    braille_backend.plot(step_signal, sample_rate_hz=100.0)
    braille_result = braille_backend.render_braille()

    for line in braille_result:
        print(line)

    # Show performance info
    ascii_perf = ascii_backend.get_performance_info()
    braille_perf = braille_backend.get_performance_info()

    print(f"\nPerformance Info:")
    print(f"ASCII effective resolution: {ascii_perf['effective_resolution']} points")
    print(f"Braille effective resolution: {braille_perf['effective_resolution']} points")
    print(f"Braille advantage: {braille_perf['effective_resolution'] / ascii_perf['effective_resolution']:.1f}x")


def example_5_signal_analysis():
    """Example 5: Signal analysis use case - FFT-like magnitude display."""
    print("\n📊 Example 5: Signal Analysis - Magnitude Spectrum\n")

    # Simulate FFT magnitude spectrum
    frequencies = [i * 10 for i in range(1, 21)]  # 10 Hz to 200 Hz
    magnitudes = []

    for freq in frequencies:
        # Simulate realistic spectrum with peaks at certain frequencies
        if freq in [50, 100, 150]:  # Strong peaks
            magnitude = 0.8 + 0.2 * math.sin(freq * 0.1)
        elif freq in [70, 130]:  # Medium peaks
            magnitude = 0.4 + 0.1 * math.cos(freq * 0.05)
        else:  # Background noise
            magnitude = 0.1 + 0.05 * math.sin(freq * 0.02)

        magnitudes.append(magnitude)

    print("Simulated FFT Magnitude Spectrum:")
    print("ASCII representation:")

    # Use ASCII for universal compatibility
    spectrum_lines = plot_signal_ascii(
        magnitudes,
        title="FFT Magnitude Spectrum",
        width=60,
        height=6
    )

    for line in spectrum_lines:
        print(line)

    print(f"\nFrequency range: {frequencies[0]} - {frequencies[-1]} Hz")
    print(f"Peak frequencies: 50, 100, 150 Hz")


def main():
    """Run all examples in sequence."""
    print("🎯 UILT Library Examples - Universal Interface for Live Telemetry\n")
    print("=" * 70)

    try:
        example_1_quick_plotting()
        time.sleep(1)  # Pause between examples

        example_2_auto_backend_selection()
        time.sleep(1)

        example_3_backend_comparison()
        time.sleep(1)

        example_4_direct_backend_usage()
        time.sleep(1)

        example_5_signal_analysis()

        print("\n" + "=" * 70)
        print("✅ All examples completed successfully!")
        print("\n🚀 The UILT library is ready for your signal visualization needs!")
        print("   - SSH-friendly real-time plotting")
        print("   - Backend-aware decimation")
        print("   - 2x resolution with Braille")
        print("   - Matplotlib-like interface")

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        print("   Make sure you're running from the correct directory")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())