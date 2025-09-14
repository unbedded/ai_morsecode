"""Pipeline package for Morse code processing.

This package provides:
- Container: Dependency injection container
- PipelineBuilder: Fluent builder for creating pipelines
- PipelineExecutor: Main execution engine
"""

from .builder import PipelineBuilder
from .container import Container, configure_global_container, get_container
from .executor import PipelineExecutor

__all__ = [
    "Container",
    "get_container",
    "configure_global_container",
    "PipelineBuilder",
    "PipelineExecutor",
]
