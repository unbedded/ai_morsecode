"""UILT Debug Tools.

This module contains debugging and development tools for the UILT (Universal Interface
for Live Telemetry) library. These tools were used during development to:

- Debug Braille Unicode mapping and orientation issues
- Test backend functionality and resolution advantages
- Validate signal fidelity and timing characteristics
- Develop and test new rendering approaches

For production usage, use the examples in src.util.graph.examples instead.
For debugging and development, run the tools directly:

    python src/util/graph/debug/demo_clean_braille.py
    python src/util/graph/debug/test_braille_sine.py
"""

# Note: Debug tools are designed to be run as scripts, not imported
__all__ = []
