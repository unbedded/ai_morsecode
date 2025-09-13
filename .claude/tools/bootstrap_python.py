#!/usr/bin/env python3
"""
<DATE>2025-09-08</DATE>

Python project bootstrap tool using template system.

This module creates new Python projects from the template, replacing
placeholders with project-specific values and setting up the complete
development environment with Python-specific tools and configurations.

Example usage:
    python .claude/tools/bootstrap_python.py --package myproject --python 3.13 --author "John Doe"
    python .claude/tools/bootstrap_python.py --package web_service --install --create-venv
"""

import argparse
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from bootstrap_common import ProjectBootstrapper, setup_logging


class PythonProjectBootstrapper:
    """
    Bootstrap Python projects with complete development environment.
    
    This class creates Python projects following CLAUDE.md standards,
    including proper package structure, development tools, testing
    framework, and CI/CD pipeline setup.
    """
    
    def __init__(self, cfg_dict: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize Python project bootstrapper.
        
        Args:
            cfg_dict: Configuration dictionary with Python project settings
        """
        # STEP_1: Initialize logging first
        self.logger = logging.getLogger(__name__)
        
        # STEP_2: Configuration management  
        self.cfg_dict = self._apply_config_defaults(cfg_dict or {})
        
        # STEP_3: Initialize common bootstrapper
        self.common = ProjectBootstrapper(self.cfg_dict)
        
        self.logger.info("PythonProjectBootstrapper initialized with config: %s", self.cfg_dict)
    
    def _apply_config_defaults(self, cfg_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Apply Python-specific configuration defaults."""
        defaults = {
            "package_name": "myproject",
            "python_version": "3.13",
            "ruff_target": "py313",
            "mypy_version": "3.13",
            "author": "Your Name",
            "email": "your.email@example.com",
            "create_venv": False,
            "install_deps": False,
            "use_poetry": False,
            "include_fastapi": False,
            "include_cli": False,
        }
        
        for key, default_value in defaults.items():
            if key not in cfg_dict:
                cfg_dict[key] = default_value
                self.logger.debug("Applied Python default for missing key %s: %s", key, default_value)
        
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
    
    def create_python_directory_structure(self) -> bool:
        """
        Create Python-specific directory structure.
        
        Returns:
            True if successful
        """
        self.logger.info("Creating Python directory structure")
        
        python_dirs = [
            f"src/{self.cfg_dict['package_name']}",
            "tests",
            "docs",
            ".claude/commands",
            ".claude/tools", 
            ".github/workflows",
            ".vscode",
        ]
        
        return self.common.create_directory_structure(python_dirs)
    
    def create_python_gitignore(self) -> bool:
        """
        Create Python-specific .gitignore file.
        
        Returns:
            True if successful
        """
        python_patterns = [
            "# Python specific",
            "__pycache__/",
            "*.py[cod]",
            "*$py.class", 
            "",
            "# Distribution / packaging",
            ".Python",
            "build/",
            "develop-eggs/",
            "dist/",
            "downloads/",
            "eggs/",
            ".eggs/",
            "lib/",
            "lib64/",
            "parts/",
            "sdist/",
            "var/",
            "wheels/",
            "*.egg-info/",
            ".installed.cfg",
            "*.egg",
            "",
            "# PyInstaller",
            "*.manifest",
            "*.spec",
            "",
            "# Virtual environments",
            ".env",
            ".venv",
            "env/",
            "venv/",
            "ENV/",
            "env.bak/",
            "venv.bak/",
            "",
            "# Testing",
            ".tox/",
            ".coverage",
            ".coverage.*",
            ".cache",
            "nosetests.xml",
            "coverage.xml",
            "*.cover",
            ".hypothesis/",
            ".pytest_cache/",
            "htmlcov/",
            "",
            "# MyPy",
            ".mypy_cache/",
            ".dmypy.json",
            "dmypy.json",
            "",
            "# Ruff",
            ".ruff_cache/",
        ]
        
        return self.common.create_gitignore(python_patterns)
    
    def create_python_package_structure(self) -> bool:
        """
        Create Python package files and structure.
        
        Returns:
            True if successful
        """
        try:
            package_dir = Path(f"src/{self.cfg_dict['package_name']}")
            
            # STEP_4: Create __init__.py files
            (package_dir / "__init__.py").write_text(f'''"""
{self.cfg_dict["package_name"]} - Python package following CLAUDE.md standards.

This package provides [brief description of functionality].
"""

__version__ = "0.1.0"
__author__ = "{self.cfg_dict["author"]}"
''')
            
            # STEP_5: Create basic test file
            test_file = Path(f"tests/test_{self.cfg_dict['package_name']}.py")
            test_file.write_text(f'''"""
<DATE>2025-09-08</DATE>

Basic tests for {self.cfg_dict["package_name"]} package.

This test module provides initial test structure following CLAUDE.md
testing standards and pytest conventions.

Example usage:
    pytest tests/test_{self.cfg_dict["package_name"]}.py -v
"""

import pytest
from {self.cfg_dict["package_name"]} import __version__


def test_version():
    """Test that version is defined and valid."""
    assert __version__ is not None
    assert isinstance(__version__, str)
    assert len(__version__) > 0


def test_package_import():
    """Test that package can be imported successfully."""
    import {self.cfg_dict["package_name"]}
    assert {self.cfg_dict["package_name"]} is not None


class TestSanity:
    """Sanity test suite to ensure basic functionality."""
    
    def test_basic_functionality(self):
        """Test basic package functionality."""
        # Add your basic functionality tests here
        assert True  # Placeholder test
    
    def test_environment_setup(self):
        """Test that development environment is properly configured.""" 
        # Test that required dependencies are available
        import sys
        assert sys.version_info >= (3, 13)  # Minimum Python version
''')
            
            self.logger.info("Created Python package structure")
            print(f"✅ Created Python package: {self.cfg_dict['package_name']}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to create Python package structure: {e}"
            self.logger.exception(error_msg)
            print(f"❌ {error_msg}")
            return False
    
    def create_python_config_files(self) -> bool:
        """
        Create Python-specific configuration files.
        
        Returns:
            True if successful
        """
        try:
            # STEP_6: Create pyproject.toml (already exists, need to replace placeholders)
            replacements = {
                "__PKG__": self.cfg_dict["package_name"],
                "__RUFF_TARGET__": self.cfg_dict["ruff_target"], 
                "__MYPY_PY_VERSION__": self.cfg_dict["mypy_version"],
                "Your Name": self.cfg_dict["author"],
                "your.email@example.com": self.cfg_dict["email"],
            }
            
            # Replace placeholders in existing files (CLAUDE.md will be copied from template)
            config_files = [
                Path("pyproject.toml"),
            ]

            for config_file in config_files:
                if config_file.exists():
                    self.common.replace_placeholders(config_file, replacements)
            
            # STEP_7: Create requirements.txt if not using poetry
            if not self.cfg_dict["use_poetry"]:
                requirements = [
                    "# Development dependencies",
                    "pytest>=7.0.0",
                    "pytest-cov>=4.0.0", 
                    "mypy>=1.0.0",
                    "ruff>=0.1.0",
                    "pre-commit>=3.0.0",
                    "",
                    "# Optional dependencies",
                ]
                
                if self.cfg_dict["include_fastapi"]:
                    requirements.extend([
                        "fastapi>=0.100.0",
                        "uvicorn[standard]>=0.20.0",
                    ])
                
                if self.cfg_dict["include_cli"]:
                    requirements.extend([
                        "click>=8.0.0",
                        "rich>=13.0.0",
                    ])
                
                Path("requirements.txt").write_text("\n".join(requirements))
            
            self.logger.info("Created Python configuration files")
            print("✅ Created Python configuration files")
            return True
            
        except Exception as e:
            error_msg = f"Failed to create Python config files: {e}"
            self.logger.exception(error_msg)
            print(f"❌ {error_msg}")
            return False
    
    def create_virtual_environment(self) -> bool:
        """
        Create Python virtual environment.
        
        Returns:
            True if successful
        """
        if not self.cfg_dict["create_venv"]:
            self.logger.debug("Virtual environment creation disabled")
            return True
        
        try:
            venv_path = Path(".venv")
            
            if venv_path.exists():
                self.logger.info("Virtual environment already exists")
                return True
            
            # STEP_8: Create virtual environment
            subprocess.run([
                sys.executable, "-m", "venv", ".venv"
            ], check=True)
            
            self.logger.info("Created virtual environment")
            print("✅ Created virtual environment (.venv)")
            return True
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to create virtual environment: {e}"
            self.logger.error(error_msg)
            print(f"❌ {error_msg}")
            return False
    
    def install_dependencies(self) -> bool:
        """
        Install Python dependencies.
        
        Returns:
            True if successful
        """
        if not self.cfg_dict["install_deps"]:
            self.logger.debug("Dependency installation disabled")
            return True
        
        try:
            # STEP_9: Determine pip executable
            pip_cmd = [sys.executable, "-m", "pip"]
            
            if Path(".venv").exists():
                if sys.platform == "win32":
                    pip_cmd = [".venv/Scripts/python", "-m", "pip"]
                else:
                    pip_cmd = [".venv/bin/python", "-m", "pip"]
            
            # Install package in development mode
            subprocess.run([*pip_cmd, "install", "-e", "."], check=True)
            
            # Install development dependencies
            if Path("requirements.txt").exists():
                subprocess.run([*pip_cmd, "install", "-r", "requirements.txt"], check=True)
            
            self.logger.info("Installed Python dependencies")
            print("✅ Installed Python dependencies")
            return True
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to install dependencies: {e}"
            self.logger.error(error_msg)
            print(f"❌ {error_msg}")
            return False
    
    def bootstrap_python_project(self) -> bool:
        """
        Execute complete Python project bootstrap process.
        
        Returns:
            True if successful
        """
        self.logger.info("Starting Python project bootstrap")
        print(f"🐍 Bootstrapping Python project: {self.cfg_dict['package_name']}")
        
        steps = [
            ("Create directory structure", self.create_python_directory_structure),
            ("Setup git repository", self.common.setup_git_repository),
            ("Setup git flow", self.common.setup_git_flow),
            ("Create .gitignore", self.create_python_gitignore),
            ("Create package structure", self.create_python_package_structure),
            ("Create config files", self.create_python_config_files),
            ("Create VS Code settings", self.common.create_vscode_settings),
            ("Initialize changelog", self.common.initialize_changelog),
            ("Copy .claude directory", lambda: self.common.copy_claude_directory()),
            ("Copy Python CLAUDE.md standards", lambda: self.common.copy_language_specific_claude_md("python")),
            ("Create virtual environment", self.create_virtual_environment),
            ("Install dependencies", self.install_dependencies),
        ]
        
        failed_steps = []
        
        for step_name, step_func in steps:
            print(f"🔄 {step_name}...")
            
            if step_func():
                print(f"✅ {step_name} - COMPLETED")
            else:
                print(f"❌ {step_name} - FAILED")
                failed_steps.append(step_name)
        
        if failed_steps:
            self.logger.error("Bootstrap failed at steps: %s", failed_steps)
            print(f"\n❌ Bootstrap FAILED. Failed steps: {', '.join(failed_steps)}")
            return False
        else:
            self.logger.info("Python project bootstrap completed successfully")
            print(f"\n✅ Python project '{self.cfg_dict['package_name']}' bootstrapped successfully!")
            print("\nNext steps:")
            print("1. Activate virtual environment: source .venv/bin/activate")  
            print("2. Run quality check: /check-code --fix")
            print("3. Start development: /new-module your_module --with-tests")
            return True


def main() -> int:
    """Main entry point for command-line usage."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    parser = argparse.ArgumentParser(
        description="Bootstrap Python project from template",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python .claude/tools/bootstrap_python.py --package myproject --python 3.13
  python .claude/tools/bootstrap_python.py --package web_service --install --create-venv
  python .claude/tools/bootstrap_python.py --package api_service --author "John Doe" --include-fastapi
        """
    )
    
    parser.add_argument(
        "--package",
        required=True,
        help="Package name (replaces __PKG__ placeholder)"
    )
    
    parser.add_argument(
        "--python",
        default="3.13",
        help="Python version (default: 3.13)"
    )
    
    parser.add_argument(
        "--author",
        default="Your Name",
        help="Author name for project metadata"
    )
    
    parser.add_argument(
        "--email",
        default="your.email@example.com",
        help="Author email for project metadata"
    )
    
    parser.add_argument(
        "--create-venv",
        action="store_true",
        help="Create virtual environment"
    )
    
    parser.add_argument(
        "--install",
        action="store_true",
        dest="install_deps",
        help="Install dependencies after setup"
    )
    
    parser.add_argument(
        "--include-fastapi",
        action="store_true",
        help="Include FastAPI dependencies"
    )
    
    parser.add_argument(
        "--include-cli",
        action="store_true",
        help="Include CLI dependencies (click, rich)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Build configuration
    config = {
        "package_name": args.package,
        "python_version": args.python,
        "ruff_target": f"py{args.python.replace('.', '')}",
        "mypy_version": args.python,
        "author": args.author,
        "email": args.email,
        "create_venv": args.create_venv,
        "install_deps": args.install_deps,
        "include_fastapi": args.include_fastapi,
        "include_cli": args.include_cli,
    }
    
    try:
        bootstrapper = PythonProjectBootstrapper(config)
        success = bootstrapper.bootstrap_python_project()
        return 0 if success else 1
        
    except Exception as e:
        logger.error("Bootstrap execution failed: %s", e)
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())