#!/usr/bin/env python3
"""Debug decimation differences between backends."""

import math
import os
import sys

# Add src to path for util imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from util.graph.utils.decimation import Backend, SmartDecimation


def debug_decimation_differences():
    """Debug how decimation differs between ASCII and Braille."""
    print("🔍 Debug Decimation Differences\n")

    # Generate the same high-frequency signal as in the comparison
    sample_rate_hz = 2000.0
    duration_sec = 0.05
    num_samples = int(sample_rate_hz * duration_sec)

    high_freq_signal = []
    for i in range(num_samples):
        t = i / sample_rate_hz
        fundamental = math.sin(2 * math.pi * 100 * t)
        harmonic1 = 0.5 * math.sin(2 * math.pi * 300 * t)
        harmonic2 = 0.3 * math.sin(2 * math.pi * 500 * t)
        high_freq_signal.append(fundamental + harmonic1 + harmonic2)

    print(f"Original signal: {len(high_freq_signal)} samples")
    print(f"First 10 values: {[round(x, 3) for x in high_freq_signal[:10]]}")

    # Test decimation for ASCII backend (35 characters = 35 data points)
    ascii_decimated = SmartDecimation.decimate(high_freq_signal, Backend.ASCII, 35, 4)
    print(f"\nASCII decimated: {len(ascii_decimated)} samples")
    print(f"First 10 values: {[round(x, 3) for x in ascii_decimated[:10]]}")

    # Test decimation for Braille backend (35 characters = 70 data points)
    braille_decimated = SmartDecimation.decimate(high_freq_signal, Backend.BRAILLE, 35, 4)
    print(f"\nBraille decimated: {len(braille_decimated)} samples")
    print(f"First 10 values: {[round(x, 3) for x in braille_decimated[:10]]}")

    # Compare effective resolutions
    ascii_res = SmartDecimation.calculate_effective_resolution(Backend.ASCII, 35, 4)
    braille_res = SmartDecimation.calculate_effective_resolution(Backend.BRAILLE, 35, 4)
    print(f"\nASCII effective resolution: {ascii_res}")
    print(f"Braille effective resolution: {braille_res}")

    # Show data reduction ratios
    ascii_ratio = len(high_freq_signal) / len(ascii_decimated)
    braille_ratio = len(high_freq_signal) / len(braille_decimated)
    print(f"\nASCII reduction ratio: {ascii_ratio:.1f}:1")
    print(f"Braille reduction ratio: {braille_ratio:.1f}:1")


if __name__ == "__main__":
    debug_decimation_differences()
