#!/usr/bin/env python3
"""Fix Braille mapping by understanding actual dot positions."""


def create_correct_braille_lookup():
    """Create correct Braille lookup based on actual dot positions.

    Braille dots are numbered:
    1 • • 4
    2 • • 5
    3 • • 6
    7 • • 8

    For POSITIVE values (higher values = more dots from TOP):
    - 1 dot: top dot (dot 1)
    - 2 dots: top 2 dots (dots 1,2)
    - 3 dots: top 3 dots (dots 1,2,3)
    - 4 dots: all 4 dots (dots 1,2,3,7)
    """
    # Base Braille Unicode is U+2800 (⠀)
    # Each dot adds a specific value:
    # dot 1 = +1, dot 2 = +2, dot 3 = +4, dot 4 = +8
    # dot 5 = +16, dot 6 = +32, dot 7 = +64, dot 8 = +128

    def make_braille(dots):
        """Create Braille character from list of dot numbers (1-8)."""
        base = 0x2800
        dot_values = {1: 1, 2: 2, 3: 4, 4: 8, 5: 16, 6: 32, 7: 64, 8: 128}

        for dot in dots:
            if dot in dot_values:
                base += dot_values[dot]

        return chr(base)

    print("🧪 Testing correct Braille dot patterns\n")

    # Test left column progression (positive - fill from top)
    print("Left column positive (fill from top):")
    left_patterns = [
        ([], "0 dots"),
        ([1], "1 dot (top)"),
        ([1, 2], "2 dots (top)"),
        ([1, 2, 3], "3 dots (top)"),
        ([1, 2, 3, 7], "4 dots (all)"),
    ]

    for dots, desc in left_patterns:
        char = make_braille(dots)
        print(f"  {desc}: {char}")

    # Test right column progression
    print("\nRight column positive (fill from top):")
    right_patterns = [
        ([], "0 dots"),
        ([4], "1 dot (top)"),
        ([4, 5], "2 dots (top)"),
        ([4, 5, 6], "3 dots (top)"),
        ([4, 5, 6, 8], "4 dots (all)"),
    ]

    for dots, desc in right_patterns:
        char = make_braille(dots)
        print(f"  {desc}: {char}")

    # Test combinations
    print("\nCombinations (left 2 dots + right 1 dot):")
    combo_char = make_braille([1, 2, 4])  # Left top 2 + right top 1
    print(f"  Left 2, Right 1: {combo_char}")

    print("\n🎯 These patterns should show clear progression from top!")


if __name__ == "__main__":
    create_correct_braille_lookup()
