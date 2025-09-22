#!/usr/bin/env python3
"""Debug simple Braille case."""

import os
import sys

# Add src to path for util imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from util.graph import BrailleBackend


def test_very_simple():
    """Test the simplest possible case."""
    print("🔍 Very Simple Braille Test\n")

    # Test just: 0.0, 1.0 (should be ⠀ and ⡇)
    simple_data = [0.0, 1.0]
    print(f"Data: {simple_data}")

    backend = BrailleBackend(width=1, height=1)
    backend.plot(simple_data)

    print(f"Y-range: {backend.y_min} to {backend.y_max}")

    result = backend.render_braille()
    print(f"Result: {result[0]}")

    # Check the lookup table directly
    print("\nDirect lookup check:")
    char_0_4 = backend._positive_lookup.get((0, 4), "?")
    char_4_0 = backend._positive_lookup.get((4, 0), "?")

    print(f"(0,4) → {char_0_4} (should be right column full)")
    print(f"(4,0) → {char_4_0} (should be left column full)")

    # Expected: 0.0 maps to 0 dots, 1.0 maps to 4 dots
    # So we should get (0,4) → right column only
    print("\nExpected: (0,4) which should show right column filled from top")


def test_single_column():
    """Test single column to see progression."""
    print("\n🧪 Single Column Test\n")

    # Test: 0.0, 0.25, 0.5, 0.75, 1.0 (one column only)
    progression = [0.0, 0.25, 0.5, 0.75, 1.0]
    print(f"Progression: {progression}")

    backend = BrailleBackend(width=3, height=1)  # Only using first 5 values
    backend.plot(progression)

    result = backend.render_braille()
    print(f"Result: {result[0]}")

    # Manually check what each pair should be
    print("\nManual calculation:")
    for i in range(3):
        left_val = progression[i * 2] if i * 2 < len(progression) else 0.0
        right_val = progression[i * 2 + 1] if i * 2 + 1 < len(progression) else 0.0

        left_dots = int(left_val * 4)
        right_dots = int(right_val * 4)

        expected_char = backend._positive_lookup.get((left_dots, right_dots), "?")
        print(f"  Pair {i}: ({left_val},{right_val}) → ({left_dots},{right_dots}) → {expected_char}")


if __name__ == "__main__":
    test_very_simple()
    test_single_column()
