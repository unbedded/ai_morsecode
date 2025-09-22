#!/usr/bin/env python3
"""Test clean ascending pattern to verify Braille orientation."""

import os
import sys

# Add src to path for util imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from util.graph import BrailleBackend


def test_clean_ascending():
    """Test with clean ascending values."""
    print("🧪 Clean Ascending Pattern Test\n")

    # Clean ascending: 0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9
    ascending = [i * 0.1 for i in range(10)]
    print(f"Ascending: {ascending}")

    backend = BrailleBackend(width=5, height=1)
    backend.plot(ascending)

    result = backend.render_braille()
    print(f"Braille: {result[0]}")

    # Analyze each character
    print("\nCharacter analysis:")
    y_min, y_max = backend.y_min, backend.y_max
    y_range = y_max - y_min

    for i in range(5):
        left_val = ascending[i * 2]
        right_val = ascending[i * 2 + 1]

        left_norm = (left_val - y_min) / y_range
        right_norm = (right_val - y_min) / y_range

        left_dots = int(left_norm * 4)
        right_dots = int(right_norm * 4)

        char = backend._positive_lookup.get((left_dots, right_dots), "?")

        print(f"  Char {i}: L={left_val:.1f}({left_dots}) R={right_val:.1f}({right_dots}) → {char}")

    print("\nExpected progression: Should show increasing dot density!")


def test_simple_steps():
    """Test simple 0, 0.5, 1.0 pattern."""
    print("\n🎯 Simple Steps Test\n")

    # Simple: 0, 0.5, 1.0, 0.5, 0
    simple = [0.0, 0.5, 1.0, 0.5, 0.0]
    print(f"Simple pattern: {simple}")

    backend = BrailleBackend(width=3, height=1)  # 3 chars, but only using first 5 values
    backend.plot(simple)

    result = backend.render_braille()
    print(f"Braille: {result[0]}")

    # This should show a clear mountain pattern
    print("\nExpected: Should show mountain pattern ⠈⢿⠃ or similar")


if __name__ == "__main__":
    test_clean_ascending()
    test_simple_steps()
