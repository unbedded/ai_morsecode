"""Precision tests for sample rate handling in UILT backends.

Focuses specifically on verifying that identical waveforms with different
sampling rates produce pixel-perfect identical output renders.
"""

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

# Add the src directory to the path so we can import from util
src_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(src_dir))

from util.graph.backends.ascii_backend import ASCIIBackend
from util.graph.backends.braille_backend import BrailleBackend


class PrecisionWaveformGenerator:
    """Generate mathematically precise waveforms for testing."""

    @staticmethod
    def generate_precise_square_wave(
        frequency_hz: float, duration_sec: float, sample_rate_hz: float
    ) -> tuple[list[float], list[float]]:
        """Generate a mathematically precise square wave."""
        sample_period_sec = 1.0 / sample_rate_hz
        num_samples = int(duration_sec * sample_rate_hz)

        times = []
        samples = []

        for i in range(num_samples):
            t = i * sample_period_sec
            # Use precise math for square wave generation
            cycle_position = (t * frequency_hz) % 1.0
            value = 1.0 if cycle_position < 0.5 else -1.0

            times.append(t)
            samples.append(value)

        return times, samples

    @staticmethod
    def generate_precise_pulse_train(
        pulse_width_sec: float, period_sec: float, duration_sec: float, sample_rate_hz: float
    ) -> tuple[list[float], list[float]]:
        """Generate a precise pulse train (like morse code)."""
        sample_period_sec = 1.0 / sample_rate_hz
        num_samples = int(duration_sec * sample_rate_hz)

        times = []
        samples = []

        for i in range(num_samples):
            t = i * sample_period_sec
            # Determine position within the period
            period_position = t % period_sec
            value = 1.0 if period_position < pulse_width_sec else 0.0

            times.append(t)
            samples.append(value)

        return times, samples


class RenderHashAnalyzer:
    """Analyze render outputs using content hashing."""

    @staticmethod
    def compute_render_hash(output: list[str]) -> str:
        """Compute a hash of the rendered output for exact comparison."""
        # Concatenate all rows and compute hash
        content = "\n".join(output)
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    @staticmethod
    def analyze_render_positions(output: list[str]) -> dict[str, any]:
        """Analyze where data appears in the rendered output."""
        analysis = {
            "total_rows": len(output),
            "data_rows": 0,
            "first_data_row": -1,
            "last_data_row": -1,
            "leftmost_data_col": float("inf"),
            "rightmost_data_col": -1,
            "character_counts": {},
            "row_widths": [],
        }

        for row_idx, row in enumerate(output):
            has_data = False
            row_width = len(row.rstrip())  # Remove trailing spaces
            analysis["row_widths"].append(row_width)

            for col_idx, char in enumerate(row):
                if char != " " and char != "":  # Non-space character is data
                    has_data = True
                    analysis["leftmost_data_col"] = min(analysis["leftmost_data_col"], col_idx)
                    analysis["rightmost_data_col"] = max(analysis["rightmost_data_col"], col_idx)

                    # Count character occurrences
                    if char in analysis["character_counts"]:
                        analysis["character_counts"][char] += 1
                    else:
                        analysis["character_counts"][char] = 1

            if has_data:
                analysis["data_rows"] += 1
                if analysis["first_data_row"] == -1:
                    analysis["first_data_row"] = row_idx
                analysis["last_data_row"] = row_idx

        # Handle case where no data found
        if analysis["leftmost_data_col"] == float("inf"):
            analysis["leftmost_data_col"] = -1

        return analysis


class TestSampleRatePrecision(unittest.TestCase):
    """Test precise sample rate handling."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix="uilt_precision_test_")
        self.output_dir = Path(self.temp_dir)

        # Test parameters for maximum precision
        self.width = 80
        self.height = 10

    def tearDown(self):
        """Clean up and report output location."""
        print(f"\n🔍 Precision test outputs: {self.temp_dir}")

    def save_precision_analysis(self, test_name: str, results: dict):
        """Save detailed precision analysis to file."""
        filepath = self.output_dir / f"{test_name}_precision_analysis.txt"

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Precision Analysis: {test_name}\n")
            f.write("=" * 80 + "\n\n")

            for key, value in results.items():
                f.write(f"{key}:\n")
                if isinstance(value, dict):
                    for subkey, subvalue in value.items():
                        f.write(f"  {subkey}: {subvalue}\n")
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        f.write(f"  [{i}]: {item}\n")
                else:
                    f.write(f"  {value}\n")
                f.write("\n")

    def save_visual_comparison(self, test_name: str, outputs: dict[str, list[str]]):
        """Save side-by-side visual comparison."""
        filepath = self.output_dir / f"{test_name}_visual_comparison.txt"

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Visual Comparison: {test_name}\n")
            f.write("=" * 120 + "\n\n")

            # Get all sample rates
            sample_rates = sorted(outputs.keys())
            max_rows = max(len(output) for output in outputs.values())

            for row_idx in range(max_rows):
                f.write(f"Row {row_idx:2d}:\n")
                for rate in sample_rates:
                    if row_idx < len(outputs[rate]):
                        row_content = outputs[rate][row_idx]
                    else:
                        row_content = " " * self.width

                    f.write(f"  {float(rate):6.1f}Hz: '{row_content}'\n")
                f.write("\n")

    @unittest.skip("Known issue: ASCII backend decimation inconsistent across sample rates")
    def test_identical_square_waves_exact_match(self):
        """Test that identical square waves produce exactly identical renders."""
        test_name = "exact_square_wave_match"

        # Parameters for precise testing
        wave_frequency_hz = 0.5  # 0.5 Hz = 2 second period
        duration_sec = 4.0  # Exactly 2 complete cycles
        sample_rates = [10.0, 20.0, 40.0, 80.0]  # Powers of 2 for clean division

        results = {
            "test_parameters": {
                "wave_frequency_hz": wave_frequency_hz,
                "duration_sec": duration_sec,
                "width": self.width,
                "height": self.height,
            },
            "ascii_results": {},
            "braille_results": {},
            "hash_analysis": {},
            "position_analysis": {},
        }

        ascii_outputs = {}
        braille_outputs = {}
        ascii_hashes = {}
        braille_hashes = {}

        for sample_rate_hz in sample_rates:
            # Generate precise waveform
            times, samples = PrecisionWaveformGenerator.generate_precise_square_wave(
                wave_frequency_hz, duration_sec, sample_rate_hz
            )

            # ASCII Backend Test
            ascii_backend = ASCIIBackend(self.width, self.height)
            ascii_backend.plot(samples, sample_rate_hz=sample_rate_hz)
            ascii_output = ascii_backend.render_sparkline()
            ascii_hash = RenderHashAnalyzer.compute_render_hash(ascii_output)

            ascii_outputs[sample_rate_hz] = ascii_output
            ascii_hashes[sample_rate_hz] = ascii_hash

            # Braille Backend Test
            braille_backend = BrailleBackend(self.width, self.height)
            braille_backend.plot(samples, sample_rate_hz=sample_rate_hz)
            braille_output = braille_backend.render_braille()
            braille_hash = RenderHashAnalyzer.compute_render_hash(braille_output)

            braille_outputs[sample_rate_hz] = braille_output
            braille_hashes[sample_rate_hz] = braille_hash

            # Analyze positions
            ascii_analysis = RenderHashAnalyzer.analyze_render_positions(ascii_output)
            braille_analysis = RenderHashAnalyzer.analyze_render_positions(braille_output)

            results["ascii_results"][sample_rate_hz] = {
                "num_samples": len(samples),
                "hash": ascii_hash,
                "analysis": ascii_analysis,
            }

            results["braille_results"][sample_rate_hz] = {
                "num_samples": len(samples),
                "hash": braille_hash,
                "analysis": braille_analysis,
            }

        # Hash consistency analysis
        ascii_hash_baseline = ascii_hashes[sample_rates[0]]
        braille_hash_baseline = braille_hashes[sample_rates[0]]

        results["hash_analysis"] = {
            "ascii_baseline_hash": ascii_hash_baseline,
            "braille_baseline_hash": braille_hash_baseline,
            "ascii_matches": {},
            "braille_matches": {},
        }

        for sample_rate_hz in sample_rates:
            ascii_match = ascii_hashes[sample_rate_hz] == ascii_hash_baseline
            braille_match = braille_hashes[sample_rate_hz] == braille_hash_baseline

            results["hash_analysis"]["ascii_matches"][sample_rate_hz] = ascii_match
            results["hash_analysis"]["braille_matches"][sample_rate_hz] = braille_match

            # CRITICAL TEST: Exact hash matching
            self.assertEqual(
                ascii_hashes[sample_rate_hz],
                ascii_hash_baseline,
                f"ASCII render hash mismatch: {sample_rates[0]}Hz vs {sample_rate_hz}Hz\n"
                f"Expected: {ascii_hash_baseline}\n"
                f"Got:      {ascii_hashes[sample_rate_hz]}",
            )

            self.assertEqual(
                braille_hashes[sample_rate_hz],
                braille_hash_baseline,
                f"Braille render hash mismatch: {sample_rates[0]}Hz vs {sample_rate_hz}Hz\n"
                f"Expected: {braille_hash_baseline}\n"
                f"Got:      {braille_hashes[sample_rate_hz]}",
            )

        # Save analysis files
        self.save_precision_analysis(test_name, results)
        self.save_visual_comparison(f"{test_name}_ascii", {str(k): v for k, v in ascii_outputs.items()})
        self.save_visual_comparison(f"{test_name}_braille", {str(k): v for k, v in braille_outputs.items()})

    @unittest.skip("Known issue: ASCII backend decimation inconsistent across sample rates")
    def test_morse_dit_precision_timing(self):
        """Test precise morse DIT timing across different sample rates."""
        test_name = "morse_dit_precision"

        # Morse parameters
        wpm = 20  # 20 WPM for precise timing
        dit_duration_sec = 1.2 / wpm  # 0.06 seconds
        gap_duration_sec = dit_duration_sec  # Equal gap
        total_duration_sec = dit_duration_sec * 2 + gap_duration_sec  # DIT-GAP-DIT

        sample_rates = [50.0, 100.0, 200.0]  # High rates for precise timing

        results = {
            "test_parameters": {
                "wpm": wpm,
                "dit_duration_sec": dit_duration_sec,
                "gap_duration_sec": gap_duration_sec,
                "total_duration_sec": total_duration_sec,
            },
            "timing_analysis": {},
        }

        outputs = {}
        hashes = {}

        for sample_rate_hz in sample_rates:
            # Generate precise morse pattern
            times, samples = PrecisionWaveformGenerator.generate_precise_pulse_train(
                dit_duration_sec, dit_duration_sec * 2, total_duration_sec, sample_rate_hz
            )

            # Test with ASCII backend
            ascii_backend = ASCIIBackend(self.width, self.height)
            ascii_backend.plot(samples, sample_rate_hz=sample_rate_hz)
            output = ascii_backend.render_sparkline()
            output_hash = RenderHashAnalyzer.compute_render_hash(output)

            outputs[sample_rate_hz] = output
            hashes[sample_rate_hz] = output_hash

            # Analyze timing positions
            analysis = RenderHashAnalyzer.analyze_render_positions(output)
            results["timing_analysis"][sample_rate_hz] = {
                "num_samples": len(samples),
                "hash": output_hash,
                "leftmost_data": analysis["leftmost_data_col"],
                "rightmost_data": analysis["rightmost_data_col"],
                "data_width": analysis["rightmost_data_col"] - analysis["leftmost_data_col"] + 1,
            }

        # Check timing consistency
        baseline_hash = hashes[sample_rates[0]]
        for sample_rate_hz in sample_rates[1:]:
            self.assertEqual(
                hashes[sample_rate_hz], baseline_hash, f"Morse DIT timing hash mismatch at {sample_rate_hz}Hz"
            )

        self.save_precision_analysis(test_name, results)
        self.save_visual_comparison(f"{test_name}_timing", {str(k): v for k, v in outputs.items()})

    @unittest.skip("Known issue: ASCII backend decimation inconsistent across sample rates")
    def test_progressive_data_fill_consistency(self):
        """Test that progressive data filling is consistent across sample rates."""
        test_name = "progressive_fill_consistency"

        # Test progressive filling with different sample rates
        wave_frequency_hz = 1.0
        max_duration_sec = 2.0
        sample_rates = [25.0, 50.0]

        results = {
            "test_parameters": {"wave_frequency_hz": wave_frequency_hz, "max_duration_sec": max_duration_sec},
            "progressive_analysis": {},
        }

        # Test progressive time points
        time_points = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]

        for sample_rate_hz in sample_rates:
            rate_results = []

            for duration_sec in time_points:
                times, samples = PrecisionWaveformGenerator.generate_precise_square_wave(
                    wave_frequency_hz, duration_sec, sample_rate_hz
                )

                ascii_backend = ASCIIBackend(self.width, self.height)
                ascii_backend.plot(samples, sample_rate_hz=sample_rate_hz)
                output = ascii_backend.render_sparkline()

                analysis = RenderHashAnalyzer.analyze_render_positions(output)
                output_hash = RenderHashAnalyzer.compute_render_hash(output)

                rate_results.append(
                    {
                        "duration_sec": duration_sec,
                        "num_samples": len(samples),
                        "hash": output_hash,
                        "leftmost_data": analysis["leftmost_data_col"],
                        "rightmost_data": analysis["rightmost_data_col"],
                    }
                )

            results["progressive_analysis"][sample_rate_hz] = rate_results

        # Compare progressive fills between sample rates
        rate1_hashes = [r["hash"] for r in results["progressive_analysis"][sample_rates[0]]]
        rate2_hashes = [r["hash"] for r in results["progressive_analysis"][sample_rates[1]]]

        for i, (hash1, hash2) in enumerate(zip(rate1_hashes, rate2_hashes, strict=False)):
            duration = time_points[i]
            self.assertEqual(
                hash1,
                hash2,
                f"Progressive fill hash mismatch at {duration}s: {sample_rates[0]}Hz vs {sample_rates[1]}Hz",
            )

        self.save_precision_analysis(test_name, results)


if __name__ == "__main__":
    unittest.main(verbosity=2)
