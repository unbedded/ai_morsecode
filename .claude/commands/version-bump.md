Bump project version using semantic versioning (language-agnostic): $ARGUMENTS

**Usage:** `/version-bump <level> [--pre-release <type>]`

**Required:**
- `<level>` - Version level to bump: `patch`, `minor`, `major`

**Optional:**
- `--pre-release <type>` - Add pre-release identifier: `alpha`, `beta`, `rc` (or shortcuts: `a`, `b`, `rc`)

**Examples:**
- `/version-bump patch` → 1.0.0 → 1.0.1
- `/version-bump minor` → 1.0.0 → 1.1.0
- `/version-bump major` → 1.0.0 → 2.0.0
- `/version-bump minor --pre-release alpha` → 1.0.0 → 1.1.0a1
- `/version-bump patch --pre-release beta` → 1.0.0 → 1.0.1b1

## Language-Agnostic Version Management

### **Universal Workflow:**
<!--
WHY LANGUAGE-AGNOSTIC VERSION MANAGEMENT:
Different languages have different version storage conventions:
- Python: pyproject.toml, __init__.py, setup.py
- C++: CMakeLists.txt, version.hpp, conanfile.txt
- Node.js: package.json
- Rust: Cargo.toml

The Makefile abstraction handles these differences, allowing the same
version-bump command to work across all project types.
-->

1. **Read current version** from universal VERSION file
2. **Calculate new version** based on semantic versioning rules
3. **Update VERSION file** (language-agnostic source of truth)
4. **Update CHANGELOG.md** with new version entry
5. **Sync to language files**: `make version-sync` (language-specific implementation)
6. **Validate consistency**: `make version-check` (cross-file validation)
7. **Display results** and next steps

### **Makefile Integration:**
```bash
# The version management now delegates to Makefile targets:
make version-sync    # Updates language-specific files (pyproject.toml, CMakeLists.txt, etc.)
make version-check   # Validates version consistency across all project files
```

### **Language-Specific Behavior:**

#### **Python Projects:**
- Updates `pyproject.toml` version field
- Updates `src/*/__init__.py` `__version__` variables
- Follows PEP 440 pre-release format (`1.0.0a1`, `1.0.0b2`, `1.0.0rc1`)

#### **C++ Projects:**
- Updates `CMakeLists.txt` VERSION field
- Updates `include/version.hpp` with version macros
- Follows semantic versioning format (`1.0.0-alpha.1`, `1.0.0-beta.2`)

#### **Mixed Projects:**
- Updates files for all detected languages
- Maintains version consistency across different language conventions
- Handles format differences automatically

## Enhanced Actions Performed

### **Phase 1: Version Calculation**
1. **Read current version** from VERSION file
2. **Calculate new version** using semantic versioning rules
3. **Validate version increment** (logical progression check)

### **Phase 2: Universal Updates**
4. **Update VERSION file** (single source of truth)
5. **Update CHANGELOG.md** with version entry and placeholder for changes

### **Phase 3: Language-Specific Sync (via Makefile)**
6. **Execute `make version-sync`** - Updates language-specific files:
   - Python: pyproject.toml, __init__.py files
   - C++: CMakeLists.txt, version.hpp
   - Mixed: All applicable files

### **Phase 4: Validation & Confirmation**
7. **Execute `make version-check`** - Validates consistency across files
8. **Display results** - Shows updated version and affected files
9. **Show next steps** - Suggests commit message and next actions

## Integration with Git-Flow Commands

### **Used by Release Commands:**
- **`/release-start <version>`** - Calls `/version-bump` for release preparation
- **`/release-finish <version>`** - Validates version consistency via `make version-check`

### **Works with Health Check:**
- **`/health-check-git`** - Includes version consistency validation
- **Detects version mismatches** across branches and languages

### **Error Handling:**
```bash
# Version validation failures
❌ Invalid version format: "v1.0.0" (should be "1.0.0")
❌ Version regression: 1.2.0 → 1.1.0 (not allowed)
❌ Missing VERSION file (run in project root)

# Language sync failures
⚠️  pyproject.toml version mismatch after sync
⚠️  CMakeLists.txt not found (C++ project detection issue)

# Recovery procedures provided for each error type
```

## Implementation

**Language-Agnostic Core:** Uses `.claude/tools/version_bump.py` for version calculation and universal file updates

**Language-Specific Sync:** Delegates to Makefile targets for project-specific file updates:
```bash
# Core version management (language-agnostic)
python .claude/tools/version_bump.py --bump $1 --pre-release $2

# Language-specific file sync (via Makefile abstraction)
make version-sync

# Validation (via Makefile abstraction)
make version-check
```

This approach ensures the same `/version-bump` command works seamlessly across Python, C++, and mixed projects while maintaining the Makefile abstraction layer for language-specific operations.