#!/usr/bin/env python3
"""Morse code integration example for UILT library.

This example demonstrates how the UILT library would integrate with
the morse code decoder for real-time signal analysis and debugging.
"""

import math
import sys
import os
import time
from collections import deque
from typing import List, Dict, Tuple
from enum import Enum

# Add src to path for util imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from util.graph import BrailleBackend, ASCIIBackend, plot_signal_auto


class MorseElement(Enum):
    """Morse code elements."""
    DOT = "dot"
    DASH = "dash"
    GAP = "gap"
    LETTER_GAP = "letter_gap"
    WORD_GAP = "word_gap"


class MockMorseDecoder:
    """Mock morse code decoder for demonstration purposes."""

    # Morse code table
    MORSE_TABLE = {
        'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
        'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
        'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
        'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
        'Y': '-.--', 'Z': '--..', '1': '.----', '2': '..---', '3': '...--',
        '4': '....-', '5': '.....', '6': '-....', '7': '--...', '8': '---..',
        '9': '----.', '0': '-----'
    }

    def __init__(self, sample_rate_hz: float = 1000.0):
        self.sample_rate_hz = sample_rate_hz
        self.wpm = 20  # Words per minute
        self.tone_freq_hz = 800.0  # Carrier frequency

        # Timing calculations (PARIS standard)
        self.dot_duration_sec = 1.2 / self.wpm
        self.dash_duration_sec = 3 * self.dot_duration_sec
        self.element_gap_sec = self.dot_duration_sec
        self.letter_gap_sec = 3 * self.dot_duration_sec
        self.word_gap_sec = 7 * self.dot_duration_sec

    def text_to_morse(self, text: str) -> str:
        """Convert text to morse code."""
        morse = []
        for char in text.upper():
            if char == ' ':
                morse.append('/')  # Word separator
            elif char in self.MORSE_TABLE:
                morse.append(self.MORSE_TABLE[char])
        return ' '.join(morse)

    def generate_morse_signal(self, text: str, add_noise: bool = True) -> Tuple[List[float], List[Dict]]:
        """Generate morse code audio signal with timing annotations."""
        morse_code = self.text_to_morse(text)
        signal = []
        annotations = []
        current_time = 0.0

        def add_samples(duration: float, amplitude: float, element_type: MorseElement, content: str = ""):
            nonlocal current_time
            num_samples = int(duration * self.sample_rate_hz)
            start_time = current_time

            for i in range(num_samples):
                t = current_time + (i / self.sample_rate_hz)
                if amplitude > 0:
                    # Generate tone with slight amplitude variation
                    sample = amplitude * math.sin(2 * math.pi * self.tone_freq_hz * t)
                    sample *= (0.9 + 0.1 * math.sin(2 * math.pi * 10 * t))  # 10 Hz amplitude modulation
                else:
                    sample = 0.0

                # Add noise if enabled
                if add_noise:
                    noise = 0.05 * math.sin(2 * math.pi * 50 * t)  # 50 Hz hum
                    noise += 0.02 * math.sin(2 * math.pi * 200 * t * t)  # Chirp noise
                    sample += noise

                signal.append(sample)

            annotations.append({
                'start_time': start_time,
                'end_time': current_time + duration,
                'duration': duration,
                'element_type': element_type,
                'content': content
            })

            current_time += duration

        # Process morse code
        for word in morse_code.split(' / '):  # Split by word separators
            if not word:
                continue

            for letter in word.split(' '):
                if not letter:
                    continue

                for symbol in letter:
                    if symbol == '.':
                        add_samples(self.dot_duration_sec, 1.0, MorseElement.DOT, ".")
                        add_samples(self.element_gap_sec, 0.0, MorseElement.GAP)
                    elif symbol == '-':
                        add_samples(self.dash_duration_sec, 1.0, MorseElement.DASH, "-")
                        add_samples(self.element_gap_sec, 0.0, MorseElement.GAP)

                # Letter gap (remove last element gap, add letter gap)
                if annotations:
                    annotations.pop()  # Remove last element gap
                    current_time -= self.element_gap_sec

                add_samples(self.letter_gap_sec, 0.0, MorseElement.LETTER_GAP)

            # Word gap
            add_samples(self.word_gap_sec, 0.0, MorseElement.WORD_GAP)

        return signal, annotations


class MorseVisualizationDebugger:
    """Real-time morse code visualization for debugging."""

    def __init__(self, backend_type: str = "braille", width: int = 80, height: int = 6):
        self.width = width
        self.height = height

        # Create visualization backend
        if backend_type.lower() == "braille":
            self.backend = BrailleBackend(width, height, "Morse Code Analysis")
            self.render_method = self.backend.render_braille
            self.backend_name = "Braille"
        else:
            self.backend = ASCIIBackend(width, height, "Morse Code Analysis")
            self.render_method = self.backend.render_sparkline
            self.backend_name = "ASCII"

        # Analysis parameters
        self.buffer_size = 2000  # Keep 2 seconds of data at 1kHz
        self.signal_buffer = deque(maxlen=self.buffer_size)
        self.envelope_buffer = deque(maxlen=self.buffer_size)

        # Detection state
        self.threshold = 0.3
        self.current_state = "silence"
        self.state_start_time = 0.0
        self.detected_elements = []

    def add_samples(self, samples: List[float], sample_rate_hz: float):
        """Add new samples and perform real-time analysis."""
        for sample in samples:
            self.signal_buffer.append(sample)

            # Simple envelope detection
            envelope = abs(sample)
            self.envelope_buffer.append(envelope)

    def detect_morse_elements(self, current_time: float) -> List[Dict]:
        """Simple morse element detection (for demonstration)."""
        if len(self.envelope_buffer) < 10:
            return []

        # Simple threshold detection
        recent_envelope = list(self.envelope_buffer)[-50:]  # Last 50 samples
        avg_level = sum(recent_envelope) / len(recent_envelope)

        new_state = "tone" if avg_level > self.threshold else "silence"

        detections = []
        if new_state != self.current_state:
            # State change detected
            duration = current_time - self.state_start_time

            if self.current_state == "tone" and duration > 0.01:  # Ignore very short tones
                if duration < 0.08:  # Dot threshold
                    element_type = "DOT"
                else:
                    element_type = "DASH"

                detections.append({
                    'type': element_type,
                    'duration': duration,
                    'start_time': self.state_start_time,
                    'end_time': current_time
                })

            self.current_state = new_state
            self.state_start_time = current_time

        return detections

    def render_analysis(self, annotations: List[Dict] = None) -> List[str]:
        """Render current signal analysis."""
        # Update backend with current signal
        self.backend.clear()
        if self.signal_buffer:
            self.backend.plot(list(self.signal_buffer))

        # Render visualization
        return self.render_method()

    def display_timing_info(self, annotations: List[Dict]):
        """Display timing information for morse elements."""
        if not annotations:
            return

        print(f"\n⏱️  Timing Analysis ({self.backend_name} backend):")
        print("-" * 40)

        dot_durations = []
        dash_durations = []

        for ann in annotations:
            if ann['element_type'] == MorseElement.DOT:
                dot_durations.append(ann['duration'])
                print(f"DOT:  {ann['duration']*1000:5.1f}ms at {ann['start_time']*1000:6.1f}ms")
            elif ann['element_type'] == MorseElement.DASH:
                dash_durations.append(ann['duration'])
                print(f"DASH: {ann['duration']*1000:5.1f}ms at {ann['start_time']*1000:6.1f}ms")

        if dot_durations and dash_durations:
            avg_dot = sum(dot_durations) / len(dot_durations)
            avg_dash = sum(dash_durations) / len(dash_durations)
            ratio = avg_dash / avg_dot

            print(f"\nTiming Statistics:")
            print(f"  Average dot:  {avg_dot*1000:.1f}ms")
            print(f"  Average dash: {avg_dash*1000:.1f}ms")
            print(f"  Dash/dot ratio: {ratio:.2f} (ideal: 3.0)")


def demonstrate_morse_visualization():
    """Demonstrate morse code visualization capabilities."""
    print("📡 Morse Code Integration Demonstration")
    print("=" * 45)

    # Initialize components
    decoder = MockMorseDecoder(sample_rate_hz=1000.0)
    visualizer = MorseVisualizationDebugger(backend_type="braille", width=60, height=4)

    # Test message
    test_message = "SOS"
    print(f"Test message: '{test_message}'")

    # Generate morse signal
    print("Generating morse code signal...")
    signal, annotations = decoder.generate_morse_signal(test_message, add_noise=True)

    morse_pattern = decoder.text_to_morse(test_message)
    print(f"Morse pattern: {morse_pattern}")
    print(f"Signal length: {len(signal)} samples ({len(signal)/decoder.sample_rate_hz:.2f} seconds)\n")

    # Add signal to visualizer
    visualizer.add_samples(signal, decoder.sample_rate_hz)

    # Render visualization
    print("Signal visualization:")
    viz_lines = visualizer.render_analysis(annotations)
    for line in viz_lines:
        print(line)

    # Display timing analysis
    visualizer.display_timing_info(annotations)


def compare_backends_for_morse():
    """Compare ASCII vs Braille for morse code analysis."""
    print("\n🔍 Backend Comparison for Morse Code Analysis")
    print("=" * 48)

    decoder = MockMorseDecoder(sample_rate_hz=800.0)

    # Generate a challenging signal with fast morse code
    fast_message = "PARIS"  # Standard test word
    decoder.wpm = 25  # Faster speed
    signal, annotations = decoder.generate_morse_signal(fast_message, add_noise=True)

    print(f"Test: '{fast_message}' at {decoder.wpm} WPM")
    print(f"Morse: {decoder.text_to_morse(fast_message)}")
    print(f"Signal: {len(signal)} samples\n")

    # ASCII visualization
    print("ASCII Backend (standard compatibility):")
    ascii_lines = plot_signal_auto(signal, sample_rate_hz=decoder.sample_rate_hz, width=50, height=4)[0]
    for line in ascii_lines:
        print(line)

    # Braille visualization
    print("\nBraille Backend (2x time resolution):")
    braille_viz = MorseVisualizationDebugger(backend_type="braille", width=50, height=3)
    braille_viz.add_samples(signal, decoder.sample_rate_hz)
    braille_lines = braille_viz.render_analysis()
    for line in braille_lines:
        print(line)

    print("\n💡 Analysis:")
    print("   • Braille shows finer timing details")
    print("   • Better resolution for dot/dash discrimination")
    print("   • Critical for accurate timing analysis")
    print("   • Especially important at higher WPM rates")


def demonstrate_real_time_debugging():
    """Demonstrate real-time debugging scenario."""
    print("\n🛠️  Real-time Debugging Scenario")
    print("=" * 35)

    print("Scenario: Debug timing issues in morse decoder")
    print("Problem: Decoder missing some dots at high speed")
    print("Solution: Use UILT for real-time signal analysis\n")

    decoder = MockMorseDecoder(sample_rate_hz=1000.0)
    decoder.wpm = 30  # High speed

    # Generate problematic signal (simulated timing drift)
    message = "TEST"
    signal, annotations = decoder.generate_morse_signal(message, add_noise=True)

    # Simulate timing drift by slightly compressing some dots
    for i, ann in enumerate(annotations):
        if ann['element_type'] == MorseElement.DOT and i % 3 == 0:
            # Simulate 20% shorter dots (timing issue)
            start_idx = int(ann['start_time'] * decoder.sample_rate_hz)
            end_idx = int(ann['end_time'] * decoder.sample_rate_hz)
            if end_idx < len(signal):
                # Compress the dot by zeroing out the last 20%
                compress_start = start_idx + int(0.8 * (end_idx - start_idx))
                for j in range(compress_start, min(end_idx, len(signal))):
                    signal[j] = 0.0

    print(f"Debugging: '{message}' at {decoder.wpm} WPM with timing issues")

    # Braille visualization for detailed analysis
    debug_viz = MorseVisualizationDebugger(backend_type="braille", width=70, height=4)
    debug_viz.add_samples(signal, decoder.sample_rate_hz)

    print("\nHigh-resolution timing analysis:")
    debug_lines = debug_viz.render_analysis()
    for line in debug_lines:
        print(line)

    print("\n🎯 Debug insights visible in Braille mode:")
    print("   • Irregular dot durations clearly visible")
    print("   • Timing drift patterns detectable")
    print("   • Can identify specific problematic elements")
    print("   • Enables precise timing calibration")


def integration_architecture_demo():
    """Show how UILT integrates with morse decoder architecture."""
    print("\n🏗️  Integration Architecture")
    print("=" * 28)

    print("UILT Integration Points in Morse Decoder:")
    print("┌─────────────────────────────────────────┐")
    print("│ Audio Input → Signal Processing         │")
    print("│      ↓              ↓                   │")
    print("│ UILT Visualizer ← Raw Signal            │")
    print("│      ↓              ↓                   │")
    print("│ Display Graph  ← Filtered Signal        │")
    print("│      ↓              ↓                   │")
    print("│ Timing Analysis ← Envelope Detection    │")
    print("│      ↓              ↓                   │")
    print("│ Debug Output   ← Morse Decoding         │")
    print("└─────────────────────────────────────────┘\n")

    print("Configuration for different use cases:")
    print("─" * 40)

    configs = [
        ("Development", "Braille", "High resolution for algorithm development"),
        ("Production", "ASCII", "Universal compatibility for deployment"),
        ("SSH Debug", "Auto", "Adaptive based on terminal capabilities"),
        ("Performance", "ASCII", "Lower overhead for continuous monitoring"),
    ]

    for use_case, backend, description in configs:
        print(f"{use_case:<12} | {backend:<8} | {description}")

    print("\nSample integration code:")
    print("```python")
    print("from util.graph import BrailleBackend")
    print("")
    print("class MorseDecoder:")
    print("    def __init__(self, debug_mode=False):")
    print("        if debug_mode:")
    print("            self.visualizer = BrailleBackend(80, 6)")
    print("        ")
    print("    def process_audio(self, samples):")
    print("        # Signal processing...")
    print("        if hasattr(self, 'visualizer'):")
    print("            self.visualizer.clear()")
    print("            self.visualizer.plot(samples)")
    print("            lines = self.visualizer.render_braille()")
    print("            for line in lines:")
    print("                self.logger.debug(line)")
    print("```")


def main():
    """Run all morse code integration examples."""
    print("🎯 UILT + Morse Code Integration Examples\n")

    try:
        demonstrate_morse_visualization()
        compare_backends_for_morse()
        demonstrate_real_time_debugging()
        integration_architecture_demo()

        print("\n" + "=" * 60)
        print("✅ Morse code integration examples completed!")
        print("\n🚀 Ready for Production Integration:")
        print("   • Real-time signal visualization")
        print("   • Timing analysis and debugging")
        print("   • SSH-friendly remote debugging")
        print("   • Backend selection for different use cases")
        print("   • Performance optimized for continuous monitoring")

    except Exception as e:
        print(f"\n❌ Error in morse integration demo: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())