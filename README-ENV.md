# Python Claude Code Development Template (Streamlined)

This repository serves as a comprehensive template for **Python 3.13.5** and **C++ (CMake + GTest)** development projects using Claude Code, with enhanced GitFlow workflow safety and language-agnostic development tools.

## 🎯 **Key Features**

### **Enhanced Git-Flow Safety**
- **Prevents accidental main merges**: Features must go through proper develop → release → main flow
- **Comprehensive pre-flight validation**: Clean working tree, branch sync, version consistency
- **Educational guidance**: Learn git-flow concepts while working
- **Intelligent error recovery**: AI-powered diagnosis and fix procedures

### **Language-Agnostic Development**
- **Makefile abstraction layer**: `make quality`, `make test`, `make test-full` work for any language
- **Standardized toolchains**: Python (ruff + mypy + pytest) | C++ (CMake + GTest + clang-format)
- **Universal version management**: Same commands work across languages
- **Mixed project support**: Handle Python + C++ projects seamlessly

## 🏗️ **Template Structure**

```
├── .claude/                 # Streamlined Claude Code configuration
│   ├── commands/           # AI-enhanced git-flow + intelligent commands only
│   ├── templates/          # Language-specific CLAUDE.md templates
│   └── tools/              # Language detection & project setup utilities
├── .github/workflows/       # CI/CD pipelines
├── .vscode/                # VS Code settings
├── src/                    # Source code (language-agnostic structure)
├── tests/                  # Test suite (language-appropriate)
├── CLAUDE.md               # Language-specific coding standards (auto-copied from template)
├── CHANGELOG.md            # Release history
├── VERSION                 # Current version (language-agnostic)
├── Makefile               # Generated language-specific targets
├── pyproject.toml          # Python: Build and tool configuration
├── CMakeLists.txt          # C++: Build and test configuration
└── requirements.txt        # Python: Dependencies
```

## 📋 **Streamlined Command Structure**

**🎯 Major Simplification:**
- **Quality/Testing → Makefile** (`make quality`, `make test`, `make test-full`)
- **Claude Commands → AI Intelligence** (git-flow safety, smart commit, release planning)
- **Language Detection → Automatic** (Python, C++, mixed projects)

### **🛡️ Enhanced Git-Flow Commands (Safety + Education)**

#### **`/gitflow-start <type> <name>`** - Safe branch creation with validation
- **Pre-flight checks**: Clean working tree, correct base branch, sync status
- **Branch validation**: Naming conventions, duplicate prevention
- **Educational**: Explains git-flow concepts and best practices
- **Language-agnostic**: Works with Python, C++, mixed projects

#### **`/gitflow-finish <type> <name>`** - Daily git-flow operations (features, hotfixes, bugfixes)
- **Daily operations only**: Handles features, hotfixes, bugfixes (**NOT releases**)
- **Quality validation**: Runs `make quality` for all branch types
- **Fast workflow**: Streamlined for routine development work
- **Critical safety**: Features/bugfixes only merge to develop, hotfixes to main+develop
- **⚠️ Releases**: Use `/release-finish` instead for version management and enhanced safety

#### **`/health-check-git [--fix]`** - Comprehensive repository diagnostics
- **Branch synchronization**: Detects main/develop hash mismatches
- **Version consistency**: Validates VERSION file across branches
- **Quality status**: Checks `make quality` and `make test` status
- **Auto-repair**: `--fix` flag for safe automatic fixes

#### **`/release-start <version>`** - Enhanced release branch creation
- **Version validation**: Semantic versioning format and logical increment
- **Educational features**: Explains release branch purpose and workflow
- **Integration**: Auto-calls health check and release planning
- **Quality preparation**: Sets up for `make quality` validation

#### **`/release-finish <version>`** - Production release completion (releases only)
- **Release branches only**: Specialized handling for production deployments
- **Version management**: Automatic version tagging and cross-branch syncing
- **Dual-merge process**: Safe merge to both main and develop branches
- **Quality gates**: `make quality` + `make test-full` must pass (non-negotiable)
- **Production safety**: Comprehensive validation for high-stakes deployments

#### **`/release-doctor [--fix]`** - Intelligent git-flow problem recovery
- **AI diagnosis**: Analyzes repository state and identifies issues
- **Smart recovery**: Automatic fixes for common git-flow problems
- **Educational**: Explains why problems occurred and how to prevent them
- **Integration**: Called automatically by other commands when issues detected

### **🛠️ Project Setup & Management**

#### **`/makefile-generate [--language <lang>] [--force]`** - Language-appropriate Makefile generation
- **Auto-detection**: Analyzes project files to determine language
- **Standardized stacks**: Python (ruff + mypy + pytest) | C++ (CMake + GTest)
- **Universal interface**: Same targets (`quality`, `test`, `test-full`) for all languages
- **Mixed project support**: Handles polyglot codebases

#### **`/new-module <name> [--with-tests]`** - Language-aware module scaffolding
- **Python**: Creates `.py` + test files with CLAUDE.md patterns
- **C++**: Creates `.cpp/.hpp` + test files with standard patterns
- **Consistent patterns**: Follows project coding standards automatically

### **🤖 AI Intelligence Commands**

#### **`/commit-smart [--stage-all]`** - AI-generated commit messages
- **Analyzes staged changes**: Understands code modifications and intent
- **Conventional commits**: Follows semantic commit message standards
- **Project awareness**: Adapts to project-specific patterns

#### **`/release-start <version>`** - AI-powered release planning + branch creation
- **Integrated AI planning**: Analyzes changes, assesses impact, recommends strategy
- **Safe branch creation**: Creates git-flow release branch with comprehensive validation
- **Generated checklist**: Provides detailed release checklist based on analysis
- **Integration**: Combines planning with git-flow branch creation in one command

#### **`/version-bump <level> [--pre-release <type>]`** - Universal version management
- **Semantic versioning**: patch, minor, major with pre-release support
- **Language-agnostic**: Works with Python, C++, mixed projects via `make version-sync`
- **Consistent updates**: VERSION file, CHANGELOG.md, language-specific files
- **Integration**: Used by release commands for version coordination

## 🔧 **Makefile Abstraction (Language-Agnostic Interface)**

### **Universal Targets (Same for All Languages):**
```makefile
make quality      # Language-appropriate quality pipeline
make test         # Quick test execution
make test-full    # Comprehensive testing with coverage
make clean        # Clean build artifacts
make install      # Install dependencies
make version-sync # Sync VERSION file to language-specific files
```

### **Python Implementation:**
```makefile
quality: ruff format . && ruff check . && mypy .
test: pytest -q
test-full: pytest --cov=src --cov-report=html
version-sync: # Updates pyproject.toml, __init__.py files
```

### **C++ Implementation:**
```makefile
quality: clang-format -i src/**/*.cpp && clang-tidy src/ && cmake --build build/
test: cd build && ctest --output-on-failure
test-full: cd build && ctest --verbose
version-sync: # Updates CMakeLists.txt, version.hpp
```

## 🚀 **Quick Start Guide**

### **1. Setup from GitHub Template (Recommended)**
```bash
# On GitHub: Use this template → Create repository
git clone https://github.com/yourusername/your_new_project.git
cd your_new_project

# Bootstrap for your language (automatically copies language-specific CLAUDE.md)
python .claude/tools/bootstrap_python.py --package your_project --python 3.13 --author "Your Name"
# OR for C++: python .claude/tools/bootstrap_cpp.py --package your_project

# Generate appropriate Makefile
/makefile-generate --language auto

# Initialize git-flow
git flow init  # Uses .gitflow configuration
```

### **2. Daily Development Workflow (Language-Agnostic)**
```bash
# Start new feature (enhanced safety)
/health-check-git                        # Verify repository health
/gitflow-start feature user-auth         # Safe branch creation with validation

# Development cycle
/new-module user_service --with-tests    # Language-aware scaffolding
# ... coding ...
make quality                             # Language-appropriate quality pipeline
make test-full                           # Comprehensive testing

# Commit with AI assistance
/commit-smart --stage-all                # AI-generated conventional commit

# Finish feature (daily git-flow - NO releases)
/gitflow-finish feature user-auth        # Safe completion for daily operations
```

### **3. Streamlined Release Workflow (3 Steps)**
```bash
# Step 1: AI-Powered Release Start
/release-start 1.2.0                    # AI analysis + planning + branch creation + checklist

# Step 2: Quality Assurance (follow generated checklist)
make quality && make test-full           # Language-agnostic quality pipeline
# Update CHANGELOG.md, test in staging, etc.

# Step 3: Safe Release Completion
/release-finish 1.2.0                   # Bulletproof dual-merge + verification

# If problems occur:
/release-doctor --fix                    # Intelligent problem recovery
```

## 🛡️ **Safety Features**

### **Prevents Common Git-Flow Mistakes:**
- **Accidental main merges**: Enhanced commands enforce proper flow
- **Dirty working tree issues**: Pre-flight validation ensures clean state
- **Branch sync problems**: Automatic detection and repair
- **Version inconsistencies**: Cross-branch validation and correction
- **Incomplete releases**: Post-merge verification ensures completion

### **Educational While You Work:**
- **Learn git concepts**: Commands explain WHY each step matters
- **Error recovery**: Step-by-step guidance for fixing problems
- **Best practices**: Commands teach proper workflows while preventing mistakes

### **Language-Agnostic Benefits:**
- **Same interface everywhere**: `make quality` works for Python, C++, mixed
- **Easy language switching**: Commands adapt automatically
- **Consistent workflows**: Learn once, use everywhere
- **Mixed project support**: Handle polyglot codebases seamlessly

## 🔄 **Migration from Previous Version**

### **What Changed:**
- **Removed commands**: `check-code`, `run-tests`, `analyze-changes`, `suggest-version`, `review-commits`, `review-code`
- **Added commands**: `makefile-generate`, enhanced git-flow commands
- **New abstraction**: Makefile handles language-specific operations
- **Streamlined workflow**: Focus on AI intelligence and git-flow safety

### **Migration Steps:**
```bash
# 1. Generate appropriate Makefile
/makefile-generate --language auto

# 2. Update existing commands (automatic - already done)
# 3. New workflows use make targets:
make quality     # Instead of /check-code
make test-full   # Instead of /run-tests

# 4. Enhanced git-flow commands (same names, more safety)
/gitflow-start   # Enhanced with validation
/gitflow-finish  # Enhanced with quality gates
```

## 📊 **Workflow Comparison**

| Task | Old Commands | New Streamlined Approach |
|------|-------------|-------------------------|
| **Code Quality** | `/check-code --fix` | `make quality` (language-agnostic) |
| **Run Tests** | `/run-tests --coverage` | `make test-full` (language-agnostic) |
| **Start Feature** | `/gitflow-start feature name` | `/gitflow-start feature name` (enhanced safety) |
| **Finish Feature** | `/gitflow-finish feature name` | `/gitflow-finish feature name` (quality gates) |
| **Start Release** | `/gitflow-start release 1.0.0` | `/release-start 1.0.0` (AI planning + validation) |
| **Finish Release** | `/gitflow-finish release 1.0.0` | `/release-finish 1.0.0` (bulletproof process) |
| **Repository Health** | Manual git commands | `/health-check-git --fix` (AI diagnosis) |
| **Problem Recovery** | Manual troubleshooting | `/release-doctor --fix` (intelligent recovery) |

## 🎯 **Best Practices**

### **Git-Flow Safety:**
- **Start with health**: Run `/health-check-git` before major operations
- **Use enhanced commands**: Prefer safety-enhanced versions over raw git-flow
- **Quality first**: Always run `make quality` before commits
- **Bulletproof releases**: Use `/release-start` and `/release-finish` for safe releases

### **Language-Agnostic Development:**
- **Generate Makefile first**: Run `/makefile-generate` in new projects
- **Use universal targets**: `make quality`, `make test`, `make test-full` work everywhere
- **Version management**: Let `/version-bump` handle language-specific file updates
- **Mixed projects**: Commands automatically detect and handle multiple languages

### **AI-Enhanced Workflow:**
- **Smart commits**: Use `/commit-smart` for conventional commit messages
- **Streamlined releases**: Use `/release-start` for AI-powered planning + branch creation
- **Problem solving**: Use `/release-doctor` when git-flow issues arise
- **Learn while working**: Read command output for educational insights

## 📖 **Complete Claude Commands Reference**

### 🌿 **Git-Flow & Release Management**
```
/gitflow-start <type> <name>
├── <type>: feature | hotfix | bugfix  (NOT release - use /release-start)
├── <name>: Branch name (e.g., user-auth, critical-fix)
└── → Creates branch with safety validation

/gitflow-finish <type> <name> [--keep-branch] [--no-ff]
├── <type>: feature | hotfix | bugfix  (NOT release - use /release-finish)
├── <name>: Branch name to finish
├── --keep-branch: Keep branch after merging
├── --no-ff: Force no fast-forward merge
└── → Daily operations only (quality gates + merge)

/release-start <version> [--target <version>]
├── <version>: Semantic version (e.g., 1.2.0, 2.0.0)
├── --target: Alternative version specification
└── → AI analysis + planning + branch creation + checklist

/release-finish <version>
├── <version>: Version being released (must match branch name)
└── → Production deployment with dual-merge + comprehensive validation

/release-doctor [--fix]
├── --fix: Automatically fix detected issues where safe
└── → Intelligent git-flow problem diagnosis and recovery
```

### 🔧 **Development Tools**
```
/health-check-git [--fix]
├── --fix: Auto-repair safe issues (branch sync, version consistency)
└── → Comprehensive repository diagnostics

/makefile-generate [--language <lang>] [--force]
├── --language: python | cpp | mixed | auto  (default: auto-detect)
├── --force: Overwrite existing Makefile without confirmation
└── → Language-appropriate build system generation

/version-bump <level> [--pre-release <type>]
├── <level>: patch | minor | major
├── --pre-release: alpha | beta | rc
└── → Universal version management with make version-sync

/commit-smart [--stage-all]
├── --stage-all: Stage all changes before generating commit message
└── → AI-generated conventional commit messages

/new-module <name> [--with-tests]
├── <name>: Module name (e.g., user_service, data_processor)
├── --with-tests: Generate comprehensive test files
└── → Language-aware module scaffolding with CLAUDE.md patterns
```

### 🎯 **Key Features**
- **Educational**: Each command includes detailed documentation explaining git-flow concepts
- **Safe**: Pre-flight validation prevents common mistakes (dirty tree, wrong branch, etc.)
- **Language-Agnostic**: Universal interface with language-specific implementation
- **AI-Enhanced**: Smart commit messages, release planning, problem diagnosis

**📚 For detailed usage, examples, and educational content, see individual `.claude/commands/*.md` files**

---

This streamlined template provides a powerful, educational, and safe development environment that scales from simple Python scripts to complex polyglot projects, all while teaching best practices and preventing common git-flow mistakes.