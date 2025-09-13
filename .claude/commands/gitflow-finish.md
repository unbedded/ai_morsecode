Finish GitFlow branch workflow with comprehensive validation: $ARGUMENTS

**Required arguments:**
- `<branch_type>` - Branch type: `feature`, `hotfix`, `bugfix` (**NOT** `release` - use `/release-finish`)
- `<branch_name>` - Name of the branch to finish

**Options:**
- `--keep-branch` - Keep the branch after merging (don't delete)
- `--no-ff` - Force no fast-forward merge

**Examples:**
- `/gitflow-finish feature user-authentication` - Finish and delete feature branch
- `/gitflow-finish hotfix critical-fix` - Finish hotfix, merge to main and develop
- `/gitflow-finish bugfix login-error --keep-branch` - Finish bugfix but keep branch

**⚠️ For Release Branches:**
- **Use `/release-finish 1.2.0` instead** - Releases require specialized handling with version management and enhanced safety validation

## Safety Validation (Pre-finish Checks)

**Before merge execution:**
1. **Current branch verification** - Must be on the target branch to finish
2. **Working tree validation** - Ensure no uncommitted changes
3. **Branch existence check** - Verify branch exists locally and remotely
4. **Quality gates** (for releases/hotfixes):
   - Run `make quality` - Language-appropriate quality pipeline (format + lint + typecheck)
   - Run `make test-full` - Comprehensive test suite with coverage
   - Verify VERSION file matches branch name (for releases)
5. **Target branch validation** - Ensure target branches exist and are current

## Daily Git-Flow Merge Behavior (No Releases)

**Merge targets and validation:**
- `feature/*` → Merges to `develop`, deletes branch
  - ✓ Verify `develop` exists and is up-to-date
  - ✓ Run `make quality` for code quality validation
- `hotfix/*` → Merges to `main` AND `develop`, deletes branch
  - ✓ Verify both `main` and `develop` exist and are synchronized
  - ✓ Run `make quality` and `make test-full` for critical hotfix validation
  - ✓ **Note**: Hotfixes are urgent fixes, no version bumping in this command
- `bugfix/*` → Merges to `develop`, deletes branch
  - ✓ Verify `develop` exists and is up-to-date
  - ✓ Run `make quality` for code quality validation

**⚠️ Release branches (`release/*`) are NOT handled by this command:**
- **Releases require version management** - use `/release-finish` instead
- **Releases need comprehensive validation** - dual-merge + version tagging + extensive safety checks
- **Releases are high-stakes operations** - production deployment requires specialized handling

## Post-Merge Validation

**After successful completion:**
1. **Branch synchronization check** - Verify main and develop are in sync (for releases/hotfixes)
2. **Tag verification** - Confirm version tag was created and points to correct commit
3. **Remote sync** - Push all updated branches and tags to origin
4. **Final status report** - Display success summary with next steps

## Execution Flow

1. **Pre-finish validation** (branch, working tree, quality gates)
2. **Execute**: `git flow <branch_type> finish <branch_name>`
3. **Post-merge validation** (branch sync, tags, remote push)
4. **Success confirmation** and cleanup report

## Error Handling & Recovery

- **Quality gate failures** → Show specific failures, suggest fixes
- **Merge conflicts** → Display conflict files, provide resolution guidance
- **Branch sync issues** → Detect main/develop hash mismatches, suggest fix procedures
- **Remote push failures** → Show push errors, suggest authentication/connectivity checks
- **Incomplete merges** → Provide rollback procedures and manual recovery steps
- **Release branch attempted** → Clear error message directing to `/release-finish` command

## Release Branch Redirection

**If user attempts to finish a release branch with this command:**
```bash
❌ Error: Release branches require specialized handling

You attempted: /gitflow-finish release 1.2.0
✅ Use instead: /release-finish 1.2.0

Why releases are different:
• Version management and tagging required
• Enhanced safety validation for production deployment
• Comprehensive dual-merge verification
• Educational guidance for critical operations

For help: /release-finish --help
```

## Critical Safety Features

**For Daily Operations (Non-Release):**
- **Prevents accidental main merges**: Features/bugfixes only merge to develop
- **Quality gates**: All branches validated with `make quality`
- **Fast workflow**: Streamlined for daily development operations
- **Clear separation**: Release complexity handled by dedicated `/release-*` commands

**This addresses your original concern**: Features can never accidentally merge to main - they go through develop → release → main path only.