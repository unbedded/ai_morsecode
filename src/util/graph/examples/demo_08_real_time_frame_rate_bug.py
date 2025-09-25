#!/usr/bin/env python3
"""Real-time demo showing identical signals at different frame rates producing different visual output.

This demo reproduces the exact bug found in the morse code application:
- Same audio signal processed at different refresh rates
- Shows how frame rate affects visual output (the bug we're fixing)
- Demonstrates the problem UILT solves with time-aware decimation
"""

import asyncio
import os
import sys
import time
from collections import deque

# Add src to path for util imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from util.graph.backends.ascii_backend import ASCIIBackend
from util.graph.backends.braille_backend import BrailleBackend


class MockMorseSignalSource:
    """Simulates continuous morse code signal like real audio input."""

    def __init__(self, sample_rate_hz: float = 1000.0):
        self.sample_rate_hz = sample_rate_hz
        self.time_offset = 0.0
        self.wpm = 20  # Words per minute

        # Generate a repeating morse pattern (SOS)
        self.pattern = self._generate_sos_pattern()
        self.pattern_duration_sec = len(self.pattern) / sample_rate_hz

    def _generate_sos_pattern(self) -> list[float]:
        """Generate simple 50% duty cycle square wave for clear bug demonstration."""
        # Use simple square wave: 1 Hz frequency, 50% duty cycle
        frequency_hz = 1.0  # 1 Hz = 1 second period
        duration_sec = 4.0  # 4 seconds = 4 complete cycles

        samples = []
        num_samples = int(duration_sec * self.sample_rate_hz)

        for i in range(num_samples):
            t = i / self.sample_rate_hz
            # Perfect 50% duty cycle square wave
            cycle_position = (t * frequency_hz) % 1.0
            value = 1.0 if cycle_position < 0.5 else -1.0
            samples.append(value)

        return samples

    def get_samples_at_time(self, current_time_sec: float, num_samples: int) -> list[float]:
        """Get samples starting at specific time (simulates continuous signal)."""
        samples = []
        dt = 1.0 / self.sample_rate_hz

        for i in range(num_samples):
            t = current_time_sec + (i * dt)
            # Loop the pattern
            pattern_time = t % self.pattern_duration_sec
            pattern_index = int(pattern_time * self.sample_rate_hz)

            if pattern_index < len(self.pattern):
                samples.append(self.pattern[pattern_index])
            else:
                samples.append(0.0)

        return samples


class RealTimeDisplay:
    """Real-time display with specific frame rate."""

    def __init__(self, backend_type: str, frame_rate_hz: float, width: int = 50, height: int = 4):
        self.frame_rate_hz = frame_rate_hz
        self.frame_interval_sec = 1.0 / frame_rate_hz
        self.width = width
        self.height = height

        # Create backend
        title = f"{backend_type.upper()} @ {frame_rate_hz:.1f}Hz"
        if backend_type.lower() == "braille":
            from util.graph.backends.braille_backend import BrailleBackend

            self.backend = BrailleBackend(width, height, title)
            self.render_method = self.backend.render_braille
        else:
            from util.graph.backends.ascii_backend import ASCIIBackend

            self.backend = ASCIIBackend(width, height, title)
            self.render_method = self.backend.render_sparkline

        # Buffer management
        self.window_duration_sec = 2.0  # Show 2 seconds of data
        self.buffer_size = int(self.window_duration_sec * 1000)  # Assuming 1kHz signal
        self.data_buffer = deque(maxlen=self.buffer_size)

        # Performance tracking
        self.frame_count = 0
        self.last_render_time = 0.0

    def update_display(self, signal_source: MockMorseSignalSource, current_time_sec: float) -> list[str]:
        """Update display with latest signal data at this frame rate."""
        # FIRST FRAME FIX: Initialize last_render_time on first call
        if self.last_render_time == 0.0:
            self.last_render_time = current_time_sec
            # Start with minimal initial data for clean first frame
            initial_samples = signal_source.get_samples_at_time(current_time_sec, 10)
            self.data_buffer.extend(initial_samples)
        else:
            # Calculate how much new data we need since last update
            time_since_last = current_time_sec - self.last_render_time
            new_samples_needed = int(time_since_last * signal_source.sample_rate_hz)

            if new_samples_needed > 0:
                # Get new samples from the continuous signal
                start_time = self.last_render_time
                new_samples = signal_source.get_samples_at_time(start_time, new_samples_needed)
                self.data_buffer.extend(new_samples)

        self.last_render_time = current_time_sec

        # Render current buffer
        if len(self.data_buffer) > 0:
            buffer_list = list(self.data_buffer)
            self.backend.clear()
            self.backend.plot(buffer_list, sample_rate_hz=signal_source.sample_rate_hz)
            output = self.render_method()
        else:
            output = [" " * self.width for _ in range(self.height)]

        self.frame_count += 1
        return output


async def demo_frame_rate_bug():
    """Demonstrate the frame rate bug with side-by-side displays."""
    print("🐛 REAL-TIME FRAME RATE BUG DEMONSTRATION")
    print("=" * 80)
    print("PROBLEM: Same morse signal at different frame rates produces different visual output")
    print("SOLUTION: UILT time-aware decimation ensures identical output regardless of frame rate")
    print()

    # Create signal source (simulates continuous audio input)
    signal_source = MockMorseSignalSource(sample_rate_hz=1000.0)

    # Create displays with different frame rates for both ASCII and Braille
    displays = {
        "ascii_slow": RealTimeDisplay("ascii", frame_rate_hz=5.0, width=60, height=4),
        "ascii_normal": RealTimeDisplay("ascii", frame_rate_hz=15.0, width=60, height=4),
        "ascii_fast": RealTimeDisplay("ascii", frame_rate_hz=30.0, width=60, height=4),
        "braille_slow": RealTimeDisplay("braille", frame_rate_hz=5.0, width=60, height=4),
        "braille_normal": RealTimeDisplay("braille", frame_rate_hz=15.0, width=60, height=4),
        "braille_fast": RealTimeDisplay("braille", frame_rate_hz=30.0, width=60, height=4),
    }

    print("📺 Six displays showing IDENTICAL 50% duty cycle square wave:")
    print("   ASCII Backend:")
    print("     - ASCII Slow: 5 Hz refresh (updates every 200ms)")
    print("     - ASCII Normal: 15 Hz refresh (updates every 67ms)")
    print("     - ASCII Fast: 30 Hz refresh (updates every 33ms)")
    print("   Braille Backend:")
    print("     - Braille Slow: 5 Hz refresh (updates every 200ms)")
    print("     - Braille Normal: 15 Hz refresh (updates every 67ms)")
    print("     - Braille Fast: 30 Hz refresh (updates every 33ms)")
    print()
    print("❌ BUG: These SHOULD look identical but currently DON'T due to frame rate differences!")
    print("✅ SOLUTION: UILT time-aware decimation ensures identical output regardless of refresh rate")
    print("   Press Ctrl+C to stop")
    print()

    start_time = time.time()
    demo_duration_sec = 15.0

    try:
        while time.time() - start_time < demo_duration_sec:
            current_time = time.time() - start_time

            # Update all displays with same signal source
            outputs = {}
            for name, display in displays.items():
                outputs[name] = display.update_display(signal_source, current_time)

            # Clear screen and show side-by-side
            print("\033[H\033[J", end="")  # Clear screen

            # Header
            elapsed = time.time() - start_time
            remaining = demo_duration_sec - elapsed
            print(f"🔍 Frame Rate Bug Demo - Time: {elapsed:.1f}s (remaining: {remaining:.1f}s)")
            print()

            # Display graphs stacked vertically for easy comparison
            print("📊 ASCII BACKEND:")
            print("🔴 ASCII Slow (5 Hz) - Updates every 200ms:")
            print("─" * 65)
            for line in outputs["ascii_slow"]:
                print(f"  {line}")
            print(f"    Frames: {displays['ascii_slow'].frame_count}")
            print()

            print("🟡 ASCII Normal (15 Hz) - Updates every 67ms:")
            print("─" * 65)
            for line in outputs["ascii_normal"]:
                print(f"  {line}")
            print(f"    Frames: {displays['ascii_normal'].frame_count}")
            print()

            print("🟢 ASCII Fast (30 Hz) - Updates every 33ms:")
            print("─" * 65)
            for line in outputs["ascii_fast"]:
                print(f"  {line}")
            print(f"    Frames: {displays['ascii_fast'].frame_count}")
            print()

            print("📊 BRAILLE BACKEND:")
            print("🔴 Braille Slow (5 Hz) - Updates every 200ms:")
            print("─" * 65)
            for line in outputs["braille_slow"]:
                print(f"  {line}")
            print(f"    Frames: {displays['braille_slow'].frame_count}")
            print()

            print("🟡 Braille Normal (15 Hz) - Updates every 67ms:")
            print("─" * 65)
            for line in outputs["braille_normal"]:
                print(f"  {line}")
            print(f"    Frames: {displays['braille_normal'].frame_count}")
            print()

            print("🟢 Braille Fast (30 Hz) - Updates every 33ms:")
            print("─" * 65)
            for line in outputs["braille_fast"]:
                print(f"  {line}")
            print(f"    Frames: {displays['braille_fast'].frame_count}")
            print()

            print("❌ OBSERVE: Within each backend, all frame rates should show IDENTICAL patterns!")

            # Update at highest frame rate for smooth demo
            await asyncio.sleep(1.0 / 30.0)

    except KeyboardInterrupt:
        print("\n⏹️  Demo stopped by user")

    elapsed = time.time() - start_time
    print(f"\n📊 Demo Results ({elapsed:.1f}s total):")
    for name, display in displays.items():
        fps = display.frame_count / elapsed
        print(f"   {name:8s}: {display.frame_count:3d} frames ({fps:.1f} fps)")

    print("\n🎯 What We Just Observed:")
    print("   ❌ CURRENT BUG: Same 50% duty cycle square wave looks different at different frame rates")
    print("   ✅ DESIRED RESULT: All three displays should show IDENTICAL square wave patterns")
    print("   🔧 THE FIX: UILT time-aware decimation ensures consistent visualization")
    print("\n💡 This demonstrates the exact morse code visualization bug that UILT solves!")


def show_ideal_output():
    """Show what the output SHOULD look like - identical across all frame rates."""
    print("🎯 REFERENCE: What All Three Displays SHOULD Look Like")
    print("=" * 65)
    print("Perfect 50% duty cycle square wave (1 Hz, 2 seconds shown):")
    print()

    # Generate reference pattern
    signal_source = MockMorseSignalSource(sample_rate_hz=1000.0)
    reference_samples = signal_source.get_samples_at_time(0.0, 2000)  # 2 seconds

    # Show ASCII version first

    ascii_backend = ASCIIBackend(60, 4, "ASCII IDEAL")
    ascii_backend.plot(reference_samples, sample_rate_hz=1000.0)
    ascii_output = ascii_backend.render_sparkline()

    print("✅ ASCII IDEAL - Clean, consistent pattern:")
    print("─" * 65)
    for line in ascii_output:
        print(f"  {line}")
    print()

    # Show Braille version for comparison

    braille_backend = BrailleBackend(60, 4, "BRAILLE IDEAL")
    braille_backend.plot(reference_samples, sample_rate_hz=1000.0)
    braille_output = braille_backend.render_braille()

    print("✅ BRAILLE IDEAL - 2x resolution with potential artifacts:")
    print("─" * 65)
    for line in braille_output:
        print(f"  {line}")
    print()

    print("📋 Key characteristics:")
    print("   - Clean 50% duty cycle (high for 0.5s, low for 0.5s)")
    print("   - Sharp transitions")
    print("   - Consistent pattern regardless of display refresh rate")
    print("   - ASCII: Simple bar chart representation")
    print("   - Braille: 2x horizontal resolution with sub-pixel details")
    print()


async def main():
    """Main demo function."""
    print("🎯 Real-Time Frame Rate Bug Demonstration")
    print("=" * 60)
    print("This demo reproduces the exact issue found in morse code applications:")
    print("- Same signal source (like audio input)")
    print("- Different display refresh rates")
    print("- Results in different visual output (the bug!)")
    print()

    # Show ideal reference first
    show_ideal_output()

    input("Press Enter to start the live demo and see the bug...")
    await demo_frame_rate_bug()

    print("\n🎉 Demo complete!")
    print("This demonstrates why UILT's time-aware decimation is essential")
    print("for consistent morse code visualization across different frame rates.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted")
        sys.exit(1)
