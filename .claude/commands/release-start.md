Start a git-flow release with AI planning, comprehensive validation and safety checks: $ARGUMENTS

**Usage:** `/release-start <version> [--target <version>]`

**Required:**
- `<version>` - Target version (e.g., "1.2.0", "2.0.0")

**Options:**
- `--target <version>` - Alternative way to specify version (for compatibility)

**Examples:**
- `/release-start 1.2.0` → AI analysis + creates `release/1.2.0` branch
- `/release-start 2.0.0` → Comprehensive planning + major release branch creation

## 🤖 **AI-Powered Release Planning (Integrated)**

This command now combines intelligent release planning with safe branch creation:

### **Phase 1: AI Release Analysis**
1. **Change Analysis**: Reviews unreleased commits and modifications since last tag
2. **Impact Assessment**: Evaluates breaking changes, new features, bug fixes
3. **Version Validation**: Confirms version increment is logical and follows semver
4. **Risk Assessment**: Analyzes complexity and potential deployment risks
5. **Release Strategy**: Recommends deployment approach and timeline

### **Phase 2: Comprehensive Release Planning**
**Generates Release Checklist:**
```markdown
📋 Release Plan for v1.3.0

## 📊 Release Summary
**Target Version:** 1.3.0 (Minor Release)
**Changes Since:** v1.2.5 (2 weeks ago)
**Commits:** 23 commits across 8 files
**Risk Level:** LOW - No breaking changes identified

## 🔄 Change Impact
### 🚀 New Features (3)
- User authentication system with JWT tokens
- Profile management with avatar uploads
- Email notification system

### 🐛 Bug Fixes (5)
- Fixed memory leak in data processing
- Resolved race condition in async handlers
- Corrected validation logic for user input

## ✅ Pre-Release Checklist
### Code Quality
- [ ] Run full test suite (`make test-full`)
- [ ] Execute code quality pipeline (`make quality`)
- [ ] Review security scan results

### Release Preparation
- [ ] Update CHANGELOG.md with release notes
- [ ] Build and test deployment package
- [ ] Prepare rollback procedures

### Deployment Validation
- [ ] Deploy to staging environment
- [ ] Execute smoke tests and integration tests
- [ ] Monitor performance metrics

**Estimated Timeline:** 2-3 days
**Recommended Window:** Tuesday-Thursday
```

## Educational Overview: Git-Flow Release Process

<!--
WHAT IS A RELEASE BRANCH?
A release branch is where you prepare code for production deployment. It's like a "staging area"
between development (develop branch) and production (main branch).

WHY USE RELEASE BRANCHES?
1. Allows continued development on develop while preparing release
2. Provides place to fix bugs found during release testing
3. Ensures main branch only gets stable, tested code
4. Creates clear point for version bumping and changelog updates

RELEASE BRANCH LIFECYCLE:
1. Branch FROM: develop (contains all features for this release)
2. Work ON: Bug fixes, version updates, documentation only (NO new features)
3. Merge TO: main (production) AND develop (to keep them synchronized)
4. Creates: Git tag marking the release version

CRITICAL RULE: Only bug fixes allowed on release branches!
New features must wait for next release cycle.
-->

## Pre-Flight Safety Validation

### 1. **Current Branch Verification**
<!--
WHY: You must start releases from develop branch because:
- develop contains the latest integrated features
- main should only receive tested, release-ready code
- Starting from wrong branch could miss features or include untested code

WHAT WE CHECK: git branch --show-current == "develop"
-->
- Must be on `develop` branch to start release
- Prevents starting release from feature branches or main

### 2. **Working Tree Cleanliness**
<!--
WHY: Clean working tree prevents:
- Accidentally including uncommitted changes in release
- Merge conflicts when switching branches
- Confusion about which changes belong where

WHAT WE CHECK: git status --porcelain (should be empty)
IF DIRTY: Show files and suggest: git add . && git commit OR git stash
-->
- No uncommitted changes allowed
- No untracked files that might contain important work
- Ensures clean branch creation

### 3. **Branch Synchronization**
<!--
WHY: Being behind origin means:
- You're missing teammates' recent work
- Release might not include all intended features
- Could create merge conflicts later

WHY: Being ahead means:
- You have local commits not yet shared
- Team can't see your work for review
- Could lose work if not pushed

WHAT WE CHECK:
- git rev-list HEAD..origin/develop (behind count)
- git rev-list origin/develop..HEAD (ahead count)
-->
- `develop` must be up-to-date with `origin/develop`
- Prevents missing recent changes or unpushed work
- Suggests: `git pull` if behind, `git push` if ahead

### 4. **Version Validation**
<!--
WHY SEMANTIC VERSIONING MATTERS:
- MAJOR (2.0.0): Breaking changes, incompatible API changes
- MINOR (1.2.0): New features, backward compatible
- PATCH (1.1.1): Bug fixes, backward compatible

VALIDATION RULES:
- Must follow semver format: MAJOR.MINOR.PATCH
- Must be greater than current VERSION file
- Should be logical increment (1.0.0 → 1.1.0, not 1.0.0 → 3.0.0)

WHY: Version chaos leads to deployment confusion and user frustration
-->
- Version format must follow semantic versioning (semver)
- Version must be greater than current VERSION file content
- Logical version increment validation

### 5. **Existing Branch Prevention**
<!--
WHY: Duplicate release branches cause:
- Confusion about which branch is "real"
- Potential work duplication
- Git-flow command failures

WHAT WE CHECK:
- git branch --list "release/*" (local branches)
- git branch -r --list "*/release/*" (remote branches)
-->
- No existing `release/*` branches allowed
- Prevents duplicate or conflicting release preparation
- Suggests completing existing release first

## Execution Flow

### Phase 1: Validation
```bash
# These are the actual git commands that would be executed:
git status --porcelain                    # Check working tree
git branch --show-current                 # Verify current branch
git fetch origin                          # Update remote refs
git rev-list HEAD..origin/develop         # Check if behind
git rev-list origin/develop..HEAD         # Check if ahead
git branch --list "release/*"             # Check existing releases
```

### Phase 2: Release Creation
<!--
WHAT HAPPENS DURING git flow release start:
1. Creates new branch: release/X.Y.Z from current develop
2. Switches to the new release branch
3. Sets up git-flow tracking for this release

THE BRANCH NAME MATTERS:
- Must match version exactly: release/1.2.0 (not release/v1.2.0)
- Enables automatic version validation later
- Follows git-flow naming conventions
-->
```bash
git flow release start <version>          # Create and switch to release branch
```

### Phase 3: Post-Creation Setup
- Update VERSION file to match release version
- Display integrated AI-generated release checklist
- Show next steps and important warnings

## Error Handling & Recovery

### **Dirty Working Tree**
```
❌ Working tree is not clean
📁 Uncommitted changes:
   M  src/module.py
   ?? temp_file.txt

🔧 Fix options:
   1. Commit changes: git add . && git commit -m "Pre-release cleanup"
   2. Stash changes: git stash push -m "Work in progress"
   3. Remove untracked: git clean -fd (⚠️  DESTRUCTIVE)
```

### **Wrong Starting Branch**
```
❌ Must start release from develop branch
📍 Current branch: feature/user-auth
🎯 Expected branch: develop

🔧 Fix: git checkout develop
```

### **Out of Sync Branch**
```
⚠️  develop is 3 commits behind origin/develop
📥 Missing commits:
   abc123f Fix authentication bug
   def456g Update dependencies
   789hij Add user preferences

🔧 Fix: git pull origin develop
```

### **Invalid Version Format**
```
❌ Invalid version: "v1.2.0"
✅ Required format: "1.2.0" (no 'v' prefix)
📚 Semantic versioning: MAJOR.MINOR.PATCH

Examples:
   • Bug fixes: 1.1.0 → 1.1.1
   • New features: 1.1.0 → 1.2.0
   • Breaking changes: 1.1.0 → 2.0.0
```

## Release Branch Best Practices

<!--
EDUCATIONAL GUIDELINES for working on release branches:

DO:
✅ Fix bugs discovered during testing
✅ Update documentation and changelogs
✅ Bump version numbers
✅ Make small, safe improvements to existing features
✅ Add or improve tests for existing functionality

DON'T:
❌ Add new features (wait for next release)
❌ Make large refactoring changes
❌ Change APIs or breaking existing functionality
❌ Add dependencies or major configuration changes

WHY THESE RULES:
- Release branches should be stabilization period
- New features increase risk of bugs
- Goal is to make develop→main transition as safe as possible
- Features can continue development on new feature branches from develop
-->

### ✅ **Allowed on Release Branches:**
- Bug fixes discovered during release testing
- Documentation updates and changelog entries
- Version file updates and release preparation
- Small improvements to error messages or user experience
- Test additions or improvements for existing functionality

### ❌ **NOT Allowed on Release Branches:**
- New features or functionality (wait for next cycle)
- Large refactoring or architectural changes
- Breaking API changes
- New dependencies or major configuration changes
- Experimental or risky modifications

### **Phase 3: Git-Flow Branch Creation**
After AI planning and validation:
1. **Execute git-flow**: `git flow release start <version>`
2. **Post-creation setup**: Update VERSION file and sync with `make version-sync`
3. **Display checklist**: Show generated release checklist for reference

### 🔄 **After Release Branch Creation:**
1. **Follow the generated checklist** from AI analysis
2. Run `make quality` to ensure code quality (language-appropriate pipeline)
3. Run `make test-full` to verify all tests pass with coverage
4. Update CHANGELOG.md with release notes from AI analysis
5. Perform thorough testing in staging environment
6. When ready: `/release-finish <version>`

## 🎯 **Complete Release Workflow (3 Steps)**

### **Step 1: Smart Release Start (This Command)**
```bash
/release-start 1.2.0
# → AI analysis + planning + branch creation + checklist generation
```

### **Step 2: Development & Quality Assurance**
```bash
# Follow generated checklist:
make quality           # Language-appropriate quality pipeline
make test-full         # Comprehensive testing with coverage
# Update docs, test in staging, etc.
```

### **Step 3: Safe Release Completion**
```bash
/release-finish 1.2.0  # Bulletproof dual-merge + verification
```

### **Step 4: Problem Recovery (If Needed)**
```bash
/release-doctor --fix  # Intelligent problem diagnosis and recovery
```

## Integration with Other Commands

- **Replaces**: `/release-plan` (functionality now integrated)
- **Calls**: `/health-check-git` for repository validation
- **Connects to**: `/version-bump` for version management
- **Uses**: `make quality` and `make test-full` for language-agnostic quality gates
- **Leads to**: `/release-finish` for safe completion