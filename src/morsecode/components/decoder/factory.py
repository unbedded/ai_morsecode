"""Decoder factory for algorithm selection and performance comparison.

This module provides a clean factory interface for creating different
Morse decoder implementations based on configuration. Supports both
traditional pattern-based and convolution-based algorithms.
"""

from typing import Any

from util.config import AwesomeConfigManager
from util.logging import ComponentLogger

from .keys import CfgKey
from .schema import ConfigSchema


class DecoderFactory:
    """Factory for creating Morse decoder implementations."""

    @staticmethod
    def create(cfg_mgr: AwesomeConfigManager, overrides: dict[str, Any] | None = None):
        """Create a decoder implementation based on configuration.

        Args:
            cfg_mgr: Configuration manager
            overrides: Optional configuration overrides

        Returns:
            MorseDecoder implementation (satisfies Protocol interface)

        Raises:
            ValueError: If algorithm type is not supported
        """
        logger = ComponentLogger(__name__, cfg_mgr)

        # Register configuration and get decoder section
        cfg_mgr.register_enum_config("decoder", ConfigSchema)
        cfg_section = cfg_mgr.get_section("decoder")

        if overrides:
            cfg_section.apply_overrides(overrides)

        # Get algorithm selection from config
        algorithm = cfg_section.get_string(CfgKey.ALGORITHM)

        logger.info(f"Creating decoder with algorithm: {algorithm}")

        if algorithm == "pattern":
            from .pattern_decoder import PatternBasedMorseDecoder

            return PatternBasedMorseDecoder(cfg_mgr, overrides)
        elif algorithm == "convolution":
            from .convolution_adapter import ConvolutionMorseDecoder

            return ConvolutionMorseDecoder(cfg_mgr, overrides)
        else:
            raise ValueError(f"Unsupported decoder algorithm: {algorithm}. Supported: 'pattern', 'convolution'")

    @staticmethod
    def get_available_algorithms() -> list[str]:
        """Get list of available decoder algorithms.

        Returns:
            List of algorithm names that can be used with create()
        """
        return ["pattern", "convolution"]

    @staticmethod
    def create_all_algorithms(
        cfg_mgr: AwesomeConfigManager, base_overrides: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Create instances of all available algorithms for comparison.

        Args:
            cfg_mgr: Configuration manager
            base_overrides: Base configuration overrides

        Returns:
            Dictionary mapping algorithm names to decoder instances
        """
        logger = ComponentLogger(__name__, cfg_mgr)
        algorithms = {}

        for algorithm in DecoderFactory.get_available_algorithms():
            try:
                # Create algorithm-specific overrides
                algorithm_overrides = base_overrides.copy() if base_overrides else {}
                if "decoder" not in algorithm_overrides:
                    algorithm_overrides["decoder"] = {}
                algorithm_overrides["decoder"]["algorithm"] = algorithm

                decoder = DecoderFactory.create(cfg_mgr, algorithm_overrides)
                algorithms[algorithm] = decoder
                logger.info(f"Created {algorithm} decoder for comparison")

            except Exception as e:
                logger.warning(f"Failed to create {algorithm} decoder: {e}")

        return algorithms
