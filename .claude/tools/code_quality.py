#!/usr/bin/env python3
"""
<DATE>2025-09-08</DATE>

Comprehensive code quality pipeline for Python projects.

This module provides a unified interface to run code formatting, linting,
type checking, and testing tools in a coordinated pipeline. Integrates
ruff, mypy, pytest, and coverage reporting.

Example usage:
    python .claude/tools/code_quality.py --fix
    python .claude/tools/code_quality.py --fix --report --verbose
"""

import argparse
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


class CodeQualityPipeline:
    """
    Manages comprehensive code quality checking and reporting.
    
    This class orchestrates multiple code quality tools in a logical
    sequence, providing detailed reporting and error handling for
    each step of the pipeline.
    """
    
    def __init__(self, cfg_dict: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the code quality pipeline.
        
        Args:
            cfg_dict: Configuration dictionary with pipeline settings
        """
        # STEP_1: Initialize logging first
        self.logger = logging.getLogger(__name__)
        
        # STEP_2: Configuration management
        self.cfg_dict = self._apply_config_defaults(cfg_dict or {})
        
        self.logger.info("CodeQualityPipeline initialized with config: %s", self.cfg_dict)
    
    def _apply_config_defaults(self, cfg_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Apply configuration defaults and log missing keys."""
        defaults = {
            "source_dirs": ["src"],
            "test_dirs": ["tests"],
            "ruff_config": "pyproject.toml",
            "mypy_config": "pyproject.toml", 
            "pytest_config": "pyproject.toml",
            "coverage_threshold": 80,
            "fail_fast": True,
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
    
    def run_command(self, cmd: List[str], step_name: str, verbose: bool = False) -> bool:
        """
        Run a command and handle output/errors.
        
        Args:
            cmd: Command and arguments to run
            step_name: Human-readable name for logging
            verbose: Whether to show command output
            
        Returns:
            True if command succeeded, False otherwise
        """
        self.logger.info("Running %s: %s", step_name, " ".join(cmd))
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=not verbose,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                self.logger.info("%s completed successfully", step_name)
                if verbose and result.stdout:
                    print(result.stdout)
                return True
            else:
                self.logger.error("%s failed with return code %d", step_name, result.returncode)
                if result.stderr:
                    print(f"Error: {result.stderr}", file=sys.stderr)
                if result.stdout:
                    print(result.stdout)
                return False
                
        except FileNotFoundError:
            self.logger.error("%s tool not found: %s", step_name, cmd[0])
            print(f"Error: {cmd[0]} not installed or not in PATH", file=sys.stderr)
            return False
        except Exception as e:
            self.logger.exception("%s failed with exception: %s", step_name, e)
            print(f"Error running {step_name}: {e}", file=sys.stderr)
            return False
    
    def format_code(self, verbose: bool = False) -> bool:
        """
        Run code formatting with ruff.
        
        Args:
            verbose: Show detailed output
            
        Returns:
            True if formatting succeeded
        """
        cmd = ["ruff", "format", "."]
        return self.run_command(cmd, "Code formatting", verbose)
    
    def lint_code(self, fix: bool = False, verbose: bool = False) -> bool:
        """
        Run code linting with ruff.
        
        Args:
            fix: Apply auto-fixes where possible
            verbose: Show detailed output
            
        Returns:
            True if linting passed
        """
        cmd = ["ruff", "check", "."]
        if fix:
            cmd.append("--fix")
        
        return self.run_command(cmd, "Code linting", verbose)
    
    def type_check(self, verbose: bool = False) -> bool:
        """
        Run type checking with mypy.
        
        Args:
            verbose: Show detailed output
            
        Returns:
            True if type checking passed
        """
        cmd = ["mypy", "."]
        return self.run_command(cmd, "Type checking", verbose)
    
    def run_tests(self, coverage: bool = False, verbose: bool = False) -> bool:
        """
        Run tests with pytest.
        
        Args:
            coverage: Include coverage reporting
            verbose: Show detailed output
            
        Returns:
            True if tests passed
        """
        cmd = ["pytest"]
        
        if coverage:
            cmd.extend([
                "--cov=src",
                "--cov-report=term",
                "--cov-report=html:htmlcov"
            ])
        
        if verbose:
            cmd.append("-v")
        else:
            cmd.append("-q")
        
        return self.run_command(cmd, "Test execution", verbose)
    
    def generate_reports(self, verbose: bool = False) -> bool:
        """
        Generate additional quality reports.
        
        Args:
            verbose: Show detailed output
            
        Returns:
            True if report generation succeeded
        """
        success = True
        
        # Generate coverage report if not already done
        if Path("htmlcov").exists():
            self.logger.info("Coverage report available at htmlcov/index.html")
        
        # Could add more reporting tools here (bandit, complexity, etc.)
        
        return success
    
    def run_pipeline(
        self,
        fix: bool = False,
        coverage: bool = False,
        verbose: bool = False,
        report: bool = False
    ) -> bool:
        """
        Run the complete code quality pipeline.
        
        Args:
            fix: Apply auto-fixes where possible
            coverage: Include coverage reporting
            verbose: Show detailed output
            report: Generate additional reports
            
        Returns:
            True if all steps passed
        """
        self.logger.info("Starting code quality pipeline")
        
        steps = [
            ("Format code", lambda: self.format_code(verbose)),
            ("Lint code", lambda: self.lint_code(fix, verbose)),
            ("Type check", lambda: self.type_check(verbose)),
            ("Run tests", lambda: self.run_tests(coverage, verbose)),
        ]
        
        if report:
            steps.append(("Generate reports", lambda: self.generate_reports(verbose)))
        
        failed_steps = []
        
        for step_name, step_func in steps:
            print(f"🔄 {step_name}...")
            
            if step_func():
                print(f"✅ {step_name} - PASSED")
            else:
                print(f"❌ {step_name} - FAILED")
                failed_steps.append(step_name)
                
                if self.cfg_dict["fail_fast"]:
                    break
        
        if failed_steps:
            self.logger.error("Pipeline failed at steps: %s", failed_steps)
            print(f"\n❌ Pipeline FAILED. Failed steps: {', '.join(failed_steps)}")
            return False
        else:
            self.logger.info("Pipeline completed successfully")
            print("\n✅ All quality checks PASSED!")
            return True


def setup_logging() -> None:
    """Configure logging with file output and appropriate levels."""
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(".claude/tools/code_quality.log", mode="a"),
        ]
    )


def main() -> int:
    """Main entry point for command-line usage."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    parser = argparse.ArgumentParser(
        description="Comprehensive code quality pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python .claude/tools/code_quality.py
  python .claude/tools/code_quality.py --fix --verbose
  python .claude/tools/code_quality.py --fix --report --coverage
        """
    )
    
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Auto-fix issues where possible"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true", 
        help="Include coverage reporting"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output"
    )
    
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate additional reports"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        pipeline = CodeQualityPipeline()
        success = pipeline.run_pipeline(
            fix=args.fix,
            coverage=args.coverage,
            verbose=args.verbose,
            report=args.report
        )
        return 0 if success else 1
        
    except Exception as e:
        logger.error("Pipeline execution failed: %s", e)
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())