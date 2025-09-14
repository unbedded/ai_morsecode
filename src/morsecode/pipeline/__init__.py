"""Pipeline components for orchestrating Morse code processing.

This package provides the dependency injection container and high-level
pipeline orchestration for combining audio sources, signal processors,
and decoders into a complete processing pipeline.
"""

from .container import Container, configure_global_container, get_container

__all__ = [
    "Container",
    "configure_global_container",
    "get_container",
]
