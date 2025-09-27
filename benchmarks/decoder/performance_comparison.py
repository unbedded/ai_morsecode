"""Performance comparison framework for decoder algorithms.

This module provides tools to benchmark and compare different decoder implementations
(pattern-based vs convolution) using standardized test data and metrics.

Example usage:
    ```python
    from benchmarks.decoder.performance_comparison import DecoderBenchmark
    from util.config import AwesomeConfigManager

    cfg_mgr = AwesomeConfigManager("morse.yaml")
    benchmark = DecoderBenchmark(cfg_mgr)

    # Run performance comparison
    results = benchmark.run_comparison()
    benchmark.print_results(results)
    ```
"""

import time
from dataclasses import dataclass
from typing import Any

from morsecode.components.decoder.factory import DecoderFactory
from util.config import AwesomeConfigManager
from util.logging import ComponentLogger


@dataclass
class BenchmarkResult:
    """Results from a single decoder benchmark run."""

    algorithm: str
    wpm: int
    accuracy_pct: float
    processing_time_ms: float
    characters_decoded: int
    errors_count: int
    memory_usage_mb: float


@dataclass
class BenchmarkConfig:
    """Configuration for benchmark execution."""

    algorithms: list[str]
    wpm_values: list[int]
    test_text: str
    iterations: int = 3
    warmup_iterations: int = 1


class DecoderBenchmark:
    """Performance benchmark framework for decoder algorithms.

    Compares pattern-based and convolution algorithms across different WPM values
    using standardized test data and performance metrics.
    """

    def __init__(self, cfg_mgr: AwesomeConfigManager):
        """Initialize decoder benchmark framework.

        Args:
            cfg_mgr: Configuration manager for decoder setup
        """
        self.logger = ComponentLogger(__name__, cfg_mgr)
        self._cfg_mgr = cfg_mgr

        # Default benchmark configuration
        self._default_config = BenchmarkConfig(
            algorithms=["pattern", "convolution"],
            wpm_values=[10, 15, 20, 25, 30],
            test_text="THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG",
            iterations=5,
            warmup_iterations=2,
        )

        self.logger.info("DecoderBenchmark initialized")

    def run_comparison(self, config: BenchmarkConfig = None) -> list[BenchmarkResult]:
        """Run performance comparison across all configured algorithms and WPM values.

        Args:
            config: Optional benchmark configuration (uses defaults if None)

        Returns:
            List of benchmark results for analysis
        """
        if config is None:
            config = self._default_config

        results = []

        self.logger.info("Starting decoder performance comparison")
        self.logger.info("Algorithms: %s", config.algorithms)
        self.logger.info("WPM values: %s", config.wpm_values)
        self.logger.info("Test text: %s", config.test_text)

        for algorithm in config.algorithms:
            for wpm in config.wpm_values:
                try:
                    result = self._benchmark_algorithm(algorithm, wpm, config)
                    results.append(result)

                    self.logger.info(
                        "Completed: %s @ %d WPM - Accuracy: %.1f%%, Time: %.1fms",
                        algorithm,
                        wpm,
                        result.accuracy_pct,
                        result.processing_time_ms,
                    )

                except Exception as e:
                    self.logger.exception("Error benchmarking %s @ %d WPM: %s", algorithm, wpm, e)

        self.logger.info("Performance comparison completed: %d results", len(results))
        return results

    def _benchmark_algorithm(self, algorithm: str, wpm: int, config: BenchmarkConfig) -> BenchmarkResult:
        """Benchmark a single algorithm at specific WPM.

        Args:
            algorithm: Algorithm name ("pattern" or "convolution")
            wpm: Words per minute for testing
            config: Benchmark configuration

        Returns:
            BenchmarkResult with performance metrics
        """
        # Create decoder with specific algorithm
        overrides = {"decoder": {"algorithm": algorithm, "wpm": wpm}}

        processing_times = []
        accuracy_scores = []

        # Run warmup iterations (not measured)
        for _ in range(config.warmup_iterations):
            decoder = DecoderFactory.create(self._cfg_mgr, overrides)
            self._run_decode_test(decoder, config.test_text)

        # Run measured iterations
        for _ in range(config.iterations):
            decoder = DecoderFactory.create(self._cfg_mgr, overrides)

            start_time = time.perf_counter()
            decoded_text, stats = self._run_decode_test(decoder, config.test_text)
            end_time = time.perf_counter()

            processing_time = (end_time - start_time) * 1000  # Convert to milliseconds
            processing_times.append(processing_time)

            # Calculate accuracy
            accuracy = self._calculate_accuracy(config.test_text, decoded_text)
            accuracy_scores.append(accuracy)

        # Calculate average metrics
        avg_processing_time = sum(processing_times) / len(processing_times)
        avg_accuracy = sum(accuracy_scores) / len(accuracy_scores)

        # Get final statistics
        decoder = DecoderFactory.create(self._cfg_mgr, overrides)
        _, final_stats = self._run_decode_test(decoder, config.test_text)

        return BenchmarkResult(
            algorithm=algorithm,
            wpm=wpm,
            accuracy_pct=avg_accuracy * 100,
            processing_time_ms=avg_processing_time,
            characters_decoded=final_stats.get("total_characters", 0),
            errors_count=len(config.test_text) - final_stats.get("total_characters", 0),
            memory_usage_mb=0.0,  # TODO: Implement memory measurement
        )

    def _run_decode_test(self, decoder, test_text: str) -> tuple[str, dict[str, Any]]:
        """Run decoding test with simulated timing data.

        Args:
            decoder: Decoder instance to test
            test_text: Text to simulate as morse code input

        Returns:
            Tuple of (decoded_text, statistics)
        """
        # TODO: Implement proper morse code simulation
        # For now, simulate processing by calling decoder methods

        # Simulate tone detection events based on text
        # This is a simplified simulation - real implementation would
        # convert text to morse timing patterns

        for char in test_text:
            if char == " ":
                # Simulate word spacing
                decoder.process_detection(False, 350.0)  # Word space duration
            elif char.isalpha():
                # Simulate character patterns (simplified)
                decoder.process_detection(True, 80.0)  # Dot
                decoder.process_detection(False, 80.0)  # Element space
                decoder.process_detection(True, 240.0)  # Dash
                decoder.process_detection(False, 240.0)  # Character space

        # Finalize decoding
        decoder.finalize()

        decoded_text = decoder.get_decoded_text()
        statistics = decoder.get_statistics()

        return decoded_text, statistics

    def _calculate_accuracy(self, expected: str, actual: str) -> float:
        """Calculate decoding accuracy as character-level match percentage.

        Args:
            expected: Original input text
            actual: Decoded output text

        Returns:
            Accuracy as a float between 0.0 and 1.0
        """
        if not expected:
            return 1.0 if not actual else 0.0

        # Simple character-by-character comparison
        matches = 0
        max_len = max(len(expected), len(actual))

        for i in range(max_len):
            exp_char = expected[i] if i < len(expected) else ""
            act_char = actual[i] if i < len(actual) else ""

            if exp_char.upper() == act_char.upper():
                matches += 1

        return matches / max_len if max_len > 0 else 1.0

    def print_results(self, results: list[BenchmarkResult]) -> None:
        """Print benchmark results in formatted table.

        Args:
            results: List of benchmark results to display
        """
        if not results:
            self.logger.warning("No benchmark results to display")
            return

        print("\n" + "=" * 80)
        print("DECODER PERFORMANCE COMPARISON RESULTS")
        print("=" * 80)
        print(f"{'Algorithm':<12} {'WPM':<4} {'Accuracy':<9} {'Time (ms)':<10} {'Chars':<6} {'Errors':<7}")
        print("-" * 80)

        # Group results by algorithm for easier comparison
        pattern_results = [r for r in results if r.algorithm == "pattern"]
        conv_results = [r for r in results if r.algorithm == "convolution"]

        # Print pattern results
        if pattern_results:
            print("Pattern-Based Algorithm:")
            for result in sorted(pattern_results, key=lambda x: x.wpm):
                print(
                    f"{'  ' + result.algorithm:<12} {result.wpm:<4} "
                    f"{result.accuracy_pct:<8.1f}% {result.processing_time_ms:<9.1f} "
                    f"{result.characters_decoded:<6} {result.errors_count:<7}"
                )

        # Print convolution results
        if conv_results:
            print("\nConvolution Algorithm:")
            for result in sorted(conv_results, key=lambda x: x.wpm):
                print(
                    f"{'  ' + result.algorithm:<12} {result.wpm:<4} "
                    f"{result.accuracy_pct:<8.1f}% {result.processing_time_ms:<9.1f} "
                    f"{result.characters_decoded:<6} {result.errors_count:<7}"
                )

        print("=" * 80)

        # Calculate and display summary statistics
        self._print_summary_stats(results)

    def _print_summary_stats(self, results: list[BenchmarkResult]) -> None:
        """Print summary statistics comparing algorithms.

        Args:
            results: List of benchmark results for analysis
        """
        if len(results) < 2:
            return

        # Group by algorithm
        by_algorithm = {}
        for result in results:
            if result.algorithm not in by_algorithm:
                by_algorithm[result.algorithm] = []
            by_algorithm[result.algorithm].append(result)

        print("\nSUMMARY STATISTICS:")
        print("-" * 40)

        for algorithm, algo_results in by_algorithm.items():
            avg_accuracy = sum(r.accuracy_pct for r in algo_results) / len(algo_results)
            avg_time = sum(r.processing_time_ms for r in algo_results) / len(algo_results)

            print(f"{algorithm.capitalize()} Algorithm:")
            print(f"  Average Accuracy: {avg_accuracy:.1f}%")
            print(f"  Average Time: {avg_time:.1f}ms")
            print(f"  Total Tests: {len(algo_results)}")
            print()


def main():
    """Run decoder performance comparison with default configuration."""
    from util.config import AwesomeConfigManager

    # Initialize configuration
    cfg_mgr = AwesomeConfigManager("morse.yaml")

    # Create and run benchmark
    benchmark = DecoderBenchmark(cfg_mgr)
    results = benchmark.run_comparison()

    # Display results
    benchmark.print_results(results)


if __name__ == "__main__":
    main()
