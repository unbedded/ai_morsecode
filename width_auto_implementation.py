#!/usr/bin/env python3
"""Implementation plan for configurable width with AUTO option."""

import shutil


def resolve_display_width(config_width: str | int) -> int:
    """Resolve display width from configuration.

    Args:
        config_width: Either 'auto' for terminal detection or integer for fixed width

    Returns:
        Integer width in characters
    """
    if isinstance(config_width, str) and config_width.lower() == "auto":
        # AUTO mode: detect terminal size
        try:
            terminal_size = shutil.get_terminal_size()
            width = terminal_size.columns
            # Clamp to reasonable bounds for graphics display
            width = max(40, min(200, width))  # Same bounds as config validation
            return width
        except OSError:
            # Fallback if terminal size detection fails (e.g., non-interactive)
            return 80  # Safe default
    else:
        # Fixed width mode
        return int(config_width)


# Example usage scenarios:
test_cases = [
    ("auto", "Dynamic terminal detection"),
    (80, "Fixed 80-character width"),
    (120, "Fixed 120-character width for wide terminals"),
    (60, "Fixed 60-character width for narrow displays"),
]

print("🖥️  Display Width Resolution Test:")
print("=" * 50)

# Simulate different config values
current_terminal_width = shutil.get_terminal_size().columns
print(f"Current terminal: {current_terminal_width} columns\n")

for config_val, description in test_cases:
    resolved = resolve_display_width(config_val)
    print(f"Config: {config_val:>4} → Width: {resolved:>3} | {description}")

print("\n📋 Configuration Schema Update:")
print("""
debug_display:
  display_width_chars: "auto"  # or integer 40-200
  # "auto" = adapt to terminal size
  # integer = fixed width (40-200 range)
  # Recommended: "auto" for local dev, fixed for SSH/CI
""")

print("\n🎯 Benefits:")
print("✅ User choice: fixed predictability OR responsive adaptation")
print("✅ SSH-friendly: users can set fixed width for consistent remote experience")
print("✅ CI/automation: predictable output with fixed width")
print("✅ Local development: auto-adapts to terminal size changes")
