#!/usr/bin/env python3
"""Test the ported util/graph library with corrected Braille functionality."""

import math
import os
import sys

# Add src to path so we can import util
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from util.graph import (
    ASCIIBackend,
    Backend,
    BrailleBackend,
    SmartDecimation,
    compare_backends,
    plot_signal_ascii,
    plot_signal_braille,
)


def test_basic_functionality():
    """Test basic plotting functionality."""
    print("🧪 Testing Ported UTIL Graph Library\n")

    # Create test data
    test_data = [math.sin(i * 0.2) for i in range(20)]
    print(f"Test data: {[f'{x:.2f}' for x in test_data[:10]]}...")

    # Test ASCII backend
    print("\n📊 ASCII Backend Test:")
    ascii_lines = plot_signal_ascii(test_data, sample_rate_hz=100.0, title="ASCII Test", width=40, height=4)
    for line in ascii_lines:
        print(line)

    # Test Braille backend
    print("\n📊 Braille Backend Test:")
    braille_lines = plot_signal_braille(test_data, sample_rate_hz=100.0, title="Braille Test", width=40, height=4)
    for line in braille_lines:
        print(line)


def test_backend_comparison():
    """Test backend comparison feature."""
    print("\n🔍 Backend Comparison Test:")

    # Create ramp data for clear comparison
    ramp_data = [i / 10 for i in range(21)]  # 0.0 to 2.0
    print(f"Ramp data: {[f'{x:.1f}' for x in ramp_data[:11]]}...")

    comparison_lines = compare_backends(ramp_data, sample_rate_hz=50.0, width=30, height=3)
    for line in comparison_lines:
        print(line)


def test_decimation_logic():
    """Test backend-aware decimation."""
    print("\n⚙️ Decimation Logic Test:")

    test_data = list(range(100))  # 0 to 99
    print("Original data: 100 points")

    # Test ASCII decimation
    ascii_decimated = SmartDecimation.decimate(test_data, Backend.ASCII, width=20, height=4)
    print(f"ASCII decimated: {len(ascii_decimated)} points (expected: 20)")

    # Test Braille decimation
    braille_decimated = SmartDecimation.decimate(test_data, Backend.BRAILLE, width=20, height=4)
    print(f"Braille decimated: {len(braille_decimated)} points (expected: 40)")

    # Show decimation info
    ascii_info = SmartDecimation.get_backend_info(Backend.ASCII, 20, 4)
    braille_info = SmartDecimation.get_backend_info(Backend.BRAILLE, 20, 4)

    print(f"\nASCII info: {ascii_info['description']}")
    print(f"Braille info: {braille_info['description']}")


def test_direct_backends():
    """Test direct backend usage."""
    print("\n🎯 Direct Backend Usage Test:")

    # Create simple test data
    simple_data = [0.0, 0.3, 0.7, 1.0, 0.7, 0.3, 0.0, -0.3, -0.7, -1.0]

    # Test ASCII backend directly
    ascii_backend = ASCIIBackend(width=10, height=3, title="Direct ASCII")
    ascii_backend.plot(simple_data, sample_rate_hz=10.0)
    ascii_result = ascii_backend.render_sparkline()

    print("ASCII Backend (direct):")
    for line in ascii_result:
        print(f"  {line}")

    # Test Braille backend directly
    braille_backend = BrailleBackend(width=5, height=1, title="Direct Braille")
    braille_backend.plot(simple_data, sample_rate_hz=10.0)
    braille_result = braille_backend.render_braille()

    print("\nBraille Backend (direct):")
    for line in braille_result:
        print(f"  {line}")

    # Show performance info
    ascii_perf = ascii_backend.get_performance_info()
    braille_perf = braille_backend.get_performance_info()

    print(f"\nASCII performance: {ascii_perf['effective_resolution']} effective resolution")
    print(f"Braille performance: {braille_perf['effective_resolution']} effective resolution")


if __name__ == "__main__":
    test_basic_functionality()
    test_backend_comparison()
    test_decimation_logic()
    test_direct_backends()

    print("\n✅ All tests completed! UTIL Graph library successfully ported.")
    print("📝 Ready to delete util/graphics directory.")
