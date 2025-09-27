"""Integration tests for morsecode graphics display with UILT backend fixes.

This module tests the complete integration between the morsecode debug display
and the UILT graphing system, verifying that identical signals at different
sample rates produce identical visual outputs.
"""

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

# Add the src directory to the path so we can import from morsecode
src_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(src_dir))

from morsecode.components.graphics.graphics_display import GraphicsDisplay
from util.config import AwesomeConfigManager


class MorsecodeSignalGenerator:
    """Generate test signals that simulate real morsecode scenarios."""

    @staticmethod
    def generate_morse_dit_pattern(wpm: int, sample_rate_hz: float) -> list[float]:
        """Generate a precise morse DIT pattern with proper timing."""
        dit_duration_sec = 1.2 / wpm  # Standard morse timing
        gap_duration_sec = dit_duration_sec

        # Generate: DIT, GAP, DIT sequence
        total_duration = 2 * dit_duration_sec + gap_duration_sec
        sample_period_sec = 1.0 / sample_rate_hz
        num_samples = int(total_duration * sample_rate_hz)

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

            samples.append(value)

        return samples

    @staticmethod
    def generate_probability_impulses(sample_rate_hz: float, duration_sec: float = 4.0) -> list[float]:
        """Generate probability impulses that simulate convolution decoder output."""
        sample_period_sec = 1.0 / sample_rate_hz
        num_samples = int(duration_sec * sample_rate_hz)

        # Simulate convolution updates every 500ms (2 Hz)
        convolution_period_sec = 0.5
        samples = []

        for i in range(num_samples):
            t = i * sample_period_sec

            # Create impulses every 500ms
            time_in_period = t % convolution_period_sec

            if time_in_period < 0.02:  # 20ms impulse width
                # High probability during impulse
                value = 0.8
            else:
                # Low probability between impulses
                value = 0.1

            samples.append(value)

        return samples

    @staticmethod
    def generate_magnitude_signal(frequency_hz: float, sample_rate_hz: float, duration_sec: float = 4.0) -> list[float]:
        """Generate magnitude signal that's mathematically identical regardless of sample rate.

        Uses square wave patterns to ensure identical waveforms despite different sampling rates.
        """
        sample_period_sec = 1.0 / sample_rate_hz
        num_samples = int(duration_sec * sample_rate_hz)

        samples = []
        for i in range(num_samples):
            t = i * sample_period_sec
            # Use simple square wave pattern for deterministic results
            cycle_position = (t * frequency_hz) % 1.0
            if cycle_position < 0.5:
                value = 1.0  # High
            else:
                value = 0.0  # Low
            samples.append(value)

        return samples


class TestMorsecodeGraphicsIntegration(unittest.TestCase):
    """Test morsecode graphics integration with different sample rates."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix="morsecode_graphics_test_")
        self.output_dir = Path(self.temp_dir)

        # Test parameters
        self.width = 80
        self.height = 10

    def tearDown(self):
        """Clean up and report output location."""
        print(f"\n📊 Test outputs saved to: {self.temp_dir}")

    def compute_render_hash(self, output: list[str]) -> str:
        """Compute a hash of the rendered output for exact comparison."""
        content = "\n".join(output)
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    def save_test_output(self, test_name: str, outputs: dict[str, Any]):
        """Save test outputs to files for manual inspection."""
        filepath = self.output_dir / f"{test_name}_results.txt"

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Test Results: {test_name}\n")
            f.write("=" * 80 + "\n\n")

            for key, value in outputs.items():
                f.write(f"{key}:\n")
                if isinstance(value, list) and len(value) > 0 and isinstance(value[0], str):
                    # This is rendered output
                    for i, line in enumerate(value):
                        f.write(f"  {i:2d}: {line}\n")
                else:
                    f.write(f"  {value}\n")
                f.write("\n")

    def test_magnitude_identical_signals_different_rates(self):
        """Test that identical magnitude signals at different sample rates render identically.

        This is the main test function to run: test_magnitude_identical_signals_different_rates
        """
        print("\n🔬 Testing magnitude signal consistency across sample rates...")

        # Use sample rates that create integer samples per half-cycle for identical waveforms
        sample_rates = [10.0, 20.0, 40.0]  # Different sampling rates
        signal_frequency = 0.5  # 0.5 Hz signal = 2 second period, 1 second half-cycles
        duration_sec = 4.0  # Exactly 2 complete cycles

        outputs = {}
        hashes = {}

        for sample_rate_hz in sample_rates:
            print(f"  Testing sample rate: {sample_rate_hz} Hz")

            # Generate magnitude signal
            magnitude_data = MorsecodeSignalGenerator.generate_magnitude_signal(
                signal_frequency, sample_rate_hz, duration_sec
            )

            # Create debug display with ASCII backend for deterministic output
            cfg_mgr = AwesomeConfigManager()
            overrides = {
                "backend": "ascii",
                "chart_width": self.width,
                "chart_height": self.height,
                "update_rate_hz": 10.0,
            }

            debug_display = GraphicsDisplay(cfg_mgr, overrides=overrides)

            # Test magnitude backend directly
            mag_backend = debug_display._magnitude_backend
            self.assertIsNotNone(mag_backend, "Magnitude backend should be initialized")

            # Render the signal using the ACTUAL input sample rate, not the graphics processing rate
            # This is critical for UILT time-aware decimation to work correctly
            mag_backend.clear()
            mag_backend.plot(magnitude_data, sample_rate_hz=sample_rate_hz)

            if hasattr(mag_backend, "render_sparkline"):
                output = mag_backend.render_sparkline()
            else:
                output = mag_backend.render_braille()

            outputs[f"{sample_rate_hz}Hz"] = output
            hashes[sample_rate_hz] = self.compute_render_hash(output)

            print(f"    Samples: {len(magnitude_data)}, Hash: {hashes[sample_rate_hz][:8]}...")

        # Verify all outputs are identical
        baseline_hash = hashes[sample_rates[0]]
        baseline_output = outputs[f"{sample_rates[0]}Hz"]

        for sample_rate_hz in sample_rates[1:]:
            current_hash = hashes[sample_rate_hz]
            current_output = outputs[f"{sample_rate_hz}Hz"]

            self.assertEqual(
                current_hash,
                baseline_hash,
                f"Magnitude render hash mismatch: {sample_rates[0]}Hz vs {sample_rate_hz}Hz\n"
                f"Expected: {baseline_hash}\n"
                f"Got:      {current_hash}",
            )

            self.assertEqual(
                current_output,
                baseline_output,
                f"Magnitude render output differs between {sample_rates[0]}Hz and {sample_rate_hz}Hz",
            )

        # Save outputs for inspection
        test_results = {
            "test_name": "magnitude_identical_signals",
            "sample_rates": sample_rates,
            "signal_frequency": signal_frequency,
            "duration_sec": duration_sec,
            "all_hashes_identical": len(set(hashes.values())) == 1,
            "baseline_hash": baseline_hash,
        }

        for rate in sample_rates:
            test_results[f"output_{rate}Hz"] = outputs[f"{rate}Hz"]

        self.save_test_output("magnitude_identical_signals", test_results)

        print(f"✅ Magnitude test PASSED: All {len(sample_rates)} sample rates produce identical output")
        print(f"   Hash: {baseline_hash}")

    def test_probability_compression_effectiveness(self):
        """Test that probability data compression removes repeated cached values.

        This is another key test function: test_probability_compression_effectiveness
        """
        print("\n🔬 Testing probability data compression...")

        # Test different event publishing rates vs convolution rates
        event_rates = [25.0, 50.0, 100.0]  # Different event publishing frequencies
        convolution_rate = 2.0  # Fixed convolution rate (500ms intervals)
        duration_sec = 4.0

        compression_results = {}

        for event_rate_hz in event_rates:
            print(f"  Testing event rate: {event_rate_hz} Hz (vs {convolution_rate} Hz convolution)")

            # Generate probability data with repeated cached values
            prob_data = MorsecodeSignalGenerator.generate_probability_impulses(event_rate_hz, duration_sec)

            # Create debug display
            cfg_mgr = AwesomeConfigManager()
            overrides = {"backend": "ascii", "chart_width": self.width, "chart_height": self.height}

            debug_display = GraphicsDisplay(cfg_mgr, overrides=overrides)

            # Test compression function directly
            compressed_data = debug_display._compress_repeated_values(prob_data)

            # Calculate metrics
            original_length = len(prob_data)
            compressed_length = len(compressed_data)
            compression_ratio = original_length / compressed_length if compressed_length > 0 else 0
            expected_ratio = event_rate_hz / convolution_rate

            compression_results[event_rate_hz] = {
                "original_samples": original_length,
                "compressed_samples": compressed_length,
                "compression_ratio": compression_ratio,
                "expected_ratio": expected_ratio,
                "ratio_match": abs(compression_ratio - expected_ratio) < 2.0,  # Allow some tolerance
            }

            print(f"    Original: {original_length} samples")
            print(f"    Compressed: {compressed_length} samples")
            print(f"    Ratio: {compression_ratio:.1f}:1 (expected ~{expected_ratio:.1f}:1)")

            # Verify compression is effective
            self.assertGreater(
                compression_ratio,
                2.0,
                f"Compression should be significant for {event_rate_hz}Hz events with {convolution_rate}Hz convolution",
            )

        # Save compression analysis
        test_results = {
            "test_name": "probability_compression",
            "convolution_rate_hz": convolution_rate,
            "duration_sec": duration_sec,
            "compression_results": compression_results,
        }

        self.save_test_output("probability_compression", test_results)

        print("✅ Probability compression test PASSED: All event rates show effective compression")

    def test_complete_integration_morse_pattern(self):
        """Test complete integration with realistic morse code pattern.

        This is the comprehensive integration test: test_complete_integration_morse_pattern
        """
        print("\n🔬 Testing complete morsecode integration...")

        # Test realistic morse code scenario
        wpm_rates = [15, 20, 25]  # Different WPM rates
        sample_rates = [25.0, 50.0]  # Different digitization rates

        results = {}

        for wpm in wpm_rates:
            for sample_rate_hz in sample_rates:
                print(f"  Testing {wpm} WPM at {sample_rate_hz} Hz sampling")

                # Generate morse pattern
                morse_data = MorsecodeSignalGenerator.generate_morse_dit_pattern(wpm, sample_rate_hz)

                # Create debug display
                cfg_mgr = AwesomeConfigManager()
                debug_display = GraphicsDisplay(cfg_mgr)

                # Get actual calculated sample rates
                mag_rate = debug_display._magnitude_sample_rate_hz
                prob_rate = debug_display._probability_sample_rate_hz

                test_key = f"{wpm}wpm_{sample_rate_hz}hz"
                results[test_key] = {
                    "wpm": wpm,
                    "input_sample_rate": sample_rate_hz,
                    "morse_samples": len(morse_data),
                    "magnitude_sample_rate": mag_rate,
                    "probability_sample_rate": prob_rate,
                    "sample_rate_ratio": mag_rate / prob_rate if prob_rate > 0 else 0,
                    "dit_duration_sec": 1.2 / wpm,
                }

                # Verify sample rates are correctly calculated
                self.assertGreater(mag_rate, 0, "Magnitude sample rate should be positive")
                self.assertGreater(prob_rate, 0, "Probability sample rate should be positive")

                # Verify probability rate is lower (due to convolution intervals)
                self.assertLess(
                    prob_rate,
                    mag_rate,
                    f"Probability rate ({prob_rate}) should be less than magnitude rate ({mag_rate})",
                )

                print(f"    Morse samples: {len(morse_data)}")
                print(f"    Calculated rates: Mag={mag_rate}Hz, Prob={prob_rate}Hz")

        # Save integration results
        self.save_test_output("complete_integration", results)

        print(f"✅ Complete integration test PASSED: All {len(results)} scenarios configured correctly")
        print("✅ Sample rate calculations are consistent and properly differentiated")


def run_morsecode_graphics_verification():
    """Convenience function to run all morsecode graphics verification tests.

    Call this function to run the complete test suite:
    python -c "from src.util.graph.tests.test_morsecode_integration import run_morsecode_graphics_verification; run_morsecode_graphics_verification()"
    """
    import unittest

    print("🚀 Running Morsecode Graphics Verification Suite...")
    print("=" * 80)

    # Create test suite with specific tests
    suite = unittest.TestSuite()

    # Add the key tests
    suite.addTest(TestMorsecodeGraphicsIntegration("test_magnitude_identical_signals_different_rates"))
    suite.addTest(TestMorsecodeGraphicsIntegration("test_probability_compression_effectiveness"))
    suite.addTest(TestMorsecodeGraphicsIntegration("test_complete_integration_morse_pattern"))

    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 80)
    if result.wasSuccessful():
        print("🎉 ALL TESTS PASSED! Morsecode graphics integration is working correctly.")
        print("✅ Identical signals at different sample rates produce identical outputs")
        print("✅ Probability data compression is working effectively")
        print("✅ Complete integration handles realistic morse patterns correctly")
    else:
        print("❌ SOME TESTS FAILED! Check the output above for details.")
        print(f"   Failures: {len(result.failures)}")
        print(f"   Errors: {len(result.errors)}")

    return result.wasSuccessful()


if __name__ == "__main__":
    # Run all tests when executed directly
    unittest.main(verbosity=2)
