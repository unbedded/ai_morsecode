"""Real-time output instrumentation for UILT backends.

Captures backend renders to files for detailed analysis and comparison.
Useful for debugging sample rate consistency and visual alignment issues.
"""

import json
import threading
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any


class OutputInstrumenter:
    """Instrument backend outputs for analysis."""

    def __init__(self, output_dir: str, max_captures_per_session: int = 1000):
        """Initialize output instrumenter.

        Args:
            output_dir: Directory to save captured outputs
            max_captures_per_session: Maximum captures to prevent disk overflow
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.max_captures = max_captures_per_session
        self.capture_count = 0
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Thread-safe capture queue
        self.capture_queue = deque(maxlen=max_captures_per_session)
        self._lock = threading.Lock()

        # Metadata tracking
        self.session_metadata = {
            "session_id": self.session_id,
            "start_time": datetime.now().isoformat(),
            "captures": [],
            "backend_stats": {},
        }

    def capture_render(self, backend_type: str, output: list[str], metadata: dict[str, Any]) -> str:
        """Capture a backend render with metadata.

        Args:
            backend_type: 'ascii' or 'braille'
            output: Rendered output lines
            metadata: Additional metadata (sample_rate, data_points, etc.)

        Returns:
            Capture ID for reference
        """
        if self.capture_count >= self.max_captures:
            return "CAPTURE_LIMIT_EXCEEDED"

        with self._lock:
            timestamp = datetime.now()
            capture_id = f"{self.session_id}_{backend_type}_{self.capture_count:04d}"

            capture_data = {
                "capture_id": capture_id,
                "backend_type": backend_type,
                "timestamp": timestamp.isoformat(),
                "timestamp_ms": int(timestamp.timestamp() * 1000),
                "output_lines": output.copy(),
                "metadata": metadata.copy(),
            }

            # Save individual capture file
            self._save_capture_file(capture_data)

            # Update session metadata
            self.session_metadata["captures"].append(
                {
                    "capture_id": capture_id,
                    "backend_type": backend_type,
                    "timestamp": timestamp.isoformat(),
                    "metadata": metadata,
                }
            )

            # Update backend stats
            if backend_type not in self.session_metadata["backend_stats"]:
                self.session_metadata["backend_stats"][backend_type] = {
                    "total_captures": 0,
                    "total_output_lines": 0,
                    "sample_rates_seen": set(),
                }

            stats = self.session_metadata["backend_stats"][backend_type]
            stats["total_captures"] += 1
            stats["total_output_lines"] += len(output)

            if "sample_rate_hz" in metadata:
                stats["sample_rates_seen"].add(metadata["sample_rate_hz"])

            self.capture_count += 1

            return capture_id

    def _save_capture_file(self, capture_data: dict):
        """Save individual capture to file."""
        capture_id = capture_data["capture_id"]
        backend_type = capture_data["backend_type"]

        # Create backend-specific subdirectory
        backend_dir = self.output_dir / backend_type
        backend_dir.mkdir(exist_ok=True)

        # Save as text file for easy viewing
        txt_file = backend_dir / f"{capture_id}.txt"
        with open(txt_file, "w", encoding="utf-8") as f:
            f.write(f"# Capture: {capture_id}\n")
            f.write(f"# Backend: {backend_type}\n")
            f.write(f"# Timestamp: {capture_data['timestamp']}\n")
            f.write(f"# Metadata: {json.dumps(capture_data['metadata'], indent=2)}\n")
            f.write("# " + "=" * 76 + "\n\n")

            for i, line in enumerate(capture_data["output_lines"]):
                f.write(f"{i:2d}: {line}\n")

        # Also save as JSON for programmatic analysis
        json_file = backend_dir / f"{capture_id}.json"
        # Convert sets to lists for JSON serialization
        json_data = capture_data.copy()
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

    def save_session_summary(self):
        """Save session summary with all captures."""
        # Convert sets to lists for JSON serialization
        summary = self.session_metadata.copy()
        for backend_type, stats in summary["backend_stats"].items():
            if "sample_rates_seen" in stats:
                stats["sample_rates_seen"] = sorted(list(stats["sample_rates_seen"]))

        summary["end_time"] = datetime.now().isoformat()
        summary["total_captures"] = self.capture_count

        summary_file = self.output_dir / f"session_summary_{self.session_id}.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        return summary_file

    def create_comparison_report(self, sample_rate1: float, sample_rate2: float) -> str:
        """Create a detailed comparison report between two sample rates.

        Args:
            sample_rate1: First sample rate to compare
            sample_rate2: Second sample rate to compare

        Returns:
            Path to comparison report file
        """
        report_file = self.output_dir / f"comparison_{sample_rate1}hz_vs_{sample_rate2}hz.txt"

        # Find captures for each sample rate
        captures_1 = []
        captures_2 = []

        for capture_info in self.session_metadata["captures"]:
            metadata = capture_info["metadata"]
            if metadata.get("sample_rate_hz") == sample_rate1:
                captures_1.append(capture_info)
            elif metadata.get("sample_rate_hz") == sample_rate2:
                captures_2.append(capture_info)

        with open(report_file, "w", encoding="utf-8") as f:
            f.write("# Sample Rate Comparison Report\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n")
            f.write(f"# Session: {self.session_id}\n")
            f.write("# " + "=" * 76 + "\n\n")

            f.write(f"Comparing {sample_rate1}Hz vs {sample_rate2}Hz:\n\n")

            f.write(f"Captures at {sample_rate1}Hz: {len(captures_1)}\n")
            for capture in captures_1:
                f.write(f"  - {capture['capture_id']} at {capture['timestamp']}\n")

            f.write(f"\nCaptures at {sample_rate2}Hz: {len(captures_2)}\n")
            for capture in captures_2:
                f.write(f"  - {capture['capture_id']} at {capture['timestamp']}\n")

            f.write("\n# Analysis:\n")
            f.write("# - Load capture files to compare render outputs\n")
            f.write("# - Check for identical patterns despite different sampling\n")
            f.write("# - Verify timing alignment and visual consistency\n")

        return str(report_file)


class InstrumentedBackendWrapper:
    """Wrapper that instruments any backend with output capture."""

    def __init__(self, backend, instrumenter: OutputInstrumenter, backend_type: str):
        """Wrap a backend with instrumentation.

        Args:
            backend: Original backend instance (ASCIIBackend or BrailleBackend)
            instrumenter: OutputInstrumenter instance
            backend_type: 'ascii' or 'braille'
        """
        self.backend = backend
        self.instrumenter = instrumenter
        self.backend_type = backend_type
        self._render_count = 0

    def plot(self, *args, **kwargs):
        """Delegate plot call to original backend."""
        return self.backend.plot(*args, **kwargs)

    def render_sparkline(self) -> list[str]:
        """Render and capture ASCII output."""
        if self.backend_type != "ascii":
            raise ValueError("render_sparkline only for ASCII backends")

        output = self.backend.render_sparkline()

        # Extract metadata for capture
        metadata = {
            "render_count": self._render_count,
            "backend_type": "ascii",
            "width": self.backend.width,
            "height": self.backend.height,
            "num_data_buffers": len(self.backend.data_buffers),
            "output_rows": len(output),
        }

        # Add sample rate if available
        if hasattr(self.backend, "data_buffers") and self.backend.data_buffers:
            first_buffer = self.backend.data_buffers[0]
            if hasattr(first_buffer, "time_axis") and first_buffer.time_axis:
                metadata["sample_rate_hz"] = 1.0 / first_buffer.time_axis.sample_period_sec
                metadata["num_samples"] = len(first_buffer.get_values())

        # Capture output
        capture_id = self.instrumenter.capture_render(self.backend_type, output, metadata)
        metadata["capture_id"] = capture_id

        self._render_count += 1
        return output

    def render_braille(self) -> list[str]:
        """Render and capture Braille output."""
        if self.backend_type != "braille":
            raise ValueError("render_braille only for Braille backends")

        output = self.backend.render_braille()

        # Extract metadata for capture
        metadata = {
            "render_count": self._render_count,
            "backend_type": "braille",
            "width": self.backend.width,
            "height": self.backend.height,
            "num_data_buffers": len(self.backend.data_buffers),
            "output_rows": len(output),
        }

        # Add sample rate if available
        if hasattr(self.backend, "data_buffers") and self.backend.data_buffers:
            first_buffer = self.backend.data_buffers[0]
            if hasattr(first_buffer, "time_axis") and first_buffer.time_axis:
                metadata["sample_rate_hz"] = 1.0 / first_buffer.time_axis.sample_period_sec
                metadata["num_samples"] = len(first_buffer.get_values())

        # Capture output
        capture_id = self.instrumenter.capture_render(self.backend_type, output, metadata)
        metadata["capture_id"] = capture_id

        self._render_count += 1
        return output

    def __getattr__(self, name):
        """Delegate all other attributes to the original backend."""
        return getattr(self.backend, name)


def create_instrumented_backends(output_dir: str, width: int = 80, height: int = 10):
    """Create instrumented ASCII and Braille backends for testing.

    Args:
        output_dir: Directory to save captured outputs
        width: Backend width
        height: Backend height

    Returns:
        Tuple of (ascii_backend, braille_backend, instrumenter)
    """
    from ..backends.ascii_backend import ASCIIBackend
    from ..backends.braille_backend import BrailleBackend

    instrumenter = OutputInstrumenter(output_dir)

    ascii_backend = ASCIIBackend(width, height)
    braille_backend = BrailleBackend(width, height)

    instrumented_ascii = InstrumentedBackendWrapper(ascii_backend, instrumenter, "ascii")
    instrumented_braille = InstrumentedBackendWrapper(braille_backend, instrumenter, "braille")

    return instrumented_ascii, instrumented_braille, instrumenter


if __name__ == "__main__":
    # Example usage
    import tempfile

    # Create test directory
    test_dir = tempfile.mkdtemp(prefix="uilt_instrumentation_test_")
    print(f"Test output directory: {test_dir}")

    # Create instrumented backends
    ascii_backend, braille_backend, instrumenter = create_instrumented_backends(test_dir)

    # Generate test data
    import math

    test_data = [math.sin(i * 0.1) for i in range(100)]

    # Test ASCII backend
    ascii_backend.plot(test_data, sample_rate_hz=10.0)
    ascii_output = ascii_backend.render_sparkline()
    print(f"ASCII output captured: {len(ascii_output)} lines")

    # Test Braille backend
    braille_backend.plot(test_data, sample_rate_hz=10.0)
    braille_output = braille_backend.render_braille()
    print(f"Braille output captured: {len(braille_output)} lines")

    # Save session summary
    summary_file = instrumenter.save_session_summary()
    print(f"Session summary saved: {summary_file}")

    print(f"\n📊 Instrumentation complete. Check outputs in: {test_dir}")
