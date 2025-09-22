#!/usr/bin/env python3
"""Test what the correct Braille orientation should be."""


def make_correct_braille_char(dots: int) -> str:
    """Make Braille char with correct orientation for ASCENDING values."""
    base = 0x2800  # ⠀
    dot_values = {1: 1, 2: 2, 3: 4, 4: 8, 5: 16, 6: 32, 7: 64, 8: 128}

    # For ASCENDING/POSITIVE values, fill from BOTTOM UP
    # Left column dots (bottom to top): 7, 3, 2, 1
    active_dots = []

    if dots >= 1:
        active_dots.append(7)  # Bottom dot first
    if dots >= 2:
        active_dots.append(3)  # Then middle-bottom
    if dots >= 3:
        active_dots.append(2)  # Then middle-top
    if dots >= 4:
        active_dots.append(1)  # Finally top

    for dot in active_dots:
        base += dot_values[dot]

    return chr(base)


def test_correct_progression():
    """Test what the correct progression should look like."""
    print("🎯 CORRECT Braille Progression for Ascending Values\n")

    print("For values going UP (0.0 → 1.0), dots should fill BOTTOM to TOP:")
    for i in range(5):
        char = make_correct_braille_char(i)
        print(f"  {i} dots: {char}")

    print("\nThis should look like a bar filling UP: ⠀ → ⡀ → ⡄ → ⡆ → ⡇")


if __name__ == "__main__":
    test_correct_progression()
