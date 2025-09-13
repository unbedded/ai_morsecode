#!/usr/bin/env python3
"""
<DATE>2025-09-08</DATE>

Common bootstrap utilities for project template setup.

This module provides shared functionality for language-specific bootstrap
tools, including directory creation, git flow setup, and common file
operations used across Python, C++, and other language templates.

Example usage:
    from bootstrap_common import ProjectBootstrapper
    
    bootstrapper = ProjectBootstrapper("myproject", "John Doe")
    bootstrapper.create_directory_structure(["src", "tests", "docs"])
    bootstrapper.setup_git_flow()
"""

import logging
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional


class ProjectBootstrapper:
    """
    Common project bootstrapping functionality across languages.
    
    This class provides language-agnostic project setup operations
    including directory creation, git initialization, and common
    file management used by language-specific bootstrap tools.
    """
    
    def __init__(self, cfg_dict: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the project bootstrapper.
        
        Args:
            cfg_dict: Configuration dictionary with project settings
        """
        # STEP_1: Initialize logging first
        self.logger = logging.getLogger(__name__)
        
        # STEP_2: Configuration management
        self.cfg_dict = self._apply_config_defaults(cfg_dict or {})
        
        self.logger.info("ProjectBootstrapper initialized with config: %s", self.cfg_dict)
    
    def _apply_config_defaults(self, cfg_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Apply configuration defaults and log missing keys."""
        defaults = {
            "project_name": "myproject",
            "author": "Your Name",
            "email": "your.email@example.com",
            "license": "MIT",
            "create_git_repo": True,
            "setup_gitflow": True,
            "create_vscode_settings": True,
            "create_github_workflows": True,
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
    
    def create_directory_structure(self, directories: List[str]) -> bool:
        """
        Create project directory structure.
        
        Args:
            directories: List of directories to create
            
        Returns:
            True if successful
        """
        self.logger.info("Creating directory structure: %s", directories)
        
        try:
            for directory in directories:
                dir_path = Path(directory)
                dir_path.mkdir(parents=True, exist_ok=True)
                self.logger.debug("Created directory: %s", dir_path)
            
            print(f"✅ Created {len(directories)} directories")
            return True
            
        except Exception as e:
            error_msg = f"Failed to create directories: {e}"
            self.logger.exception(error_msg)
            print(f"❌ {error_msg}")
            return False
    
    def setup_git_repository(self) -> bool:
        """
        Initialize git repository and basic configuration.
        
        Returns:
            True if successful
        """
        if not self.cfg_dict["create_git_repo"]:
            self.logger.debug("Git repository creation disabled")
            return True
        
        try:
            # STEP_3: Initialize git repo
            import subprocess
            
            # Check if already a git repo
            if Path(".git").exists():
                self.logger.info("Git repository already exists")
                return True
            
            # Initialize repository
            subprocess.run(["git", "init"], check=True, capture_output=True)
            self.logger.info("Initialized git repository")
            
            # Create initial commit structure
            Path(".gitignore").touch()
            subprocess.run(["git", "add", ".gitignore"], check=True, capture_output=True)
            subprocess.run([
                "git", "commit", "-m", "Initial commit: Project structure"
            ], check=True, capture_output=True)
            
            print("✅ Git repository initialized")
            return True
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Git command failed: {e}"
            self.logger.error(error_msg)
            print(f"❌ {error_msg}")
            return False
        except Exception as e:
            error_msg = f"Failed to setup git repository: {e}"
            self.logger.exception(error_msg)
            print(f"❌ {error_msg}")
            return False
    
    def setup_git_flow(self) -> bool:
        """
        Configure git flow with standard branch structure.
        
        Returns:
            True if successful
        """
        if not self.cfg_dict["setup_gitflow"]:
            self.logger.debug("Git flow setup disabled")
            return True
        
        try:
            import subprocess
            
            # Check if git flow is available
            subprocess.run(["git", "flow", "version"], 
                          check=True, capture_output=True)
            
            # Initialize git flow with defaults
            # This will create develop branch and set up flow config
            process = subprocess.run([
                "git", "flow", "init", "-d"
            ], input="\n\n\n\n\n\n\n", text=True, capture_output=True)
            
            if process.returncode == 0:
                self.logger.info("Git flow initialized")
                print("✅ Git flow configured")
                return True
            else:
                self.logger.warning("Git flow init returned non-zero: %s", process.stderr)
                return False
            
        except subprocess.CalledProcessError:
            self.logger.warning("Git flow not available, skipping setup")
            print("⚠️ Git flow not installed, skipping configuration")
            return False
        except Exception as e:
            error_msg = f"Failed to setup git flow: {e}"
            self.logger.exception(error_msg)
            print(f"❌ {error_msg}")
            return False
    
    def create_gitignore(self, language_patterns: List[str]) -> bool:
        """
        Create .gitignore file with language-specific patterns.
        
        Args:
            language_patterns: Language-specific ignore patterns
            
        Returns:
            True if successful
        """
        try:
            # STEP_4: Common ignore patterns
            common_patterns = [
                "# IDE and Editor files",
                ".vscode/",
                ".idea/",
                "*.swp",
                "*.swo",
                "*~",
                "",
                "# OS generated files",
                ".DS_Store",
                ".DS_Store?",
                "._*",
                ".Spotlight-V100",
                ".Trashes",
                "ehthumbs.db",
                "Thumbs.db",
                "",
                "# Log files",
                "*.log",
                ".claude/tools/*.log",
                "",
            ]
            
            gitignore_content = "\n".join(common_patterns + language_patterns)
            
            Path(".gitignore").write_text(gitignore_content)
            self.logger.info("Created .gitignore with %d patterns", 
                           len(common_patterns + language_patterns))
            print("✅ Created .gitignore file")
            return True
            
        except Exception as e:
            error_msg = f"Failed to create .gitignore: {e}"
            self.logger.exception(error_msg)
            print(f"❌ {error_msg}")
            return False
    
    def create_vscode_settings(self) -> bool:
        """
        Create VS Code workspace settings.
        
        Returns:
            True if successful
        """
        if not self.cfg_dict["create_vscode_settings"]:
            self.logger.debug("VS Code settings creation disabled")
            return True
        
        try:
            vscode_dir = Path(".vscode")
            vscode_dir.mkdir(exist_ok=True)
            
            # STEP_5: Basic VS Code settings
            settings = {
                "files.trimTrailingWhitespace": True,
                "files.insertFinalNewline": True,
                "editor.formatOnSave": True,
                "editor.codeActionsOnSave": {
                    "source.organizeImports": True
                }
            }
            
            import json
            settings_file = vscode_dir / "settings.json"
            settings_file.write_text(json.dumps(settings, indent=4))
            
            self.logger.info("Created VS Code settings")
            print("✅ Created VS Code workspace settings")
            return True
            
        except Exception as e:
            error_msg = f"Failed to create VS Code settings: {e}"
            self.logger.exception(error_msg)
            print(f"❌ {error_msg}")
            return False
    
    def initialize_changelog(self) -> bool:
        """
        Create initial CHANGELOG.md file.
        
        Returns:
            True if successful
        """
        try:
            from datetime import datetime
            
            changelog_content = f'''# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure created on {datetime.now().strftime("%Y-%m-%d")}

### Changed
- Nothing yet

### Deprecated  
- Nothing yet

### Removed
- Nothing yet

### Fixed
- Nothing yet

### Security
- Nothing yet

## [0.1.0] - {datetime.now().strftime("%Y-%m-%d")}

### Added
- Initial release of {self.cfg_dict["project_name"]}
- Basic project structure and configuration
- Development tooling setup
'''
            
            Path("CHANGELOG.md").write_text(changelog_content)
            self.logger.info("Created initial CHANGELOG.md")
            print("✅ Created CHANGELOG.md")
            return True
            
        except Exception as e:
            error_msg = f"Failed to create CHANGELOG.md: {e}"
            self.logger.exception(error_msg)
            print(f"❌ {error_msg}")
            return False
    
    def copy_claude_directory(self, source_template_path: Optional[str] = None) -> bool:
        """
        Copy .claude directory from template.
        
        Args:
            source_template_path: Path to template .claude directory
            
        Returns:
            True if successful
        """
        try:
            if source_template_path and Path(source_template_path).exists():
                source_path = Path(source_template_path)
            else:
                # Use current .claude directory as template
                source_path = Path(".claude")
                
            if not source_path.exists():
                self.logger.warning("Source .claude directory not found: %s", source_path)
                return False
            
            target_path = Path(".claude")
            
            if target_path.exists():
                self.logger.info(".claude directory already exists, skipping copy")
                return True
            
            # STEP_6: Copy .claude directory structure
            shutil.copytree(source_path, target_path)
            
            self.logger.info("Copied .claude directory from %s", source_path)
            print("✅ Copied .claude directory")
            return True
            
        except Exception as e:
            error_msg = f"Failed to copy .claude directory: {e}"
            self.logger.exception(error_msg)
            print(f"❌ {error_msg}")
            return False
    
    def replace_placeholders(self, file_path: Path, replacements: Dict[str, str]) -> bool:
        """
        Replace placeholders in a file.
        
        Args:
            file_path: Path to file to process
            replacements: Dictionary of placeholder -> replacement mappings
            
        Returns:
            True if successful
        """
        try:
            if not file_path.exists():
                self.logger.warning("File not found for placeholder replacement: %s", file_path)
                return False
            
            content = file_path.read_text()
            
            # STEP_7: Replace all placeholders
            for placeholder, replacement in replacements.items():
                content = content.replace(placeholder, replacement)
            
            file_path.write_text(content)
            
            self.logger.debug("Replaced placeholders in %s: %s", file_path, list(replacements.keys()))
            return True
            
        except Exception as e:
            error_msg = f"Failed to replace placeholders in {file_path}: {e}"
            self.logger.exception(error_msg)
            return False

    def copy_language_specific_claude_md(self, language: str) -> bool:
        """
        Copy language-specific CLAUDE.md template to project root.

        Args:
            language: Programming language (python, cpp, rust, go, etc.)

        Returns:
            True if successful
        """
        try:
            template_name = f"CLAUDE-{language}.md"
            template_path = Path(f".claude/templates/{template_name}")
            target_path = Path("CLAUDE.md")

            if not template_path.exists():
                self.logger.error("Language-specific CLAUDE.md template not found: %s", template_path)
                print(f"❌ Template not found: {template_name}")
                return False

            # Copy template to project root
            shutil.copy2(template_path, target_path)

            self.logger.info("Copied language-specific CLAUDE.md template: %s", template_name)
            print(f"✅ Copied {language} CLAUDE.md standards")
            return True

        except Exception as e:
            error_msg = f"Failed to copy language-specific CLAUDE.md template: {e}"
            self.logger.exception(error_msg)
            print(f"❌ {error_msg}")
            return False


def setup_logging() -> None:
    """Configure logging with file output and appropriate levels."""
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(".claude/tools/bootstrap_common.log", mode="a"),
        ]
    )