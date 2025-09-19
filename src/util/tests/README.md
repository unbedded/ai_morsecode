# UTIL Test Suite

## Future Development Phase

This directory is a placeholder for comprehensive unit tests of the `util` package.

### Planned Test Coverage

#### Configuration System Tests
- `test_config_manager.py` - AwesomeConfigManager functionality
- `test_config_validation.py` - CfgField validation and schema tests
- `test_config_profiles.py` - Profile override mechanism

#### Logging System Tests
- `test_component_logger.py` - ComponentLogger functionality
- `test_logging_security.py` - Secret redaction patterns
- `test_logging_performance.py` - Lazy evaluation verification

#### Integration Tests
- `test_config_logging_integration.py` - Config-driven log levels
- `test_util_examples.py` - Verify example code works

### Test Standards

When implementing tests, follow these guidelines:

- **Comprehensive Coverage**: Test all public APIs and edge cases
- **CLAUDE.md Compliance**: Use descriptive test names and docstrings
- **Performance Testing**: Verify lazy evaluation and thread safety
- **Security Testing**: Ensure secret redaction works correctly
- **Integration Testing**: Test config and logging work together

### Running Tests

```bash
# Future commands when tests are implemented:
pytest src/util/tests/ -v                    # Run all util tests
pytest src/util/tests/test_config_manager.py # Run specific test file
pytest src/util/tests/ --cov=src.util        # Run with coverage
```

### Test Data

The `fixtures/` directory will contain:
- Sample configuration files for testing
- Mock data for validation tests
- Security test patterns and examples

## YAGNI Note

These tests will be implemented when the util package requires modifications or
bug fixes. Following YAGNI principles, we don't write tests for stable code
that's working correctly.