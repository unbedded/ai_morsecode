#!/usr/bin/env python3
"""Debug Braille left/right column mapping."""

import os
import sys

# Add src to path for util imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from util.graph import BrailleBackend, plot_signal_ascii


def debug_simple_ramp():
    """Debug simple ascending ramp to see column mapping."""
    print("🔍 Debug Simple Ramp Column Mapping\n")

    # Simple ascending ramp: 0, 1, 2, 3, 4, 5, 6, 7
    ramp_data = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
    print(f"Input data: {ramp_data}")

    # Test ASCII first (1 data point per character)
    print("\nASCII Backend (1 data point per character):")
    ascii_lines = plot_signal_ascii(ramp_data, width=8, height=3)
    for line in ascii_lines:
        print(line)

    # Test Braille (2 data points per character)
    print("\nBraille Backend (2 data points per character):")
    backend = BrailleBackend(width=4, height=3)  # 4 chars = 8 data points
    backend.plot(ramp_data)

    result = backend.render_braille()
    for i, row in enumerate(result):
        print(f"Row {i}: {row}")

    print("\nExpected: Braille should show smooth ascending pattern")
    print("If columns are swapped, we'd see odd discontinuities")


def debug_alternating_pattern():
    """Debug alternating pattern to clearly see left/right mapping."""
    print("\n🔍 Debug Alternating Pattern\n")

    # Alternating pattern: low, high, low, high, low, high
    alternating = [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0]
    print(f"Input data: {alternating}")

    # ASCII version
    print("\nASCII Backend:")
    ascii_lines = plot_signal_ascii(alternating, width=8, height=3)
    for line in ascii_lines:
        print(line)

    # Braille version
    print("\nBraille Backend:")
    backend = BrailleBackend(width=4, height=3)
    backend.plot(alternating)

    result = backend.render_braille()
    for i, row in enumerate(result):
        print(f"Row {i}: {row}")

    print("\nExpected: Should show alternating high/low pattern")
    print("If columns are swapped, pattern will be wrong")


def debug_step_pairs():
    """Debug step pairs to see exact column assignment."""
    print("\n🔍 Debug Step Pairs Column Assignment\n")

    # Pairs: (0,1), (2,3), (4,5), (6,7)
    # Left column should get: 0, 2, 4, 6
    # Right column should get: 1, 3, 5, 7
    step_pairs = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
    print(f"Input data: {step_pairs}")
    print("Expected assignment:")
    print("  Character 0: left=0.0, right=1.0")
    print("  Character 1: left=2.0, right=3.0")
    print("  Character 2: left=4.0, right=5.0")
    print("  Character 3: left=6.0, right=7.0")

    backend = BrailleBackend(width=4, height=4)
    backend.plot(step_pairs)

    result = backend.render_braille()
    print("\nBraille output:")
    for i, row in enumerate(result):
        print(f"Row {i}: {row}")

    # Manual verification
    print("\nManual verification - Character by character:")
    for i, char in enumerate(result[0]):  # Just check bottom row
        print(f"Character {i}: '{char}' (Unicode: U+{ord(char):04X})")


if __name__ == "__main__":
    debug_simple_ramp()
    debug_alternating_pattern()
    debug_step_pairs()
