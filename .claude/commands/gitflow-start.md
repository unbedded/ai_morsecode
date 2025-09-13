Start GitFlow branch workflow with comprehensive safety checks: $ARGUMENTS

Required arguments:
- `<branch_type>` - Branch type: `feature`, `hotfix`, `bugfix` (**NOT** `release` - use `/release-start`)
- `<branch_name>` - Name for the new branch

Examples:
- `/gitflow-start feature user-authentication` → Creates `feature/user-authentication`
- `/gitflow-start hotfix critical-security-fix` → Creates `hotfix/critical-security-fix`
- `/gitflow-start bugfix login-error` → Creates `bugfix/login-error`

**⚠️ For Release Branches:**
- **Use `/release-start 1.2.0` instead** - Releases require AI planning, comprehensive validation, and specialized handling

## Safety Validation (Pre-flight Checks)

**Before branch creation:**
1. **Working tree validation** - Ensure no uncommitted changes
2. **Current branch verification** - Validate starting from correct branch:
   - `feature/*`, `bugfix/*` → Must be on `develop`
   - `hotfix/*` → Must be on `main`
3. **Branch synchronization** - Ensure current branch is up-to-date with origin
4. **Branch name validation** - Check for valid naming conventions
5. **Existing branch check** - Prevent duplicate branch creation

**Branch creation rules:**
- `feature/*` - Branches from `develop`, merges back to `develop`
- `hotfix/*` - Branches from `main`, merges to `main` and `develop`
- `bugfix/*` - Branches from `develop`, merges back to `develop`

**⚠️ Release branches (`release/*`) are handled by `/release-start` command for AI planning and specialized validation**

## Execution Flow

1. **Validate prerequisites** (working tree, current branch, sync status)
2. **Execute**: `git flow <branch_type> start <branch_name>`
3. **Verify success** and display next steps
4. **Show branch info** and merge targets

## Error Handling

- **Dirty working tree** → Display uncommitted changes, suggest stash/commit
- **Wrong starting branch** → Show current vs expected branch, suggest checkout
- **Out of sync** → Display behind/ahead status, suggest pull/push
- **Invalid branch name** → Show naming conventions and examples
- **Existing branch** → List existing branches, suggest different name