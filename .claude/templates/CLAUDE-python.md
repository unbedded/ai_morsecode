# CLAUDE.md — Project Memory & Coding Standards

## Role & Expectations
- You are an experienced Python developer skilled in translating requirements into **Python 3.13.5**-compatible code.
- Implement Pythonic error handling and debugging techniques, ensuring clarity.
- Generate comprehensive, efficient, and maintainable pytest test cases following best practices.

## Coding Standards
- Adhere to **PEP8** and use **type hints** consistently.
- Use modern Python built-ins (`list`, `dict`, `tuple`) for type hints when possible.
- Use **named arguments** for functions with multiple parameters.
- Replace magic numbers with **constants**.

## Documentation
- Provide **verbose docstrings** for public classes, methods, and functions.
- Include clear explanations in module headers.
- Add example usage in docstrings where helpful.

## Error Handling
- Use Pythonic `try-except` blocks.
- Raise appropriate built-in or custom exceptions.
- Provide clear and informative error messages.
- Use `logging.exception()` to capture stack traces when errors occur.

## Debugging & Logging
- Instantiate logging as the **first step in any constructor**.
- Use the `logging` module with lazy `%` formatting.
- Configure logging with file output and timestamps.
- Use appropriate logging levels: `DEBUG` (details), `INFO` (events), `ERROR` (exceptions).
- Default logger level: `WARNING`.
- Ensure logging is **thread-safe**.
- Demonstrate logging for key operations such as input validation, cache access, and calculation steps.
- Avoid logging sensitive or redundant information.

## Security
- Never log or expose secrets, API keys, or sensitive data.
- Validate all inputs and sanitize user-provided data.
- Use secure defaults and fail securely.

## Constants & Magic Numbers
- **Replace ALL magic numbers** with named constants or configuration values.
- Use **ALL_CAPS** for module-level constants: `LOGO_WIDTH_INCHES = 0.8`
- Group related constants into dataclasses or configuration objects.
- Prefer configuration injection over hardcoded values, especially for shared constants.
- Document relationships between constants and their usage.

**Examples:**
```python
# BAD: Magic numbers scattered throughout code
logo_image = Image(path, width=0.8 * inch, height=0.25 * inch)
nutrition_width = content_width * 0.20
spacer = Spacer(1, 0.1 * inch)

# GOOD: Named constants at module level
LOGO_WIDTH_INCHES = 0.8
LOGO_HEIGHT_INCHES = 0.25
NUTRITION_COLUMN_RATIO = 0.20
DEFAULT_SPACER_INCHES = 0.1

# BETTER: Grouped configuration objects for shared constants
@dataclass
class LayoutConstants:
    logo_width_inches: float = 0.8
    logo_height_inches: float = 0.25
    nutrition_column_ratio: float = 0.20
    ingredient_column_ratio: float = 0.44
    default_spacer_inches: float = 0.1
```

**Shared Constants Architecture:**
- Create shared configuration classes for cross-module constants
- Use dependency injection to pass configuration objects to constructors
- Validate configuration values with Pydantic validators
- Avoid duplicating constants across modules

## Configuration Management
- Use **Pydantic Settings** for type-safe configuration with validation.
- Support multiple config sources: environment variables, `.env` files, and direct instantiation.
- Use secure defaults and validate all configuration values on startup.
- Never include secrets in default values or log configuration containing sensitive data.
- Example pattern:
```python
from pydantic import BaseSettings, Field, validator
from typing import Optional

class AppConfig(BaseSettings):
    debug: bool = False  # Secure default
    log_level: str = Field(default="WARNING", env="LOG_LEVEL")
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    api_key: Optional[str] = Field(default=None, env="API_KEY")

    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Invalid log level: {v}')
        return v.upper()

    class Config:
        env_file = ".env"
        case_sensitive = False
```
- Pass config objects to class constructors instead of raw dictionaries.
- Validate configuration on startup and fail fast with clear error messages.

## Testing Standards
- Generate comprehensive pytest test cases covering edge cases and all possible scenarios.
- Use pytest fixtures appropriately for setup and teardown.
- Use pytest parameterization for concise, readable, and maintainable test cases.
- Ensure tests are deterministic and produce consistent results.
- Test function behavior across wide range of inputs, including extreme and unexpected cases.
- Write descriptive test function names and organize tests logically.
- Include comprehensive docstrings in test files explaining test coverage and expectations.

## Workflow Notes
- Use `.claude/commands/new_module.md` to scaffold modules with tests.
- After edits, run: `make quality && make test-full`.

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.