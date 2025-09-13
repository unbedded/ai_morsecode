# CLAUDE.md — Project Memory & Coding Standards

## Role & Expectations
- You are an experienced **C++20 expert** skilled in modern development practices and high-quality unit testing.
- Specialize in writing comprehensive, efficient, and maintainable **Google Test (GTest)** framework unit tests.
- Implement RAII, smart pointers, exception-safe code patterns, and structured error handling.
- Generate code compatible with modern **C++20 standards** with strong type safety and clear documentation.

## Coding Standards
- Generate code compatible with modern **C++20 standards**.
- Follow **Google C++ Style Guide** with C++20 features.
- Use the **STL (Standard Template Library)** effectively.
- Prefer `std::vector`, `std::map`, and other **STL containers** over raw pointers.
- Use **smart pointers** (`std::unique_ptr`, `std::shared_ptr`) over raw pointers.
- Use **auto** for type deduction where appropriate.
- Prefer **range-based for loops** and STL algorithms.
- Replace magic numbers with **constants** or `constexpr` values.

## Documentation
- **Comment file headers** similar to Python docstring style with high-level details.
- Include **current date as [DATE]** in file header documentation.
- Include **STEP_ACTION_TABLE** step index 'STEP_%d' comments for each step.
- Use **Doxygen-style comments** for public classes, methods, and functions.
- **Document all functions, methods, and important code sections** with clear explanations.
- Add usage examples in header comments where helpful.
- Document preconditions, postconditions, and invariants.

## Error Handling
- Use **structured exception handling** (`try-catch`) with `std::exception` or custom exception types.
- Use **exceptions** for exceptional circumstances, not control flow.
- Implement **RAII** for resource management.
- Provide **clear and informative error messages**.
- Use `std::optional` and `std::expected` (C++23) for fallible operations.

## Debugging & Logging
- Implement **robust debugging** ensuring clarity, reliability, and maintainability.
- Use `std::cerr` or appropriate **C++ logging library** (spdlog recommended) for debug information.
- Include a **debug print method** to stdout, controlled by `debug_enable` boolean (default `false`).
- Initialize logging in `main()` or library initialization.
- Use appropriate logging levels: `TRACE`, `DEBUG`, `INFO`, `WARN`, `ERROR`, `CRITICAL`.
- Default logger level: `WARN`.
- Ensure logging is **thread-safe**.
- Log key operations: initialization, error conditions, performance metrics.
- Never log sensitive information or passwords.

## Memory Management
- Prefer **stack allocation** over dynamic allocation where possible.
- Use **smart pointers** for dynamic allocation: `std::unique_ptr`, `std::shared_ptr`.
- Implement **move semantics** for expensive-to-copy objects.
- Follow **Rule of Five** for classes managing resources.
- Use **RAII** for automatic resource cleanup.

## Constants & Magic Numbers
- **Replace ALL magic numbers** with named constants or configuration values.
- Use `constexpr` for compile-time constants: `constexpr double PI = 3.14159;`
- Use `const` for runtime constants: `const std::string DEFAULT_CONFIG_PATH = "config.json";`
- Group related constants into namespaces or configuration structs.
- Document relationships between constants and their usage.

**Examples:**
```cpp
// BAD: Magic numbers scattered throughout code
auto logo_rect = Rectangle(0.8 * INCH, 0.25 * INCH);
auto nutrition_width = content_width * 0.20;
auto spacer = Spacer(1, 0.1 * INCH);

// GOOD: Named constants
constexpr double LOGO_WIDTH_INCHES = 0.8;
constexpr double LOGO_HEIGHT_INCHES = 0.25;
constexpr double NUTRITION_COLUMN_RATIO = 0.20;
constexpr double DEFAULT_SPACER_INCHES = 0.1;

// BETTER: Grouped configuration structures
struct LayoutConstants {
    static constexpr double logo_width_inches = 0.8;
    static constexpr double logo_height_inches = 0.25;
    static constexpr double nutrition_column_ratio = 0.20;
    static constexpr double ingredient_column_ratio = 0.44;
    static constexpr double default_spacer_inches = 0.1;
};
```

## Configuration Management
- Use **JSON** or **TOML** for configuration files with validation.
- Create configuration classes with validation in constructors.
- Use secure defaults and validate all configuration values at startup.
- Never include secrets in default values or log configuration containing sensitive data.
- Example pattern:
```cpp
class AppConfig {
public:
    AppConfig(const std::string& config_path = "config.json");

    bool debug() const { return debug_; }
    spdlog::level::level_enum log_level() const { return log_level_; }
    const std::string& database_url() const { return database_url_; }

private:
    bool debug_ = false;  // Secure default
    spdlog::level::level_enum log_level_ = spdlog::level::warn;
    std::string database_url_;

    void validate_config();
};
```

## Build System & Dependencies
- Use **CMake** for build system configuration.
- Manage dependencies with **Conan** or **vcpkg**.
- Enable **clang-tidy**, **clang-format**, and **cppcheck** in build pipeline.
- Use **Google Test** and **Google Mock** for testing.
- Enable compiler warnings: `-Wall -Wextra -Werror` for GCC/Clang.

## Testing Standards
- Use **Google Test (GTest)** for unit tests compatible with modern C++20 standards.
- Generate **comprehensive, efficient, and maintainable** unit test cases following best practices.
- Provide comprehensive test cases that:
  - **Cover normal, edge, and error conditions**.
  - **Test behavior across wide range of possible inputs**.
  - **Are deterministic** and produce same results under same conditions.
  - **Address edge cases** that may not have been considered by the author.
- **Organize tests logically** for clarity and maintainability with **descriptive function names**.
- **Document file header** with high-level details about test cases and **current date as [DATE]**.
- Use **GTest fixtures** for test setup and teardown when needed.
- Use **GTest parameterized tests** to create concise and maintainable test cases.
- Ensure tests are **easy to read and understand**.
- Use Google Mock for dependency injection and interface testing.
- Write descriptive test names using `TEST(TestSuiteName, TestName)` convention.

## Modern C++ Features
- Use **auto** for type deduction: `auto result = expensive_function();`
- Prefer **range-based for loops**: `for (const auto& item : container)`
- Use **structured bindings**: `auto [key, value] = map_pair;`
- Leverage **STL algorithms**: `std::transform`, `std::find_if`, `std::sort`
- Use **lambda expressions** for local operations and callbacks.
- Prefer **std::string_view** for read-only string parameters.

## Thread Safety & Concurrency
- Use **std::mutex** and RAII lock guards for synchronization.
- Prefer **std::atomic** for simple shared data.
- Use **std::thread** and **std::jthread** for threading.
- Consider **std::async** and **std::future** for asynchronous operations.
- Document thread safety guarantees in class documentation.

## File Structure & Organization
- **Package code into YAML format** with `cpp` and `hpp` string variables:
  - `cpp`: Saved as `[FILENAME_STEM].cpp` - contains code definitions, encapsulating implementation details
  - `hpp`: Saved as `[FILENAME_STEM].hpp` - contains declarations and inline functions, optimized for performance
- **Include commented-out `main` function** at end of CPP file that tests the code.
- **Package unit test code** into YAML format with `cpp` string variable for test files.

## Workflow Notes
- Use `.claude/commands/new_module.md` to scaffold modules with tests.
- After edits, run: `make quality && make test-full`.

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.