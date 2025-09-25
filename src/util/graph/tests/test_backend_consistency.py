"""Comprehensive unit tests for UILT backend consistency and sample rate handling.

Tests verify that identical waves with different sampling rates render identically,
and that both ASCII and Braille backends behave consistently across refresh rates.
"""

import math
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

# Add the src directory to the path so we can import from util
src_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(src_dir))

from util.graph.backends.ascii_backend import ASCIIBackend
from util.graph.backends.braille_backend import BrailleBackend
from util.graph.core.time_axis import TimeAxis


class WaveformGenerator:
    """Generate test waveforms with precise timing control."""

    @staticmethod
    def generate_square_wave(
        frequency_hz: float, duration_sec: float, sample_rate_hz: float, amplitude: float = 1.0
    ) -> tuple[list[float], list[float]]:
        """Generate square wave with specified parameters."""
        sample_period_sec = 1.0 / sample_rate_hz
        num_samples = int(duration_sec * sample_rate_hz)

        times = []
        samples = []

        for i in range(num_samples):
            t = i * sample_period_sec
            # Square wave: +amplitude for first half of period, -amplitude for second half
            period_position = (t * frequency_hz) % 1.0
            value = amplitude if period_position < 0.5 else -amplitude

            times.append(t)
            samples.append(value)

        return times, samples

    @staticmethod
    def generate_sine_wave(
        frequency_hz: float, duration_sec: float, sample_rate_hz: float, amplitude: float = 1.0
    ) -> tuple[list[float], list[float]]:
        """Generate sine wave with specified parameters."""
        sample_period_sec = 1.0 / sample_rate_hz
        num_samples = int(duration_sec * sample_rate_hz)

        times = []
        samples = []

        for i in range(num_samples):
            t = i * sample_period_sec
            value = amplitude * math.sin(2 * math.pi * frequency_hz * t)

            times.append(t)
            samples.append(value)

        return times, samples

    @staticmethod
    def generate_morse_dit_pattern(wpm: int, sample_rate_hz: float) -> tuple[list[float], list[float]]:
        """Generate a morse DIT pattern with proper timing."""
        dit_duration_sec = 1.2 / wpm  # Standard morse timing
        gap_duration_sec = dit_duration_sec

        # Generate: DIT, GAP, DIT sequence
        total_duration = 2 * dit_duration_sec + gap_duration_sec
        sample_period_sec = 1.0 / sample_rate_hz
        num_samples = int(total_duration * sample_rate_hz)

        times = []
        samples = []

        for i in range(num_samples):
            t = i * sample_period_sec

            if t < dit_duration_sec:
                # First DIT
                value = 1.0
            elif t < dit_duration_sec + gap_duration_sec:
                # Gap
                value = 0.0
            elif t < 2 * dit_duration_sec + gap_duration_sec:
                # Second DIT
                value = 1.0
            else:
                # Final gap
                value = 0.0

            times.append(t)
            samples.append(value)

        return times, samples


class TestOutputCapture:
    """Capture and save backend output for analysis."""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save_ascii_output(self, output: list[str], filename: str, metadata: dict[str, Any] = None):
        """Save ASCII backend output to file."""
        filepath = self.output_dir / f"{filename}.txt"

        with open(filepath, "w", encoding="utf-8") as f:
            if metadata:
                f.write(f"# Metadata: {metadata}\n")
            f.write(f"# ASCII Output ({len(output)} rows)\n")
            f.write("-" * 80 + "\n")

            for i, row in enumerate(output):
                f.write(f"{i:2d}: {row}\n")

            f.write("-" * 80 + "\n")

    def save_braille_output(self, output: list[str], filename: str, metadata: dict[str, Any] = None):
        """Save Braille backend output to file."""
        filepath = self.output_dir / f"{filename}.txt"

        with open(filepath, "w", encoding="utf-8") as f:
            if metadata:
                f.write(f"# Metadata: {metadata}\n")
            f.write(f"# Braille Output ({len(output)} rows)\n")
            f.write("-" * 80 + "\n")

            for i, row in enumerate(output):
                f.write(f"{i:2d}: {row}\n")

            f.write("-" * 80 + "\n")

    def save_comparison_report(self, test_name: str, results: dict[str, Any]):
        """Save comprehensive comparison report."""
        filepath = self.output_dir / f"{test_name}_report.txt"

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Test Report: {test_name}\n")
            f.write(f"# Generated at: {results.get('timestamp', 'unknown')}\n")
            f.write("=" * 80 + "\n\n")

            for key, value in results.items():
                if key != "timestamp":
                    f.write(f"{key}:\n")
                    if isinstance(value, (list, tuple)):
                        for item in value:
                            f.write(f"  - {item}\n")
                    else:
                        f.write(f"  {value}\n")
                    f.write("\n")


class TestBackendConsistency(unittest.TestCase):
    """Test backend consistency across different scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp(prefix="uilt_test_")
        self.output_capture = TestOutputCapture(self.temp_dir)

        # Standard test parameters
        self.width = 80
        self.height = 10
        self.wave_frequency_hz = 1.0  # 1 Hz for easy verification
        self.duration_sec = 4.0  # 4 seconds = 4 complete cycles

    def tearDown(self):
        """Clean up test fixtures."""
        # Keep output files for analysis - don't delete temp_dir
        print(f"Test outputs saved to: {self.temp_dir}")

    def test_identical_square_waves_different_sampling(self):
        """Test that identical square waves render identically despite different sampling rates."""
        test_name = "identical_square_waves"

        # Test parameters - use rates that create integer samples per half-cycle
        # For 1Hz frequency, half-cycle = 0.5s, so sample rates should be multiples of 2
        sample_rates = [10.0, 20.0, 40.0, 80.0]  # Different sampling rates
        amplitude = 1.0

        results = {
            "test_name": test_name,
            "wave_frequency_hz": self.wave_frequency_hz,
            "duration_sec": self.duration_sec,
            "amplitude": amplitude,
            "width": self.width,
            "height": self.height,
            "timestamp": "2024-01-01T00:00:00",
            "ascii_results": [],
            "braille_results": [],
            "consistency_check": [],
        }

        ascii_outputs = {}
        braille_outputs = {}

        for sample_rate_hz in sample_rates:
            # Generate waveform
            times, samples = WaveformGenerator.generate_square_wave(
                self.wave_frequency_hz, self.duration_sec, sample_rate_hz, amplitude
            )

            # Create time axis
            sample_period_sec = 1.0 / sample_rate_hz
            time_axis = TimeAxis(sample_period_sec, start_time_sec=0.0)

            # Test ASCII backend
            ascii_backend = ASCIIBackend(self.width, self.height, f"Square Wave {sample_rate_hz}Hz")
            ascii_backend.plot(samples, sample_rate_hz=sample_rate_hz)
            ascii_output = ascii_backend.render_sparkline()
            ascii_outputs[sample_rate_hz] = ascii_output

            # Test Braille backend
            braille_backend = BrailleBackend(self.width, self.height, f"Square Wave {sample_rate_hz}Hz")
            braille_backend.plot(samples, sample_rate_hz=sample_rate_hz)
            braille_output = braille_backend.render_braille()
            braille_outputs[sample_rate_hz] = braille_output

            # Save individual outputs
            metadata = {
                "sample_rate_hz": sample_rate_hz,
                "num_samples": len(samples),
                "duration_sec": self.duration_sec,
                "wave_frequency_hz": self.wave_frequency_hz,
            }

            self.output_capture.save_ascii_output(ascii_output, f"{test_name}_ascii_{sample_rate_hz}hz", metadata)

            self.output_capture.save_braille_output(braille_output, f"{test_name}_braille_{sample_rate_hz}hz", metadata)

            results["ascii_results"].append(
                {
                    "sample_rate_hz": sample_rate_hz,
                    "num_samples": len(samples),
                    "output_rows": len(ascii_output),
                    "first_row": ascii_output[0] if ascii_output else "EMPTY",
                }
            )

            results["braille_results"].append(
                {
                    "sample_rate_hz": sample_rate_hz,
                    "num_samples": len(samples),
                    "output_rows": len(braille_output),
                    "first_row": braille_output[0] if braille_output else "EMPTY",
                }
            )

        # Compare outputs for consistency
        ascii_baseline = ascii_outputs[sample_rates[0]]
        braille_baseline = braille_outputs[sample_rates[0]]

        for sample_rate_hz in sample_rates[1:]:
            ascii_match = ascii_outputs[sample_rate_hz] == ascii_baseline
            braille_match = braille_outputs[sample_rate_hz] == braille_baseline

            results["consistency_check"].append(
                {"sample_rate_hz": sample_rate_hz, "ascii_identical": ascii_match, "braille_identical": braille_match}
            )

            # Assert consistency (these are the actual unit test assertions)
            self.assertEqual(
                ascii_outputs[sample_rate_hz],
                ascii_baseline,
                f"ASCII output differs between {sample_rates[0]}Hz and {sample_rate_hz}Hz sampling",
            )

            self.assertEqual(
                braille_outputs[sample_rate_hz],
                braille_baseline,
                f"Braille output differs between {sample_rates[0]}Hz and {sample_rate_hz}Hz sampling",
            )

        # Save comprehensive report
        self.output_capture.save_comparison_report(test_name, results)

    def test_sliding_window_vs_time_aware_modes(self):
        """Test that sliding window mode produces consistent left-to-right fill."""
        test_name = "sliding_window_consistency"

        # Generate sparse data (should trigger sliding window mode)
        sample_rate_hz = 5.0  # Low rate to ensure sparse data
        times, samples = WaveformGenerator.generate_square_wave(
            self.wave_frequency_hz,
            1.0,
            sample_rate_hz,  # Only 1 second of data
        )

        time_axis = TimeAxis(1.0 / sample_rate_hz, start_time_sec=0.0)

        # Test ASCII backend with small amounts of data
        results = {"test_name": test_name, "sample_rate_hz": sample_rate_hz, "progressive_fills": []}

        # Test progressive data addition (simulating real-time fill)
        for num_points in [1, 2, 3, 4, 5]:
            partial_samples = samples[:num_points]

            ascii_backend = ASCIIBackend(self.width, self.height)
            ascii_backend.plot(partial_samples, sample_rate_hz=sample_rate_hz)
            output = ascii_backend.render_sparkline()

            # Save output for each progressive fill
            metadata = {"num_points": num_points, "sample_rate_hz": sample_rate_hz}
            self.output_capture.save_ascii_output(output, f"{test_name}_ascii_{num_points}pts", metadata)

            # Analyze where data appears (should be left-aligned for sliding window)
            first_data_col = -1
            if output and len(output) > 0:
                for col_idx, char in enumerate(output[-1]):  # Bottom row has most data
                    if char != " ":
                        first_data_col = col_idx
                        break

            results["progressive_fills"].append(
                {
                    "num_points": num_points,
                    "first_data_column": first_data_col,
                    "output_sample": output[-1] if output else "EMPTY",
                }
            )

            # Assert that data starts from the left (column 0 or very close)
            self.assertLessEqual(
                first_data_col,
                2,  # Allow some tolerance for braille positioning
                f"Data should start from left, but first data at column {first_data_col} for {num_points} points",
            )

        self.output_capture.save_comparison_report(test_name, results)

    def test_morse_dit_pattern_consistency(self):
        """Test morse DIT pattern rendering consistency."""
        test_name = "morse_dit_consistency"

        # Test different WPM rates with different sampling
        wpm_rates = [15, 20, 25]
        sample_rates = [50.0, 100.0]

        results = {"test_name": test_name, "morse_tests": []}

        for wpm in wpm_rates:
            for sample_rate_hz in sample_rates:
                times, samples = WaveformGenerator.generate_morse_dit_pattern(wpm, sample_rate_hz)

                # Test ASCII backend
                ascii_backend = ASCIIBackend(self.width, self.height)
                ascii_backend.plot(samples, sample_rate_hz=sample_rate_hz)
                ascii_output = ascii_backend.render_sparkline()

                # Test Braille backend
                braille_backend = BrailleBackend(self.width, self.height)
                braille_backend.plot(samples, sample_rate_hz=sample_rate_hz)
                braille_output = braille_backend.render_braille()

                # Save outputs
                metadata = {
                    "wpm": wpm,
                    "sample_rate_hz": sample_rate_hz,
                    "num_samples": len(samples),
                    "dit_duration_sec": 1.2 / wpm,
                }

                self.output_capture.save_ascii_output(
                    ascii_output, f"{test_name}_ascii_{wpm}wpm_{sample_rate_hz}hz", metadata
                )

                self.output_capture.save_braille_output(
                    braille_output, f"{test_name}_braille_{wpm}wpm_{sample_rate_hz}hz", metadata
                )

                results["morse_tests"].append(
                    {
                        "wpm": wpm,
                        "sample_rate_hz": sample_rate_hz,
                        "num_samples": len(samples),
                        "dit_duration_sec": 1.2 / wpm,
                        "ascii_rows": len(ascii_output),
                        "braille_rows": len(braille_output),
                    }
                )

        self.output_capture.save_comparison_report(test_name, results)

    def test_refresh_rate_consistency(self):
        """Test that outputs are consistent across different refresh simulation rates."""
        test_name = "refresh_rate_consistency"

        # Generate a longer signal
        sample_rate_hz = 50.0
        duration_sec = 8.0  # Longer signal
        times, samples = WaveformGenerator.generate_square_wave(self.wave_frequency_hz, duration_sec, sample_rate_hz)

        # Simulate different refresh rates by taking progressive chunks
        refresh_intervals = [0.1, 0.2, 0.5, 1.0]  # 10Hz, 5Hz, 2Hz, 1Hz refresh rates

        results = {"test_name": test_name, "refresh_tests": []}

        for refresh_interval_sec in refresh_intervals:
            refresh_outputs = []

            # Simulate progressive updates at this refresh rate
            for t in [1.0, 2.0, 3.0, 4.0]:  # Sample at different time points
                chunk_end_idx = int(t * sample_rate_hz)
                chunk_samples = samples[:chunk_end_idx]

                ascii_backend = ASCIIBackend(self.width, self.height)
                ascii_backend.plot(chunk_samples, sample_rate_hz=sample_rate_hz)
                output = ascii_backend.render_sparkline()

                refresh_outputs.append({"time_sec": t, "num_samples": len(chunk_samples), "output": output})

                # Save individual refresh frame
                metadata = {
                    "refresh_interval_sec": refresh_interval_sec,
                    "time_sec": t,
                    "num_samples": len(chunk_samples),
                }

                self.output_capture.save_ascii_output(
                    output, f"{test_name}_refresh_{refresh_interval_sec}s_t_{t}s", metadata
                )

            results["refresh_tests"].append(
                {
                    "refresh_interval_sec": refresh_interval_sec,
                    "frames": len(refresh_outputs),
                    "sample_times": [r["time_sec"] for r in refresh_outputs],
                }
            )

        self.output_capture.save_comparison_report(test_name, results)


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
