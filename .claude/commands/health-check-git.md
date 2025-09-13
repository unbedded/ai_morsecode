Comprehensive git repository state validation and health check

**Usage:** `/health-check-git [--fix]`

**Options:**
- `--fix` - Automatically fix detected issues where safe to do so

## Health Check Categories

### 🌲 **Branch Status & Relationships**
<!--
EDUCATIONAL NOTE: Git branches are lightweight pointers to commits. In git-flow:
- 'main' branch contains production-ready code (stable releases)
- 'develop' branch contains latest development changes (integration branch)
- Feature branches branch FROM develop and merge BACK to develop
- Release branches branch FROM develop, merge to BOTH main AND develop
- Hotfix branches branch FROM main, merge to BOTH main AND develop

WHY THIS MATTERS: If branches get out of sync, you can lose work or deploy broken code.
The most common mistake is merging a feature branch to main instead of develop,
which bypasses integration testing and can break production.
-->
- Current branch and working tree status
- Local vs remote branch synchronization
- Main/develop branch relationship validation
- Orphaned or stale branch detection

### 📋 **Version Consistency**
<!--
EDUCATIONAL NOTE: Version consistency is critical for deployment tracking:
- VERSION file: Single source of truth for current version
- Git tags: Mark specific commits as releases (v1.0.0, v1.1.0, etc.)
- CHANGELOG.md: Human-readable record of changes per version

WHY THIS MATTERS: Inconsistent versions lead to:
- Deploying wrong code to production
- Unable to rollback properly
- Confusion about what features are in which release
- Breaking semantic versioning contracts with users

BEST PRACTICE: VERSION file should match latest git tag on main branch.
Develop branch can have higher version (next release) but must be >= main.
-->
- VERSION file consistency across branches
- Git tags vs VERSION file validation
- Version format and semver compliance
- CHANGELOG.md version entry verification

### 🏷️ **Tag Management**
<!--
EDUCATIONAL NOTE: Git tags are immutable markers pointing to specific commits:
- Annotated tags (git tag -a v1.0.0 -m "message") are recommended for releases
- Lightweight tags (git tag v1.0.0) are just pointers, less informative
- Tags should follow semantic versioning: MAJOR.MINOR.PATCH
- Tags must be pushed separately: git push origin --tags

WHY THIS MATTERS: Tags enable:
- Precise rollback to known good states
- Release automation and deployment
- Change tracking between versions
- Compliance and audit trails

COMMON MISTAKE: Creating tags locally but forgetting to push them.
This means your local repo thinks a release exists, but CI/CD systems don't see it.
-->
- Local vs remote tag synchronization
- Tag format and naming convention validation
- Orphaned or duplicate tag detection
- Tag commit hash verification

### 🔄 **Git-Flow State**
<!--
EDUCATIONAL NOTE: Git-flow is a branching model that provides structure:

FEATURE WORKFLOW:
1. git flow feature start my-feature (branches from develop)
2. Make commits to feature/my-feature
3. git flow feature finish my-feature (merges to develop, deletes branch)

RELEASE WORKFLOW:
1. git flow release start 1.2.0 (branches from develop)
2. Update VERSION, CHANGELOG, fix bugs only
3. git flow release finish 1.2.0 (merges to main AND develop, creates tag)

HOTFIX WORKFLOW:
1. git flow hotfix start 1.1.1 (branches from main - production code)
2. Fix critical bug
3. git flow hotfix finish 1.1.1 (merges to main AND develop, creates tag)

WHY THESE RULES MATTER:
- Features never touch main directly (prevents broken production code)
- Releases ensure main and develop stay synchronized
- Hotfixes fix production while keeping develop current
- Each workflow has specific merge targets for safety
-->
- Active git-flow branches (feature/release/hotfix)
- Incomplete git-flow operations detection
- Branch naming convention compliance
- Merge conflict detection

### 🔒 **Repository Integrity**
<!--
EDUCATIONAL NOTE: Working tree cleanliness is essential for safe operations:
- Uncommitted changes can interfere with merges and checkouts
- Untracked files might contain secrets or temporary data
- Remote connectivity ensures you can push/pull changes
- Git configuration affects commit authorship and behavior

WHY THIS MATTERS: Starting git-flow operations with a dirty working tree
can cause:
- Loss of uncommitted work during merges
- Merge conflicts that are hard to resolve
- Inability to switch branches cleanly
- Confusion about which changes belong to which branch

BEST PRACTICE: Always commit or stash changes before git-flow operations.
-->
- Uncommitted changes detection
- Untracked files assessment
- Remote connectivity validation
- Git configuration verification
- Code quality status: `make quality` (language-agnostic validation)
- Test suite status: `make test` (language-agnostic validation)

## Output Format

```
🔍 Git Repository Health Check

✅ **Working Tree**
   • Clean working directory
   • No uncommitted changes
   • No untracked files

⚠️  **Branch Synchronization**
   • main: 2 commits behind origin/main
   • develop: Up to date with origin/develop

❌ **Version Consistency**
   • VERSION file (1.2.0) != latest tag (v1.1.0)
   • CHANGELOG.md missing entry for v1.2.0

✅ **Git-Flow State**
   • No active feature/release/hotfix branches
   • All branches follow naming conventions

🔧 **Suggested Fixes:**
   1. git pull origin main
   2. Update CHANGELOG.md with v1.2.0 entry
   3. Consider creating release tag: git tag v1.2.0
```

## Automatic Fixes (with --fix flag)

**Safe automatic fixes:**
<!--
EDUCATIONAL NOTE: These fixes are "safe" because they don't lose data:
- Pulling updates only adds new commits (fast-forward)
- Pushing commits shares your work without changing it
- Cleaning merged branches removes only local references to deleted remote branches
- Standardizing format doesn't change version numbers, just formatting

UNSAFE fixes require human judgment:
- Resolving merge conflicts (could choose wrong resolution)
- Version number changes (could break semantic versioning)
- Force pushing (could overwrite other's work)
-->
- Pull remote updates for behind branches
- Push local commits for ahead branches
- Clean up merged branch references
- Standardize VERSION file format
- Remove stale remote tracking branches

**Manual fix guidance:**
- Merge conflict resolution procedures
- Version inconsistency correction steps
- Branch sync repair instructions
- Git-flow recovery procedures

## Use Cases

- **Before releases** - Validate repository state
- **After git-flow operations** - Verify successful completion
- **Regular maintenance** - Periodic repository health checks
- **Troubleshooting** - Diagnose git-flow issues
- **Team onboarding** - Verify local setup

## Integration Points

- Called automatically by enhanced `/gitflow-start` and `/gitflow-finish`
- Integrates with `/version-consistency-check` for comprehensive validation
- Used by `/release-doctor` for issue diagnosis
- Supports `/release-start` pre-release validation

## Error Detection & Reporting

**Critical Issues (❌):**
<!-- These can break deployments or cause data loss -->
- Version inconsistencies across branches
- Merge conflicts or incomplete operations
- Missing or corrupted tags
- Remote connectivity problems

**Warnings (⚠️):**
<!-- These should be fixed but won't break things immediately -->
- Branches behind/ahead of remote
- Uncommitted changes
- Non-standard branch names
- Missing CHANGELOG entries

**Success Indicators (✅):**
<!-- Repository is in ideal state for git-flow operations -->
- Clean working directory
- Synchronized branches
- Consistent versioning
- Proper git-flow state