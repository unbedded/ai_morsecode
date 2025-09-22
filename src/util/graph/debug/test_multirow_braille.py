#!/usr/bin/env python3
"""Test multi-row Braille rendering."""

import math
import os
import sys

# Add src to path for util imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from util.graph import BrailleBackend


def test_multirow_simple():
    """Test multi-row with simple step signal."""
    print("🧪 Multi-row Braille Test\n")

    # Simple ascending values
    data = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 0.8, 0.6, 0.4, 0.2]
    print(f"Data: {data}")

    # Test with 5 rows
    backend = BrailleBackend(width=5, height=5)
    backend.plot(data)

    result = backend.render_braille()
    print("\n5-row Braille output:")
    for i, row in enumerate(result):
        print(f"Row {i}: {row}")

    print("\nExpected: Should show mountain pattern across 5 rows")


def test_multirow_sine():
    """Test multi-row with sine wave."""
    print("\n🌊 Multi-row Sine Wave Test\n")

    # Generate sine wave
    sine_data = [math.sin(i * 0.3) for i in range(20)]
    print("Sine wave: 20 samples")

    # Test with 5 rows for better resolution
    backend = BrailleBackend(width=10, height=5)
    backend.plot(sine_data, sample_rate_hz=10.0)

    result = backend.render_braille()
    print("\n5-row sine wave:")
    for i, row in enumerate(result):
        print(f"Row {i}: {row}")

    print("\nExpected: Should show smooth sine curve across multiple rows")


if __name__ == "__main__":
    test_multirow_simple()
    test_multirow_sine()
