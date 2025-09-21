#!/usr/bin/env python3
"""Real-time signal visualization demo using UILT library.

This example demonstrates how to use UILT for live signal monitoring,
similar to how it would be integrated with the morse code decoder
for real-time audio analysis.
"""

import asyncio
import math
import sys
import os
import time
from collections import deque

# Add src to path for util imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from util.graph import BrailleBackend, ASCIIBackend


class RealTimeSignalGenerator:
    """Simulates real-time signal generation (like audio input)."""

    def __init__(self, sample_rate_hz: float = 1000.0):
        self.sample_rate_hz = sample_rate_hz
        self.time_offset = 0.0
        self.signal_type = "sine"
        self.frequency_hz = 50.0
        self.amplitude = 1.0

    def get_next_samples(self, num_samples: int) -> list[float]:
        """Generate next batch of samples."""
        samples = []
        dt = 1.0 / self.sample_rate_hz

        for i in range(num_samples):
            t = self.time_offset + (i * dt)

            if self.signal_type == "sine":
                sample = self.amplitude * math.sin(2 * math.pi * self.frequency_hz * t)
            elif self.signal_type == "square":
                sample = self.amplitude * (1 if math.sin(2 * math.pi * self.frequency_hz * t) > 0 else -1)
            elif self.signal_type == "noise":
                sample = self.amplitude * (math.sin(t * 100) + 0.5 * math.sin(t * 237) + 0.3 * math.sin(t * 451))
            elif self.signal_type == "chirp":
                # Frequency sweep
                f_inst = self.frequency_hz + 50 * math.sin(t * 0.5)
                sample = self.amplitude * math.sin(2 * math.pi * f_inst * t)
            else:
                sample = 0.0

            samples.append(sample)

        self.time_offset += num_samples * dt
        return samples

    def set_signal_type(self, signal_type: str):
        """Change signal type on the fly."""
        self.signal_type = signal_type

    def set_frequency(self, frequency_hz: float):
        """Change frequency on the fly."""
        self.frequency_hz = frequency_hz


class RealTimePlotter:
    """Real-time plotter using UILT backends."""

    def __init__(self, backend_type: str = "braille", width: int = 60, height: int = 6, buffer_size: int = 1000):
        self.width = width
        self.height = height
        self.buffer_size = buffer_size
        self.data_buffer = deque(maxlen=buffer_size)

        # Create backend
        if backend_type.lower() == "braille":
            self.backend = BrailleBackend(width, height, "Real-time Signal")
            self.render_method = self.backend.render_braille
        else:
            self.backend = ASCIIBackend(width, height, "Real-time Signal")
            self.render_method = self.backend.render_sparkline

        # Performance tracking
        self.frame_count = 0
        self.start_time = time.time()

    def add_samples(self, samples: list[float]):
        """Add new samples to the buffer."""
        self.data_buffer.extend(samples)

    def render_frame(self) -> list[str]:
        """Render current frame."""
        if not self.data_buffer:
            return [" " * self.width for _ in range(self.height)]

        # Clear previous data and plot current buffer
        self.backend.clear()
        self.backend.plot(list(self.data_buffer))

        self.frame_count += 1
        return self.render_method()

    def get_fps(self) -> float:
        """Calculate current FPS."""
        elapsed = time.time() - self.start_time
        return self.frame_count / elapsed if elapsed > 0 else 0.0


async def realtime_visualization_demo():
    """Main real-time visualization demonstration."""
    print("🎬 Real-time Signal Visualization Demo")
    print("=" * 50)
    print("This demo simulates real-time signal processing like morse code audio analysis\n")

    # Setup
    signal_generator = RealTimeSignalGenerator(sample_rate_hz=500.0)
    plotter = RealTimePlotter(backend_type="braille", width=50, height=4, buffer_size=200)

    # Demo sequence
    demo_sequence = [
        ("sine", 25.0, "25 Hz Sine Wave", 3.0),
        ("sine", 75.0, "75 Hz Sine Wave", 3.0),
        ("square", 40.0, "40 Hz Square Wave", 3.0),
        ("chirp", 50.0, "Frequency Sweep", 4.0),
        ("noise", 1.0, "Multi-tone Signal", 3.0),
    ]

    total_demo_time = sum(duration for _, _, _, duration in demo_sequence)
    print(f"Demo duration: {total_demo_time:.1f} seconds")
    print("Press Ctrl+C to stop early\n")

    try:
        for signal_type, frequency, description, duration in demo_sequence:
            print(f"🎵 {description}")
            print("-" * 30)

            # Configure signal generator
            signal_generator.set_signal_type(signal_type)
            signal_generator.set_frequency(frequency)

            # Run visualization for specified duration
            end_time = time.time() + duration
            frame_interval = 0.05  # 20 FPS target

            while time.time() < end_time:
                loop_start = time.time()

                # Generate new samples (simulate real-time input)
                samples_per_frame = int(signal_generator.sample_rate_hz * frame_interval)
                new_samples = signal_generator.get_next_samples(samples_per_frame)

                # Add to plotter
                plotter.add_samples(new_samples)

                # Render frame
                frame_lines = plotter.render_frame()

                # Clear screen and display
                print("\033[H\033[J", end="")  # Clear screen
                print(f"🎵 {description}")
                print(f"FPS: {plotter.get_fps():.1f} | Frequency: {frequency:.1f} Hz")
                print("-" * 30)

                for line in frame_lines:
                    print(line)

                print(f"\nBuffer: {len(plotter.data_buffer)}/{plotter.buffer_size} samples")
                print(f"Time remaining: {end_time - time.time():.1f}s")

                # Maintain frame rate
                elapsed = time.time() - loop_start
                sleep_time = max(0, frame_interval - elapsed)
                await asyncio.sleep(sleep_time)

            print(f"\n✅ {description} complete\n")
            await asyncio.sleep(0.5)  # Brief pause between signals

    except KeyboardInterrupt:
        print("\n\n⏹️  Demo stopped by user")

    final_fps = plotter.get_fps()
    print(f"\n📊 Performance Summary:")
    print(f"   Average FPS: {final_fps:.1f}")
    print(f"   Total frames rendered: {plotter.frame_count}")
    print(f"   Backend: {'Braille (2x resolution)' if isinstance(plotter.backend, BrailleBackend) else 'ASCII'}")


async def morse_code_simulation_demo():
    """Simulate morse code signal detection visualization."""
    print("\n📡 Morse Code Signal Simulation")
    print("=" * 40)
    print("Simulating morse code 'SOS' pattern detection\n")

    # SOS pattern: ··· --- ···
    # Short pulse = 0.1s, Long pulse = 0.3s, Gap = 0.1s, Letter gap = 0.3s
    morse_pattern = []
    sample_rate = 200.0

    def add_pulse(duration: float, amplitude: float):
        samples = int(duration * sample_rate)
        for _ in range(samples):
            morse_pattern.append(amplitude)

    def add_gap(duration: float):
        add_pulse(duration, 0.0)

    # Create SOS pattern
    # S: ···
    add_pulse(0.1, 1.0)  # dot
    add_gap(0.1)
    add_pulse(0.1, 1.0)  # dot
    add_gap(0.1)
    add_pulse(0.1, 1.0)  # dot
    add_gap(0.3)  # letter gap

    # O: ---
    add_pulse(0.3, 1.0)  # dash
    add_gap(0.1)
    add_pulse(0.3, 1.0)  # dash
    add_gap(0.1)
    add_pulse(0.3, 1.0)  # dash
    add_gap(0.3)  # letter gap

    # S: ···
    add_pulse(0.1, 1.0)  # dot
    add_gap(0.1)
    add_pulse(0.1, 1.0)  # dot
    add_gap(0.1)
    add_pulse(0.1, 1.0)  # dot

    print(f"Generated SOS pattern: {len(morse_pattern)} samples")

    # Display with both backends for comparison
    print("\nASCII Backend:")
    ascii_plotter = RealTimePlotter(backend_type="ascii", width=60, height=4)
    ascii_plotter.add_samples(morse_pattern)
    ascii_frame = ascii_plotter.render_frame()
    for line in ascii_frame:
        print(line)

    print("\nBraille Backend (2x resolution):")
    braille_plotter = RealTimePlotter(backend_type="braille", width=60, height=3)
    braille_plotter.add_samples(morse_pattern)
    braille_frame = braille_plotter.render_frame()
    for line in braille_frame:
        print(line)

    print("\n💡 Notice how Braille backend shows more timing detail")
    print("   This would help with precise morse code timing analysis")


async def main():
    """Run all real-time demos."""
    print("🚀 UILT Real-time Visualization Examples\n")

    try:
        await realtime_visualization_demo()
        await morse_code_simulation_demo()

        print("\n" + "=" * 50)
        print("✅ Real-time demos completed!")
        print("\n🎯 Key Takeaways:")
        print("   • UILT enables smooth real-time visualization")
        print("   • Braille backend provides 2x time resolution")
        print("   • Perfect for SSH-based remote debugging")
        print("   • Ideal for morse code timing analysis")

    except Exception as e:
        print(f"\n❌ Error in real-time demo: {e}")
        return 1

    return 0


if __name__ == "__main__":
    # Run async demo
    exit(asyncio.run(main()))