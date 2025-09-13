#!/usr/bin/env python3
"""
<DATE>2025-09-08</DATE>

PEP 440 compliant version management tool with GitFlow integration.

This module provides automated version bumping functionality that follows
Python's PEP 440 versioning specification with support for pre-release
identifiers (alpha, beta, rc) commonly used in GitFlow workflows.

Example usage:
    python .claude/tools/version_bump.py --bump patch
    python .claude/tools/version_bump.py --bump minor --pre-release alpha
    python .claude/tools/version_bump.py --bump major --pre-release beta
"""

import argparse
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


# STEP_1: Constants and configuration
VERSION_FILE: str = "VERSION"
CHANGELOG_FILE: str = "CHANGELOG.md"
VALID_BUMP_TYPES: Tuple[str, ...] = ("major", "minor", "patch")
VALID_PRE_RELEASE_TYPES: Tuple[str, ...] = ("alpha", "beta", "rc")
PRE_RELEASE_SHORTCUTS: Dict[str, str] = {"a": "alpha", "b": "beta", "rc": "rc"}


class VersionBumper:
    """
    Manages PEP 440 compliant version bumping with GitFlow integration.
    
    This class handles version parsing, validation, bumping, and changelog
    updates following semantic versioning principles with Python-specific
    pre-release identifier support.
    """
    
    def __init__(self, cfg_dict: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the VersionBumper with configuration.
        
        Args:
            cfg_dict: Configuration dictionary with version management settings
        """
        # STEP_2: Initialize logging first
        self.logger = logging.getLogger(__name__)
        
        # STEP_3: Configuration management
        self.cfg_dict = self._apply_config_defaults(cfg_dict or {})
        
        # STEP_4: Initialize paths and validation
        self.version_file = Path(self.cfg_dict["version_file"])
        self.changelog_file = Path(self.cfg_dict["changelog_file"])
        
        self.logger.info("VersionBumper initialized with config: %s", self.cfg_dict)
    
    def _apply_config_defaults(self, cfg_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Apply configuration defaults and log missing keys."""
        defaults = {
            "version_file": VERSION_FILE,
            "changelog_file": CHANGELOG_FILE,
            "git_tag_prefix": "v",
            "update_changelog": True,
            "validate_git_clean": True,
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
    
    def parse_version(self, version_str: str) -> Dict[str, Any]:
        """
        Parse PEP 440 compliant version string into components.
        
        Args:
            version_str: Version string to parse (e.g., "1.2.3a1", "2.0.0rc2")
            
        Returns:
            Dictionary with version components: major, minor, patch, pre_release_type, pre_release_num
            
        Raises:
            ValueError: If version string is invalid
        """
        # STEP_5: PEP 440 regex pattern for version parsing
        pattern = r"^(\d+)\.(\d+)\.(\d+)(?:(a|b|rc)(\d+))?$"
        match = re.match(pattern, version_str.strip())
        
        if not match:
            error_msg = f"Invalid PEP 440 version format: {version_str}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        major, minor, patch, pre_type, pre_num = match.groups()
        
        result = {
            "major": int(major),
            "minor": int(minor),
            "patch": int(patch),
            "pre_release_type": pre_type,
            "pre_release_num": int(pre_num) if pre_num else None,
        }
        
        self.logger.debug("Parsed version %s into components: %s", version_str, result)
        return result
    
    def format_version(self, components: Dict[str, Any]) -> str:
        """
        Format version components back into PEP 440 compliant string.
        
        Args:
            components: Dictionary with version components
            
        Returns:
            Formatted version string
        """
        base = f"{components['major']}.{components['minor']}.{components['patch']}"
        
        if components.get("pre_release_type") and components.get("pre_release_num") is not None:
            pre_release = f"{components['pre_release_type']}{components['pre_release_num']}"
            return f"{base}{pre_release}"
        
        return base
    
    def bump_version(self, current: str, bump_type: str, pre_release: Optional[str] = None) -> str:
        """
        Bump version according to semantic versioning rules.
        
        Args:
            current: Current version string
            bump_type: Type of bump (major, minor, patch)
            pre_release: Pre-release type (alpha, beta, rc) or None
            
        Returns:
            New version string
            
        Raises:
            ValueError: If bump_type or pre_release is invalid
        """
        if bump_type not in VALID_BUMP_TYPES:
            raise ValueError(f"Invalid bump type: {bump_type}. Must be one of {VALID_BUMP_TYPES}")
        
        if pre_release and pre_release not in VALID_PRE_RELEASE_TYPES:
            # Check shortcuts
            pre_release = PRE_RELEASE_SHORTCUTS.get(pre_release, pre_release)
            if pre_release not in VALID_PRE_RELEASE_TYPES:
                raise ValueError(f"Invalid pre-release type: {pre_release}. Must be one of {VALID_PRE_RELEASE_TYPES}")
        
        # STEP_6: Parse current version and apply bump
        components = self.parse_version(current)
        
        # Remove pre-release for main version bump
        if bump_type != "pre_release":
            components["pre_release_type"] = None
            components["pre_release_num"] = None
        
        # Apply version bump
        if bump_type == "major":
            components["major"] += 1
            components["minor"] = 0
            components["patch"] = 0
        elif bump_type == "minor":
            components["minor"] += 1
            components["patch"] = 0
        elif bump_type == "patch":
            components["patch"] += 1
        
        # Apply pre-release if specified
        if pre_release:
            components["pre_release_type"] = pre_release
            components["pre_release_num"] = 1
        
        new_version = self.format_version(components)
        self.logger.info("Bumped version %s -> %s (bump_type=%s, pre_release=%s)", 
                        current, new_version, bump_type, pre_release)
        
        return new_version
    
    def read_current_version(self) -> str:
        """
        Read current version from VERSION file.
        
        Returns:
            Current version string
            
        Raises:
            FileNotFoundError: If VERSION file doesn't exist
            ValueError: If VERSION file is empty or invalid
        """
        try:
            version = self.version_file.read_text().strip()
            if not version:
                raise ValueError("VERSION file is empty")
            
            # Validate format
            self.parse_version(version)
            
            self.logger.debug("Read current version: %s", version)
            return version
            
        except FileNotFoundError:
            error_msg = f"VERSION file not found: {self.version_file}"
            self.logger.error(error_msg)
            raise
        except Exception as e:
            error_msg = f"Failed to read current version: {e}"
            self.logger.exception(error_msg)
            raise ValueError(error_msg) from e
    
    def write_version(self, version: str) -> None:
        """
        Write new version to VERSION file.
        
        Args:
            version: New version string to write
        """
        try:
            self.version_file.write_text(version + "\n")
            self.logger.info("Updated VERSION file with: %s", version)
        except Exception as e:
            error_msg = f"Failed to write version to {self.version_file}: {e}"
            self.logger.exception(error_msg)
            raise
    
    def update_changelog(self, new_version: str) -> None:
        """
        Update CHANGELOG.md with new version entry.
        
        Args:
            new_version: New version string to add
        """
        if not self.cfg_dict["update_changelog"]:
            self.logger.debug("Changelog update disabled in config")
            return
        
        try:
            if not self.changelog_file.exists():
                self.logger.warning("CHANGELOG.md not found, skipping update")
                return
            
            # STEP_7: Read and update changelog
            content = self.changelog_file.read_text()
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Find the [Unreleased] section and add new version
            unreleased_pattern = r"(## \[Unreleased\].*?)(## \[)"
            replacement = f"\\1## [{new_version}] - {today}\n\n### Added\n- Version bump to {new_version}\n\n\\2"
            
            if "[Unreleased]" in content:
                updated_content = re.sub(unreleased_pattern, replacement, content, flags=re.DOTALL)
                self.changelog_file.write_text(updated_content)
                self.logger.info("Updated CHANGELOG.md with version %s", new_version)
            else:
                self.logger.warning("Could not find [Unreleased] section in CHANGELOG.md")
                
        except Exception as e:
            self.logger.exception("Failed to update changelog: %s", e)
            # Don't raise - changelog update is not critical
    
    def execute_bump(self, bump_type: str, pre_release: Optional[str] = None) -> str:
        """
        Execute complete version bump workflow.
        
        Args:
            bump_type: Type of version bump
            pre_release: Optional pre-release identifier
            
        Returns:
            New version string
        """
        self.logger.info("Starting version bump: bump_type=%s, pre_release=%s", bump_type, pre_release)
        
        # STEP_8: Execute complete workflow
        current_version = self.read_current_version()
        new_version = self.bump_version(current_version, bump_type, pre_release)
        
        self.write_version(new_version)
        self.update_changelog(new_version)
        
        self.logger.info("Version bump completed: %s -> %s", current_version, new_version)
        return new_version


def setup_logging() -> None:
    """Configure logging with file output and appropriate levels."""
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(".claude/tools/version_bump.log", mode="a"),
        ]
    )


def main() -> int:
    """Main entry point for command-line usage."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    parser = argparse.ArgumentParser(
        description="PEP 440 compliant version management tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python .claude/tools/version_bump.py --bump patch
  python .claude/tools/version_bump.py --bump minor --pre-release alpha
  python .claude/tools/version_bump.py --bump major --pre-release beta
        """
    )
    
    parser.add_argument(
        "--bump",
        required=True,
        choices=VALID_BUMP_TYPES,
        help="Type of version bump to perform"
    )
    
    parser.add_argument(
        "--pre-release",
        choices=VALID_PRE_RELEASE_TYPES + tuple(PRE_RELEASE_SHORTCUTS.keys()),
        help="Add pre-release identifier (alpha, beta, rc)"
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
        bumper = VersionBumper()
        new_version = bumper.execute_bump(args.bump, args.pre_release)
        print(f"Version updated to: {new_version}")
        return 0
        
    except Exception as e:
        logger.error("Version bump failed: %s", e)
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())