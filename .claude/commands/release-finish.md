Complete git-flow release with comprehensive validation and branch synchronization: $ARGUMENTS

**Usage:** `/release-finish <version>`

**Required:**
- `<version>` - Version being released (must match release branch name)

**Examples:**
- `/release-finish 1.2.0` → Merges release/1.2.0 to main and develop
- `/release-finish 2.0.0` → Completes major release with full validation

## Educational Overview: Git-Flow Release Completion

<!--
WHAT HAPPENS DURING RELEASE FINISH?
This is the most critical operation in git-flow because it affects BOTH branches
that matter most: main (production) and develop (ongoing work).

THE DUAL-MERGE PROCESS:
1. Merge release branch → main (deploys to production)
2. Merge release branch → develop (keeps develop current)
3. Create git tag on main (marks the release)
4. Delete release branch (cleanup)

WHY BOTH MERGES ARE CRITICAL:
- main gets the release (production deployment)
- develop gets any bug fixes made during release preparation
- If develop doesn't get the bug fixes, they'll be lost in next release!

THIS IS WHERE THE "ACCIDENTAL MAIN MERGE" PROBLEM GETS SOLVED:
- Features go: develop → release → main (never feature → main directly)
- Releases ensure both main and develop stay synchronized
- Validates that the right code goes to the right places
-->

## Critical Safety Validation (Pre-Finish Checks)

### 1. **Current Branch Verification**
<!--
WHY: You must be ON the release branch to finish it because:
- Git-flow needs to merge FROM the release branch
- Ensures you're completing the right release
- Prevents accidental merge from wrong branch

WHAT WE CHECK: git branch --show-current == "release/<version>"
-->
- Must be on `release/<version>` branch
- Version in command must match current branch name
- Prevents finishing wrong release or from wrong branch

### 2. **Working Tree Validation**
<!--
WHY: Clean working tree is CRITICAL for releases because:
- Uncommitted changes could accidentally be included in production
- Dirty tree can cause merge conflicts during dual-merge process
- Release should contain only intentional, committed changes

WHAT WE CHECK: git status --porcelain (must be empty)
-->
- Absolutely no uncommitted changes allowed
- No untracked files that might be important
- Release must contain only committed, reviewed changes

### 3. **Quality Gate Enforcement**
<!--
WHY THESE QUALITY CHECKS MATTER:
- Broken code should never reach main (production)
- Tests ensure functionality works as expected
- Linting catches style issues and potential bugs
- Type checking prevents runtime type errors

FOR RELEASES, WE'RE EXTRA STRICT:
- ALL tests must pass (no exceptions)
- ALL linting issues must be resolved
- ALL type checking must be clean
- This is the last checkpoint before production
-->
- **Code Quality**: Run `/check-code` - all linting and type checking must pass
- **Test Suite**: Run `/run-tests` - 100% test success required
- **Version Consistency**: VERSION file must match release branch name
- **CHANGELOG Validation**: Must have entry for this version

### 4. **Target Branch Readiness**
<!--
WHY TARGET BRANCHES MUST BE READY:
- main: Must exist and be the production branch
- develop: Must exist and be current (for receiving bug fixes)
- Both must be synchronized with remote (team collaboration)

SYNCHRONIZATION PREVENTS:
- Losing other people's work during merge
- Merge conflicts from outdated branches
- Deployment of incomplete code
-->
- `main` branch exists and is up-to-date with remote
- `develop` branch exists and is up-to-date with remote
- No merge conflicts detected between release and target branches

## Enhanced Merge Process with Validation

### Phase 1: Pre-Merge Validation
```bash
# Critical safety checks before any merges happen
git status --porcelain                           # Working tree clean
git fetch origin                                 # Update remote refs
git show-branch main develop release/<version>   # Verify branches exist
git merge-tree main release/<version>            # Check for conflicts with main
git merge-tree develop release/<version>         # Check for conflicts with develop
```

### Phase 2: Quality Gate Execution
<!--
QUALITY GATES ARE NON-NEGOTIABLE FOR RELEASES:
These commands must succeed before any merge happens.
If any fail, the release process stops and shows specific errors to fix.
-->
- Execute `make quality` (language-appropriate linting, formatting, type checking)
- Execute `make test-full` (comprehensive test suite with coverage)
- Validate VERSION file content matches `<version>` argument
- Confirm CHANGELOG.md has entry for this version

### Phase 3: Git-Flow Release Finish
<!--
WHAT git flow release finish DOES:
1. Switches to main branch
2. Merges release/<version> into main
3. Creates annotated git tag (v<version>) on main
4. Switches to develop branch
5. Merges release/<version> into develop
6. Deletes local release/<version> branch

WHY THIS ORDER MATTERS:
- main gets the release first (production deployment)
- Tag is created on main (proper release marking)
- develop gets the same changes (synchronization)
- Release branch cleanup (prevents confusion)
-->
```bash
git flow release finish <version>
```

### Phase 4: Post-Merge Validation & Synchronization
<!--
CRITICAL POST-MERGE CHECKS:
Even after git-flow finishes, we must verify everything worked correctly:
-->

#### **Branch Hash Synchronization Verification**
<!--
WHY CHECK BRANCH HASHES:
After a release, main and develop should point to the same commit
(or develop should be ahead by merge commit only).

WHAT WE'RE DETECTING:
- Failed merge-back to develop (develop missing release changes)
- Merge conflicts that weren't properly resolved
- Git-flow command that didn't complete fully

HOW WE CHECK:
- git rev-parse main (get main commit hash)
- git rev-parse develop (get develop commit hash)
- git merge-base main develop (should be main's hash for clean release)
-->
```bash
# Verify branches are properly synchronized
main_hash=$(git rev-parse main)
develop_hash=$(git rev-parse develop)
merge_base=$(git merge-base main develop)

# For clean release: merge_base should equal main_hash
# develop_hash should equal main_hash OR be one commit ahead (merge commit)
```

#### **Tag Verification**
<!--
WHY TAG VALIDATION MATTERS:
- Tags are used by deployment systems to identify releases
- Wrong tag could deploy wrong code version
- Missing tag means deployment automation fails

WHAT WE CHECK:
- Tag exists locally: git tag -l "v<version>"
- Tag points to correct commit: git rev-parse "v<version>" == main_hash
- Tag is annotated (not lightweight): git cat-file -t "v<version>" == "tag"
-->
```bash
# Verify release tag was created correctly
git tag -l "v<version>"                    # Tag exists
tag_hash=$(git rev-parse "v<version>")     # Tag commit hash
main_hash=$(git rev-parse main)            # Main commit hash
# tag_hash should equal main_hash
```

#### **Remote Synchronization**
<!--
WHY PUSH TO REMOTE:
- Team needs to see the release branches and tags
- CI/CD systems deploy from remote repositories
- Backup of release work

WHAT WE PUSH:
- main branch (production code)
- develop branch (synchronized development)
- Tags (release markers)

PUSH ORDER MATTERS:
- Push main first (production deployment trigger)
- Then develop (team synchronization)
- Finally tags (release automation trigger)
-->
```bash
git push origin main         # Production deployment
git push origin develop      # Development synchronization
git push origin --tags       # Release tags for automation
```

## Advanced Error Detection & Recovery

### **Quality Gate Failures**
```
❌ Quality gates failed - Release blocked

🧪 Test Failures (3):
   • test_authentication.py::test_login_flow
   • test_api.py::test_user_creation
   • test_integration.py::test_checkout_process

🔧 Required fixes:
   1. Fix failing tests on release branch
   2. Commit fixes: git add . && git commit -m "Fix release tests"
   3. Re-run: /release-finish 1.2.0

⚠️  DO NOT proceed without fixing tests - production deployment will fail!
```

### **Branch Synchronization Issues**
```
❌ Branch synchronization problem detected

📊 Branch State Analysis:
   • main:    commit abc123f "Previous release v1.1.0"
   • develop: commit def456g "Feature XYZ merged"
   • release: commit 789hijf "Release v1.2.0 ready"

⚠️  Problem: develop is ahead of main, but should be synchronized after release

🔧 Recovery procedure:
   1. This suggests an incomplete previous release
   2. Run /release-doctor for detailed diagnosis
   3. May need manual branch synchronization
```

### **Tag Creation Failures**
```
❌ Git tag creation failed

🏷️  Tag Issues:
   • Tag v1.2.0 already exists locally
   • Tag points to different commit: commit abc123f
   • Expected commit: def456g

🔧 Recovery options:
   1. Delete existing tag: git tag -d v1.2.0
   2. Re-run release finish: /release-finish 1.2.0
   3. Or fix tag manually: git tag -f -a v1.2.0 -m "Release v1.2.0"
```

### **Remote Push Failures**
```
❌ Failed to push to remote

🌐 Push Status:
   ✅ main → origin/main (success)
   ❌ develop → origin/develop (rejected)
   ⏸️  tags (skipped due to develop failure)

🔧 Common causes:
   • develop is behind remote (need git pull origin develop first)
   • Network connectivity issues
   • Authentication problems
   • Remote repository permissions

Fix: git pull origin develop && git push origin develop && git push origin --tags
```

## Success Confirmation & Next Steps

### **Successful Release Output**
```
✅ Release v1.2.0 completed successfully!

📊 Release Summary:
   • Source: release/1.2.0 → ✅ deleted
   • Target: main (commit def456g) → ✅ updated
   • Merge-back: develop (commit def456g) → ✅ synchronized
   • Tag: v1.2.0 → ✅ created and pushed
   • Remote sync: ✅ all branches and tags pushed

🚀 Production Deployment:
   • Code is ready for production deployment
   • Version tag v1.2.0 available for CI/CD systems
   • All branches synchronized with remote

🔄 Next Development Cycle:
   • New features can be started from develop
   • develop branch contains v1.2.0 + any ongoing work
   • Ready for next release cycle
```

## Git-Flow Best Practices Reinforcement

<!--
EDUCATIONAL SUMMARY: What this release process achieves

1. PRODUCTION SAFETY:
   - Only tested, quality-checked code reaches main
   - Clear version marking with git tags
   - Rollback capability to any previous release

2. DEVELOPMENT CONTINUITY:
   - develop stays current with all changes
   - Bug fixes from release are not lost
   - Team can continue new features immediately

3. TEAM COLLABORATION:
   - All changes pushed to remote for team access
   - Clear release markers for deployment automation
   - Consistent process that everyone can follow

4. MISTAKE PREVENTION:
   - Multiple validation checkpoints prevent errors
   - Automatic verification of critical operations
   - Clear error messages with specific fix procedures

This addresses your original problem: "trouble merging from feature branch to develop -
by accident it went onto main." The release process ensures:
- Features NEVER go directly to main
- Only release branches (tested, validated) merge to main
- develop and main stay synchronized through the release process
-->

### **The Release Safety Model:**
1. **Features** → `develop` (integration testing)
2. **Releases** → `main` + `develop` (production + synchronization)
3. **Hotfixes** → `main` + `develop` (emergency fixes + synchronization)

### **Why This Prevents Accidental Main Merges:**
- Features can only merge to develop (enforced by git-flow)
- Main only receives code through release/hotfix process
- Every main update is validated, tested, and tagged
- develop and main synchronization is automatic and verified

## Integration Points

- Called after `/release-start` completion and release preparation
- Uses `/health-check-git` for comprehensive validation
- Integrates with `make quality` and `make test-full` for language-agnostic quality gates
- Connects to upcoming `/release-doctor` for error recovery