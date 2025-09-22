#!/usr/bin/env python3
"""Debug Braille character pairs."""

import os
import sys

# Add src to path for util imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from util.graph import BrailleBackend


def debug_braille_pairs():
    """Debug what characters we get for specific left/right combinations."""
    print("🔍 Debug Braille Character Pairs\n")

    backend = BrailleBackend(width=1, height=1)

    # Test the combinations we found in the debug
    test_pairs = [
        (1, 2, "should be first char: 1 left, 2 right"),
        (3, 4, "should be second char: 3 left, 4 right"),
        (3, 1, "should be third char: 3 left, 1 right"),
        (0, 0, "should be fourth char: 0 left, 0 right"),
        (2, 3, "should be fifth char: 2 left, 3 right"),
    ]

    for left_dots, right_dots, desc in test_pairs:
        char = backend._positive_lookup.get((left_dots, right_dots), "?")
        print(f"  ({left_dots},{right_dots}): {char} - {desc}")

    print("\nActual result was: ⠙⢿⠏⠀⠻")
    print("Let's find what combinations give these characters:")

    # Reverse lookup to see what gives us these characters
    target_chars = ["⠙", "⢿", "⠏", "⠀", "⠻"]

    print("\nReverse lookup:")
    for target_char in target_chars:
        for left in range(5):
            for right in range(5):
                if backend._positive_lookup.get((left, right)) == target_char:
                    print(f"  {target_char} = ({left},{right})")
                    break

    # Let's manually check the expected vs actual for our step signal
    print("\nStep signal analysis:")
    step_signal = [0.0, 0.2, 0.8, 1.0, 0.6, -0.2, -0.8, -0.5, 0.1, 0.9]
    print(f"Values: {step_signal}")

    # Simulate the pairing logic
    print("\nExpected character pairs:")
    for i in range(5):  # 5 characters for 10 values
        left_idx = i * 2
        right_idx = i * 2 + 1
        left_val = step_signal[left_idx]
        right_val = step_signal[right_idx]

        # Normalize like the backend does
        y_min, y_max = -0.8, 1.0
        y_range = y_max - y_min

        left_norm = max(0.0, min(1.0, (left_val - y_min) / y_range))
        right_norm = max(0.0, min(1.0, (right_val - y_min) / y_range))

        left_dots = int(left_norm * 4)
        right_dots = int(right_norm * 4)

        expected_char = backend._positive_lookup.get((left_dots, right_dots), "?")

        print(f"  Char {i}: L={left_val:4.1f}({left_dots}) R={right_val:4.1f}({right_dots}) → {expected_char}")


if __name__ == "__main__":
    debug_braille_pairs()
