#!/usr/bin/env python3
"""Debug specific column patterns."""

import os
import sys

# Add src to path for util imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from util.graph import BrailleBackend, plot_signal_ascii


def debug_true_alternating():
    """Debug true alternating pattern across time."""
    print("🔍 Debug True Time-based Alternating Pattern\n")

    # True chronological alternating: 0, 1, 0, 1, 0, 1, 0, 1
    # For ASCII (1 point per char): should show alternating bars
    # For Braille (2 points per char): Character 0 should show (0,1), Char 1 should show (0,1), etc.
    alternating = [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0]
    print(f"Input data: {alternating}")

    # ASCII version (8 characters, each gets 1 data point)
    print("\nASCII Backend (8 chars, 1 point each):")
    ascii_lines = plot_signal_ascii(alternating, width=8, height=3)
    for line in ascii_lines:
        print(line)
    print("Expected: ⬜⬛⬜⬛⬜⬛⬜⬛ (alternating pattern)")

    # Braille version (4 characters, each gets 2 data points)
    print("\nBraille Backend (4 chars, 2 points each):")
    backend = BrailleBackend(width=4, height=3)
    backend.plot(alternating)
    result = backend.render_braille()
    for i, row in enumerate(result):
        print(f"Row {i}: {row}")
    print("Expected: All chars should be identical since each gets (0.0, 1.0)")


def debug_progressive_pairs():
    """Debug progressive pairs to see clear left/right distinction."""
    print("\n🔍 Debug Progressive Pairs\n")

    # Progressive pairs: (0,1), (1,2), (2,3), (3,4)
    # This should show different patterns for each character
    progressive = [0.0, 1.0, 1.0, 2.0, 2.0, 3.0, 3.0, 4.0]
    print(f"Input data: {progressive}")
    print("Expected Braille assignments:")
    print("  Char 0: left=0.0, right=1.0")
    print("  Char 1: left=1.0, right=2.0")
    print("  Char 2: left=2.0, right=3.0")
    print("  Char 3: left=3.0, right=4.0")

    # ASCII version
    print("\nASCII Backend:")
    ascii_lines = plot_signal_ascii(progressive, width=8, height=4)
    for line in ascii_lines:
        print(line)

    # Braille version
    print("\nBraille Backend:")
    backend = BrailleBackend(width=4, height=4)
    backend.plot(progressive)
    result = backend.render_braille()
    for i, row in enumerate(result):
        print(f"Row {i}: {row}")

    print("\nShould show DIFFERENT patterns for each character")


def debug_left_vs_right():
    """Debug pure left vs right column patterns."""
    print("\n🔍 Debug Pure Left vs Right Columns\n")

    # Pattern designed to isolate left vs right
    # Left high, right low: (1,0), (1,0), (1,0), (1,0)
    left_high = [1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0]
    print(f"Left-high pattern: {left_high}")
    print("Expected: left column full, right column empty")

    backend = BrailleBackend(width=4, height=3)
    backend.plot(left_high)
    result = backend.render_braille()
    print("Braille result:")
    for i, row in enumerate(result):
        print(f"Row {i}: {row}")

    # Right high, left low: (0,1), (0,1), (0,1), (0,1)
    right_high = [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0]
    print(f"\nRight-high pattern: {right_high}")
    print("Expected: left column empty, right column full")

    backend.clear()
    backend.plot(right_high)
    result = backend.render_braille()
    print("Braille result:")
    for i, row in enumerate(result):
        print(f"Row {i}: {row}")


if __name__ == "__main__":
    debug_true_alternating()
    debug_progressive_pairs()
    debug_left_vs_right()
