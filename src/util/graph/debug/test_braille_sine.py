#!/usr/bin/env python3
"""Simple Braille sine wave scrolling test - sanity check for UILT design.

This script tests:
- Braille character rendering over SSH
- Real-time scrolling sine wave
- 4-row high-resolution display
- Terminal UTF-8 compatibility
"""

import asyncio
import math
import os
import sys
import time
from collections import deque

# Braille patterns - 2x4 dot matrix (8 dots total)
# Each character represents 8 possible dot combinations
BRAILLE_PATTERNS = [
    "⠀",
    "⠁",
    "⠂",
    "⠃",
    "⠄",
    "⠅",
    "⠆",
    "⠇",  # Bottom dots
    "⠈",
    "⠉",
    "⠊",
    "⠋",
    "⠌",
    "⠍",
    "⠎",
    "⠏",  # Bottom + middle
    "⠐",
    "⠑",
    "⠒",
    "⠓",
    "⠔",
    "⠕",
    "⠖",
    "⠗",  # Middle dots
    "⠘",
    "⠙",
    "⠚",
    "⠛",
    "⠜",
    "⠝",
    "⠞",
    "⠟",  # All combinations
    "⠠",
    "⠡",
    "⠢",
    "⠣",
    "⠤",
    "⠥",
    "⠦",
    "⠧",  # Top + bottom
    "⠨",
    "⠩",
    "⠪",
    "⠫",
    "⠬",
    "⠭",
    "⠮",
    "⠯",  # Complex patterns
    "⠰",
    "⠱",
    "⠲",
    "⠳",
    "⠴",
    "⠵",
    "⠶",
    "⠷",  # More patterns
    "⠸",
    "⠹",
    "⠺",
    "⠻",
    "⠼",
    "⠽",
    "⠾",
    "⠿",  # Full combinations
]


def test_terminal_capabilities():
    """Test if terminal supports UTF-8 and Braille characters."""
    print("🧪 Testing terminal capabilities...")

    # Check locale
    lang = os.environ.get("LANG", "")
    print(f"   LANG: {lang}")

    # Check if we're in SSH
    ssh = "SSH_CONNECTION" in os.environ
    print(f"   SSH: {'Yes' if ssh else 'No'}")

    # Test basic Braille rendering
    try:
        test_chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        print(f"   Braille test: {test_chars}")
        sys.stdout.flush()
        return True
    except UnicodeEncodeError as e:
        print(f"   ❌ Braille not supported: {e}")
        return False


def sine_wave_to_braille_rows(values, width=60, height=4):
    """Convert sine wave values to 4-row Braille display.

    Args:
        values: List of sine wave values (-1.0 to +1.0)
        width: Display width in characters
        height: Display height in rows (4 for this test)

    Returns:
        List of strings, one per row
    """
    if not values:
        return [" " * width for _ in range(height)]

    # Take the most recent values to fit width
    data = list(values)[-width:]

    # Pad with zeros if needed
    while len(data) < width:
        data.insert(0, 0.0)

    rows = []
    total_levels = height * 8  # 4 rows × 8 vertical levels per Braille char

    for row in range(height):
        row_chars = []

        for col in range(width):
            if col < len(data):
                # Convert sine value (-1 to +1) to level (0 to 31)
                sine_value = data[col]
                normalized = (sine_value + 1.0) / 2.0  # Map to 0-1
                level = int(normalized * (total_levels - 1))
                level = max(0, min(total_levels - 1, level))

                # Determine which row this level belongs to (top=0, bottom=3)
                target_row = 3 - (level // 8)  # Which row (3=bottom, 0=top)
                dot_level = level % 8  # Which dot pattern within row

                if row < target_row:
                    # Above the signal - empty
                    char = "⠀"  # Empty Braille
                elif row == target_row:
                    # Signal row - show appropriate dot pattern
                    # Simple mapping: use dot_level to index into patterns
                    char_index = min(dot_level * 8, len(BRAILLE_PATTERNS) - 1)
                    char = BRAILLE_PATTERNS[char_index]
                else:
                    # Below signal - filled
                    char = "⠿"  # Full Braille block
            else:
                char = "⠀"  # Empty for padding

            row_chars.append(char)

        rows.append("".join(row_chars))

    return rows


async def scrolling_sine_wave_demo(duration=30, frequency=0.5, width=60):
    """Demo scrolling sine wave in Braille for specified duration.

    Args:
        duration: How long to run in seconds
        frequency: Sine wave frequency (cycles per second)
        width: Display width in characters
    """
    print(f"\n🌊 Starting {duration}s Braille sine wave demo...")
    print(f"   Frequency: {frequency} Hz")
    print(f"   Width: {width} chars × 4 rows")
    print("   Press Ctrl+C to stop early\n")

    # Data buffer for scrolling
    buffer = deque(maxlen=width * 2)  # Keep extra for smooth scrolling

    start_time = time.time()
    frame_count = 0

    try:
        while time.time() - start_time < duration:
            current_time = time.time() - start_time

            # Generate new sine wave sample
            sine_value = math.sin(2 * math.pi * frequency * current_time)
            buffer.append(sine_value)

            # Render current buffer to Braille
            braille_rows = sine_wave_to_braille_rows(buffer, width, 4)

            # Clear screen and redraw
            print("\033[H\033[J", end="")  # Clear screen, move to top

            # Header with stats
            print(f"🌊 Braille Sine Wave Demo - Time: {current_time:.1f}s")
            print(f"┌─{'─' * width}─┐")

            # Render Braille rows with Y-axis labels
            y_labels = ["+1.0", "+0.3", "-0.3", "-1.0"]
            for row, label in zip(braille_rows, y_labels, strict=False):
                print(f"│{label} {row} │")

            print(f"└─{'─' * width}─┘")
            print(f"Frame: {frame_count}, Value: {sine_value:+.3f}, Freq: {frequency} Hz")

            # Flush output
            sys.stdout.flush()

            frame_count += 1

            # Control refresh rate (~20 FPS)
            await asyncio.sleep(0.05)

    except KeyboardInterrupt:
        print("\n⏹️  Demo stopped by user")

    elapsed = time.time() - start_time
    fps = frame_count / elapsed if elapsed > 0 else 0
    print(f"\n📊 Demo complete: {frame_count} frames in {elapsed:.1f}s ({fps:.1f} FPS)")


async def main():
    """Main test function."""
    print("=" * 70)
    print("🎯 UILT Braille Sine Wave Sanity Check")
    print("=" * 70)

    # Test terminal capabilities first
    if not test_terminal_capabilities():
        print("\n❌ Terminal doesn't support Braille - falling back to ASCII would be needed")
        print("   Try: export LANG=en_US.UTF-8")
        return 1

    print("\n✅ Terminal supports Braille!")

    # Run the demo
    try:
        await scrolling_sine_wave_demo(duration=15, frequency=0.3, width=50)
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        return 1

    print("\n🎉 Sanity check complete! Braille scrolling works.")
    return 0


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(result)
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted")
        sys.exit(1)
