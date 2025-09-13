#!/usr/bin/env python3
"""
<DATE>2025-09-08</DATE>

Module scaffolding tool following CLAUDE.md standards.

This module generates new Python modules and their corresponding test files
according to the project's coding standards defined in CLAUDE.md, including
proper logging, configuration management, and documentation patterns.

Example usage:
    python .claude/tools/module_scaffold.py user_manager
    python .claude/tools/module_scaffold.py auth_service --tests
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class ModuleScaffolder:
    """
    Generates Python modules following CLAUDE.md standards.
    
    This class creates properly structured Python modules with consistent
    patterns for logging, configuration management, error handling, and
    documentation as defined in the project standards.
    """
    
    def __init__(self, cfg_dict: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the module scaffolder.
        
        Args:
            cfg_dict: Configuration dictionary with scaffolding settings
        """
        # STEP_1: Initialize logging first
        self.logger = logging.getLogger(__name__)
        
        # STEP_2: Configuration management
        self.cfg_dict = self._apply_config_defaults(cfg_dict or {})
        
        self.logger.info("ModuleScaffolder initialized with config: %s", self.cfg_dict)
    
    def _apply_config_defaults(self, cfg_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Apply configuration defaults and log missing keys."""
        defaults = {
            "src_dir": "src",
            "test_dir": "tests", 
            "package_name": "__PKG__",  # Will be replaced by bootstrap
            "author": "Your Name",
            "create_tests": True,
            "include_main": False,
        }
        
        for key, default_value in defaults.items():
            if key not in cfg_dict:
                cfg_dict[key] = default_value
                self.logger.debug("Applied default for missing key %s: %s", key, default_value)
        
        return cfg_dict
    
    def get_cfg(self) -> Dict[str, Any]:
        """Return current configuration dictionary."""
        return self.cfg_dict.copy()
    
    def set_cfg(self, cfg_dict: Dict[str, Any]) -> None:
        """Update configuration with new values."""
        for key, value in cfg_dict.items():
            if key in self.cfg_dict:
                old_value = self.cfg_dict[key]
                self.cfg_dict[key] = value
                self.logger.info("Updated config %s: %s -> %s", key, old_value, value)
            else:
                self.logger.warning("Unknown config key ignored: %s", key)
    
    def generate_module_content(self, module_name: str, class_name: str) -> str:
        """
        Generate module content following CLAUDE.md standards.
        
        Args:
            module_name: Name of the module (snake_case)
            class_name: Name of the main class (PascalCase)
            
        Returns:
            Complete module source code
        """
        today = datetime.now().strftime("%Y-%m-%d")
        
        template = f'''"""
<DATE>{today}</DATE>

{class_name} module for handling {module_name.replace('_', ' ')} operations.

This module provides {class_name} class with comprehensive configuration
management, logging, and error handling following CLAUDE.md standards.

Example usage:
    from {self.cfg_dict["package_name"]}.{module_name} import {class_name}
    
    config = {{"param1": "value1", "param2": "value2"}}
    instance = {class_name}(config)
    result = instance.process_data(input_data)
"""

import logging
from typing import Any, Dict, List, Optional


class {class_name}:
    """
    Handles {module_name.replace('_', ' ')} operations with configuration management.
    
    This class provides a template for implementing business logic while
    following CLAUDE.md standards for logging, configuration, and error
    handling patterns.
    """
    
    def __init__(self, cfg_dict: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize {class_name} with configuration.
        
        Args:
            cfg_dict: Configuration dictionary for {module_name} operations
        """
        # STEP_1: Initialize logging as first step in constructor
        self.logger = logging.getLogger(__name__)
        
        # STEP_2: Configuration management with defaults
        self.cfg_dict = self._apply_config_defaults(cfg_dict or {{}})
        
        # STEP_3: Initialize instance variables
        self._initialize_state()
        
        self.logger.info("{class_name} initialized with config: %s", self.cfg_dict)
    
    def _apply_config_defaults(self, cfg_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Apply configuration defaults and log missing keys."""
        defaults = {{
            "param1": "default_value1",
            "param2": "default_value2",
            "max_retries": 3,
            "timeout_seconds": 30,
            "enable_caching": True,
        }}
        
        for key, default_value in defaults.items():
            if key not in cfg_dict:
                cfg_dict[key] = default_value
                self.logger.debug("Applied default for missing key %s: %s", key, default_value)
        
        return cfg_dict
    
    def get_cfg(self) -> Dict[str, Any]:
        """Return current configuration dictionary."""
        current_config = self.cfg_dict.copy()
        current_config.update({{
            "param1": self.cfg_dict["param1"],
            "param2": self.cfg_dict["param2"], 
        }})
        return current_config
    
    def set_cfg(self, cfg_dict: Dict[str, Any]) -> None:
        """Update configuration with new values."""
        for key, value in cfg_dict.items():
            if key in self.cfg_dict:
                old_value = self.cfg_dict[key]
                self.cfg_dict[key] = value
                self.logger.info("Updated config %s: %s -> %s", key, old_value, value)
            else:
                self.logger.warning("Unknown config key ignored: %s", key)
    
    def _initialize_state(self) -> None:
        """Initialize internal state variables."""
        # STEP_4: Initialize state based on configuration
        self._cache: Dict[str, Any] = {{}} if self.cfg_dict["enable_caching"] else None
        self._retry_count: int = 0
        
        self.logger.debug("Internal state initialized")
    
    def process_data(self, input_data: Any) -> Any:
        """
        Process input data according to configuration.
        
        Args:
            input_data: Data to be processed
            
        Returns:
            Processed data result
            
        Raises:
            ValueError: If input data is invalid
            RuntimeError: If processing fails after retries
        """
        self.logger.info("Processing data of type: %s", type(input_data).__name__)
        
        # STEP_5: Input validation with clear error messages
        if input_data is None:
            error_msg = "Input data cannot be None"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            # STEP_6: Main processing logic with retry mechanism
            for attempt in range(self.cfg_dict["max_retries"]):
                try:
                    result = self._perform_processing(input_data)
                    self.logger.info("Processing completed successfully on attempt %d", attempt + 1)
                    return result
                    
                except Exception as e:
                    self.logger.warning("Processing attempt %d failed: %s", attempt + 1, e)
                    if attempt == self.cfg_dict["max_retries"] - 1:
                        raise
                    
        except Exception as e:
            error_msg = f"Processing failed after {{self.cfg_dict['max_retries']}} attempts: {{e}}"
            self.logger.exception(error_msg)
            raise RuntimeError(error_msg) from e
    
    def _perform_processing(self, data: Any) -> Any:
        """
        Perform the actual processing logic.
        
        Args:
            data: Input data to process
            
        Returns:
            Processed result
        """
        # STEP_7: Implement specific business logic here
        self.logger.debug("Performing processing step")
        
        # Cache lookup if enabled
        if self._cache is not None:
            cache_key = str(hash(str(data)))
            if cache_key in self._cache:
                self.logger.debug("Cache hit for key: %s", cache_key)
                return self._cache[cache_key]
        
        # Placeholder processing - replace with actual logic
        processed_result = f"Processed: {{data}}"
        
        # Cache result if enabled
        if self._cache is not None:
            self._cache[cache_key] = processed_result
            self.logger.debug("Cached result for key: %s", cache_key)
        
        return processed_result
    
    def validate_input(self, data: Any) -> bool:
        """
        Validate input data meets requirements.
        
        Args:
            data: Data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        self.logger.debug("Validating input data")
        
        # STEP_8: Implement validation logic
        if data is None:
            return False
        
        # Add specific validation rules here
        return True
    
    def cleanup(self) -> None:
        """Clean up resources and state."""
        self.logger.info("Cleaning up {class_name} resources")
        
        if self._cache is not None:
            self._cache.clear()
            self.logger.debug("Cache cleared")
'''

        return template
    
    def generate_test_content(self, module_name: str, class_name: str) -> str:
        """
        Generate test file content for the module.
        
        Args:
            module_name: Name of the module being tested
            class_name: Name of the class being tested
            
        Returns:
            Complete test file source code
        """
        today = datetime.now().strftime("%Y-%m-%d")
        
        template = f'''"""
<DATE>{today}</DATE>

Unit tests for {class_name} module.

This test module provides comprehensive test coverage for {class_name}
following pytest conventions and CLAUDE.md testing standards.

Example usage:
    pytest tests/test_{module_name}.py -v
    pytest tests/test_{module_name}.py::TestSample::test_basic_functionality -v
"""

import pytest
from typing import Any, Dict
from unittest.mock import Mock, patch

from {self.cfg_dict["package_name"]}.{module_name} import {class_name}


class Test{class_name}:
    """Test suite for {class_name} class."""
    
    def test_initialization_default_config(self):
        """Test {class_name} initialization with default configuration."""
        instance = {class_name}()
        
        assert instance is not None
        config = instance.get_cfg()
        assert "param1" in config
        assert "param2" in config
    
    def test_initialization_custom_config(self):
        """Test {class_name} initialization with custom configuration.""" 
        custom_config = {{
            "param1": "custom_value1",
            "param2": "custom_value2",
            "max_retries": 5,
        }}
        
        instance = {class_name}(custom_config)
        config = instance.get_cfg()
        
        assert config["param1"] == "custom_value1"
        assert config["param2"] == "custom_value2"
        assert config["max_retries"] == 5
    
    def test_config_update(self):
        """Test configuration updates."""
        instance = {class_name}()
        
        new_config = {{"param1": "updated_value"}}
        instance.set_cfg(new_config)
        
        updated_config = instance.get_cfg()
        assert updated_config["param1"] == "updated_value"
    
    def test_process_data_success(self):
        """Test successful data processing."""
        instance = {class_name}()
        
        test_data = "test_input"
        result = instance.process_data(test_data)
        
        assert result is not None
        assert "Processed:" in str(result)
    
    def test_process_data_none_input(self):
        """Test processing with None input raises ValueError."""
        instance = {class_name}()
        
        with pytest.raises(ValueError, match="Input data cannot be None"):
            instance.process_data(None)
    
    def test_validate_input_valid(self):
        """Test input validation with valid data."""
        instance = {class_name}()
        
        assert instance.validate_input("valid_data") is True
        assert instance.validate_input({{"key": "value"}}) is True
    
    def test_validate_input_invalid(self):
        """Test input validation with invalid data."""
        instance = {class_name}()
        
        assert instance.validate_input(None) is False
    
    def test_caching_enabled(self):
        """Test caching functionality when enabled."""
        config = {{"enable_caching": True}}
        instance = {class_name}(config)
        
        test_data = "cached_test"
        
        # First call should process and cache
        result1 = instance.process_data(test_data)
        
        # Second call should use cache
        result2 = instance.process_data(test_data)
        
        assert result1 == result2
    
    def test_caching_disabled(self):
        """Test functionality when caching is disabled.""" 
        config = {{"enable_caching": False}}
        instance = {class_name}(config)
        
        test_data = "non_cached_test"
        result = instance.process_data(test_data)
        
        assert result is not None
    
    @patch('logging.getLogger')
    def test_logging_initialization(self, mock_logger):
        """Test that logging is properly initialized."""
        {class_name}()
        mock_logger.assert_called()
    
    def test_cleanup(self):
        """Test resource cleanup."""
        instance = {class_name}()
        
        # Should not raise any exceptions
        instance.cleanup()
    
    def test_retry_mechanism(self):
        """Test retry mechanism on processing failures."""
        instance = {class_name}()
        
        # Mock the internal processing to fail then succeed
        with patch.object(instance, '_perform_processing') as mock_process:
            mock_process.side_effect = [Exception("Temporary failure"), "Success"]
            
            result = instance.process_data("retry_test")
            
            assert result == "Success"
            assert mock_process.call_count == 2


# Integration tests
class Test{class_name}Integration:
    """Integration tests for {class_name}."""
    
    def test_end_to_end_workflow(self):
        """Test complete workflow from initialization to cleanup."""
        # Initialize with custom config
        config = {{
            "param1": "integration_test",
            "max_retries": 2,
            "enable_caching": True,
        }}
        
        instance = {class_name}(config)
        
        try:
            # Process data
            result = instance.process_data("integration_data")
            assert result is not None
            
            # Validate input
            assert instance.validate_input("valid_input") is True
            
            # Update config
            instance.set_cfg({{"param2": "updated_in_integration"}})
            updated_config = instance.get_cfg()
            assert updated_config["param2"] == "updated_in_integration"
            
        finally:
            # Cleanup
            instance.cleanup()


# Performance tests  
@pytest.mark.slow
class Test{class_name}Performance:
    """Performance tests for {class_name}."""
    
    def test_large_data_processing(self):
        """Test processing performance with large datasets."""
        instance = {class_name}()
        
        large_data = "x" * 10000  # 10KB string
        
        import time
        start_time = time.time()
        result = instance.process_data(large_data)
        end_time = time.time()
        
        assert result is not None
        assert end_time - start_time < 1.0  # Should complete within 1 second
    
    def test_cache_performance(self):
        """Test caching performance improvement."""
        config = {{"enable_caching": True}}
        instance = {class_name}(config)
        
        test_data = "performance_test_data"
        
        # Time first call (with processing)
        import time
        start_time = time.time()
        result1 = instance.process_data(test_data)
        first_call_time = time.time() - start_time
        
        # Time second call (should use cache)
        start_time = time.time()
        result2 = instance.process_data(test_data)
        second_call_time = time.time() - start_time
        
        assert result1 == result2
        # Cache should make second call faster (allowing some variance)
        assert second_call_time <= first_call_time + 0.001
'''

        return template
    
    def create_module(self, module_name: str, include_tests: bool = True) -> bool:
        """
        Create a new module with optional tests.
        
        Args:
            module_name: Name of the module to create (snake_case)
            include_tests: Whether to create test file
            
        Returns:
            True if creation succeeded
        """
        self.logger.info("Creating module: %s (include_tests=%s)", module_name, include_tests)
        
        # Validate module name
        if not module_name.isidentifier() or not module_name.islower():
            error_msg = f"Invalid module name: {module_name}. Must be valid Python identifier in snake_case"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Generate class name (PascalCase)
        class_name = ''.join(word.capitalize() for word in module_name.split('_'))
        
        try:
            # Create module file
            src_dir = Path(self.cfg_dict["src_dir"]) / self.cfg_dict["package_name"]
            src_dir.mkdir(parents=True, exist_ok=True)
            
            module_file = src_dir / f"{module_name}.py"
            module_content = self.generate_module_content(module_name, class_name)
            module_file.write_text(module_content)
            
            self.logger.info("Created module file: %s", module_file)
            print(f"✅ Created module: {module_file}")
            
            # Create test file if requested
            if include_tests:
                test_dir = Path(self.cfg_dict["test_dir"])
                test_dir.mkdir(parents=True, exist_ok=True)
                
                test_file = test_dir / f"test_{module_name}.py"
                test_content = self.generate_test_content(module_name, class_name)
                test_file.write_text(test_content)
                
                self.logger.info("Created test file: %s", test_file)
                print(f"✅ Created test file: {test_file}")
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to create module {module_name}: {e}"
            self.logger.exception(error_msg)
            print(f"❌ {error_msg}", file=sys.stderr)
            return False


def setup_logging() -> None:
    """Configure logging with file output and appropriate levels."""
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(".claude/tools/module_scaffold.log", mode="a"),
        ]
    )


def main() -> int:
    """Main entry point for command-line usage."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    parser = argparse.ArgumentParser(
        description="Generate Python modules following CLAUDE.md standards",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python .claude/tools/module_scaffold.py user_manager
  python .claude/tools/module_scaffold.py auth_service --tests
  python .claude/tools/module_scaffold.py data_processor --no-tests
        """
    )
    
    parser.add_argument(
        "module_name",
        help="Name of the module to create (snake_case)"
    )
    
    parser.add_argument(
        "--tests",
        action="store_true",
        dest="include_tests",
        default=True,
        help="Create test file (default: True)"
    )
    
    parser.add_argument(
        "--no-tests",
        action="store_false",
        dest="include_tests",
        help="Do not create test file"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        scaffolder = ModuleScaffolder()
        success = scaffolder.create_module(args.module_name, args.include_tests)
        return 0 if success else 1
        
    except Exception as e:
        logger.error("Module scaffolding failed: %s", e)
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())