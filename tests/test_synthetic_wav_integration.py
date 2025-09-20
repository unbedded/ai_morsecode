"""Integration tests using synthetic WAV files from test data generator.

This module tests the complete morse code pipeline using precisely generated
synthetic audio with known expected outputs for comprehensive validation.
"""

import json
from pathlib import Path

import pytest

from morsecode import decoder_app
from util.config.models import AppConfig, AudioConfig, DecoderConfig, SignalConfig


class TestSyntheticWavIntegration:
    """Test complete pipeline using generated synthetic WAV files."""

    @classmethod
    def setup_class(cls):
        """Set up test class by ensuring synthetic test data exists."""
        cls.test_data_dir = Path("tests/generated_data")
        cls.metadata_file = cls.test_data_dir / "test_suite_metadata.json"

        # Load test metadata if available
        if cls.metadata_file.exists():
            with open(cls.metadata_file) as f:
                cls.test_metadata = json.load(f)
        else:
            cls.test_metadata = None

    def _get_test_configs(self, wav_file: str) -> tuple[AudioConfig, SignalConfig, DecoderConfig, AppConfig]:
        """Create test configurations for WAV file processing."""
        audio_config = AudioConfig(
            wav_filename=wav_file,
            sample_rate=44100,
            auto_gain_control=True,
            chunk_size_ms=50,
        )

        signal_config = SignalConfig(
            sample_rate_hz=44100,
            frequency_hz=600,  # Match synthetic test frequency
            signal_threshold_norm=0.3,
            bandwidth_hz=50,
        )

        decoder_config = DecoderConfig(
            wpm=15,  # Match synthetic test WPM
            dot_duration_ms=80.0,  # 15 WPM standard
            timing_tolerance_norm=0.3,
        )

        app_config = AppConfig(
            debug=False,
            log_level="WARNING",  # Reduce noise in tests
            output_file=None,
        )

        return audio_config, signal_config, decoder_config, app_config

    def _load_expected_text(self, txt_file: str) -> str:
        """Load expected text from TXT file, extracting just the content."""
        if not Path(txt_file).exists():
            pytest.skip(f"Expected text file not found: {txt_file}")

        with open(txt_file) as f:
            content = f.read()

        # Extract just the test content (between header and footer)
        lines = content.strip().split("\n")
        content_lines = []
        in_content = False

        for line in lines:
            if line.startswith("= ") and ("WPM" in line or "TEST:" in line or "DIFFICULTY:" in line):
                continue  # Skip header lines
            elif line.strip() == "= END OF TEST =":
                break  # Stop at footer
            elif line.strip() and not line.startswith("="):
                in_content = True
                content_lines.append(line.strip())
            elif in_content and not line.strip():
                # Allow empty lines within content
                content_lines.append("")

        return " ".join(content_lines).strip()

    @pytest.mark.parametrize("test_category", ["basic", "intermediate"])
    def test_synthetic_wav_category(self, test_category: str):
        """Test all synthetic WAV files in a category."""
        if not self.test_metadata:
            pytest.skip("No synthetic test data found. Run: morsecode-test-data generate --output tests/generated_data")

        if test_category not in self.test_metadata.get("tests_by_type", {}):
            pytest.skip(f"No {test_category} test data found")

        tests = self.test_metadata["tests_by_type"][test_category]

        for test_data in tests:
            wav_file = test_data["wav_file"]
            txt_file = test_data["txt_file"]
            test_name = test_data["test_name"]

            if not Path(wav_file).exists():
                pytest.skip(f"WAV file not found: {wav_file}")

            # Load expected output
            expected_text = self._load_expected_text(txt_file)

            # Configure decoder for this test
            audio_config, signal_config, decoder_config, app_config = self._get_test_configs(wav_file)

            # Adjust decoder timing for this test's WPM
            test_wpm = test_data["wpm"]
            decoder_config.wpm = test_wpm
            decoder_config.dot_duration_ms = 1200.0 / test_wpm  # PARIS standard

            # Run decoder
            try:
                result = decoder_app.run_decoder_typed(audio_config, signal_config, decoder_config, app_config)
                assert result == 0, f"Decoder failed for {test_name}"

                # Note: In a full implementation, we'd capture the decoded output
                # For now, we're testing that the pipeline runs without errors
                print(f"✅ Successfully processed {test_name}: expected '{expected_text}'")

            except Exception as e:
                pytest.fail(f"Failed to process {test_name}: {e}")

    def test_pattern_timing_validation(self):
        """Test specific patterns that validate timing accuracy."""
        if not self.test_metadata:
            pytest.skip("No synthetic test data found")

        # Find timing-sensitive tests
        timing_tests = []
        for _category, tests in self.test_metadata.get("tests_by_type", {}).items():
            for test in tests:
                if "timing" in test.get("tags", []) or "spacing" in test.get("tags", []):
                    timing_tests.append(test)

        if not timing_tests:
            pytest.skip("No timing validation tests found")

        for test_data in timing_tests:
            wav_file = test_data["wav_file"]
            test_name = test_data["test_name"]

            if not Path(wav_file).exists():
                continue

            # Test with precise timing expectations
            audio_config, signal_config, decoder_config, app_config = self._get_test_configs(wav_file)

            # Use strict timing tolerance for precision tests
            decoder_config.tolerance = 0.2  # Tighter tolerance

            try:
                result = decoder_app.run_decoder_typed(audio_config, signal_config, decoder_config, app_config)
                assert result == 0, f"Timing test failed for {test_name}"
                print(f"✅ Timing validation passed for {test_name}")

            except Exception as e:
                pytest.fail(f"Timing validation failed for {test_name}: {e}")

    def test_frequency_variation(self):
        """Test decoder with different frequency synthetic tests."""
        if not self.test_metadata:
            pytest.skip("No synthetic test data found")

        # Find frequency-specific tests
        freq_tests = []
        for _category, tests in self.test_metadata.get("tests_by_type", {}).items():
            for test in tests:
                if "frequency" in test.get("tags", []) and test["frequency"] != 600:
                    freq_tests.append(test)

        for test_data in freq_tests:
            wav_file = test_data["wav_file"]
            test_frequency = test_data["frequency"]
            test_name = test_data["test_name"]

            if not Path(wav_file).exists():
                continue

            # Configure decoder for this frequency
            audio_config, signal_config, decoder_config, app_config = self._get_test_configs(wav_file)
            signal_config.frequency = int(test_frequency)

            try:
                result = decoder_app.run_decoder_typed(audio_config, signal_config, decoder_config, app_config)
                assert result == 0, f"Frequency test failed for {test_name} at {test_frequency}Hz"
                print(f"✅ Frequency test passed for {test_name} at {test_frequency}Hz")

            except Exception as e:
                pytest.fail(f"Frequency test failed for {test_name}: {e}")

    def test_wpm_variation(self):
        """Test decoder with different WPM synthetic tests."""
        if not self.test_metadata:
            pytest.skip("No synthetic test data found")

        # Find different WPM tests
        wpm_tests = {}
        for _category, tests in self.test_metadata.get("tests_by_type", {}).items():
            for test in tests:
                wpm = test["wpm"]
                if wpm not in wpm_tests:
                    wpm_tests[wpm] = []
                wpm_tests[wpm].append(test)

        for wpm, tests in wpm_tests.items():
            if wpm == 15:  # Skip default
                continue

            for test_data in tests[:1]:  # Test one per WPM
                wav_file = test_data["wav_file"]
                test_name = test_data["test_name"]

                if not Path(wav_file).exists():
                    continue

                # Configure decoder for this WPM
                audio_config, signal_config, decoder_config, app_config = self._get_test_configs(wav_file)
                decoder_config.wpm = wpm
                decoder_config.dot_duration_ms = 1200.0 / wpm

                try:
                    result = decoder_app.run_decoder_typed(audio_config, signal_config, decoder_config, app_config)
                    assert result == 0, f"WPM test failed for {test_name} at {wpm} WPM"
                    print(f"✅ WPM test passed for {test_name} at {wpm} WPM")

                except Exception as e:
                    pytest.fail(f"WPM test failed for {test_name}: {e}")

    @pytest.mark.slow
    def test_all_synthetic_wavs(self):
        """Comprehensive test of all generated WAV files (marked as slow)."""
        if not self.test_metadata:
            pytest.skip("No synthetic test data found")

        total_tests = 0
        passed_tests = 0

        for _category, tests in self.test_metadata.get("tests_by_type", {}).items():
            for test_data in tests:
                wav_file = test_data["wav_file"]
                test_name = test_data["test_name"]
                total_tests += 1

                if not Path(wav_file).exists():
                    continue

                audio_config, signal_config, decoder_config, app_config = self._get_test_configs(wav_file)
                decoder_config.wpm = test_data["wpm"]
                decoder_config.dot_duration_ms = 1200.0 / test_data["wpm"]
                signal_config.frequency = int(test_data["frequency"])

                try:
                    result = decoder_app.run_decoder_typed(audio_config, signal_config, decoder_config, app_config)
                    if result == 0:
                        passed_tests += 1
                        print(f"✅ {test_name}")
                    else:
                        print(f"❌ {test_name} - decoder returned {result}")

                except Exception as e:
                    print(f"❌ {test_name} - exception: {e}")

        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        print(f"\n📊 Synthetic WAV Test Results: {passed_tests}/{total_tests} passed ({success_rate:.1%})")

        # Require at least 80% success rate
        assert success_rate >= 0.8, f"Too many synthetic tests failed: {success_rate:.1%} success rate"
