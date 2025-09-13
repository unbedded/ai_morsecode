Diagnose and fix git-flow release problems with intelligent recovery procedures

**Usage:** `/release-doctor [--fix]`

**Options:**
- `--fix` - Automatically fix detected issues where safe to do so

## Educational Overview: Git-Flow Problem Diagnosis

<!--
WHY DO GIT-FLOW PROBLEMS HAPPEN?
Git-flow is powerful but complex. Common issues include:

1. INTERRUPTED OPERATIONS:
   - Network failures during push/pull
   - Merge conflicts that weren't properly resolved
   - Accidentally canceled git-flow commands mid-process

2. BRANCH SYNCHRONIZATION ISSUES:
   - main and develop get out of sync (the problem you experienced)
   - Release merges that partially failed
   - Manual git operations that bypassed git-flow

3. TAG AND VERSION PROBLEMS:
   - Version inconsistencies across branches
   - Missing or incorrect git tags
   - VERSION file doesn't match git state

4. WORKING TREE ISSUES:
   - Incomplete merges leaving conflict markers
   - Stale branches that should have been deleted
   - Uncommitted changes blocking operations

THE DOCTOR'S APPROACH:
Like a medical diagnosis, we:
1. Gather symptoms (git state analysis)
2. Identify root causes (branch relationships, version consistency)
3. Prescribe treatment (specific fix procedures)
4. Verify cure (post-fix validation)
-->

## Diagnostic Categories

### 🌿 **Branch Synchronization Diagnosis**

#### **Main/Develop Hash Mismatch Detection**
<!--
WHAT THIS MEANS:
After a release, main and develop should be synchronized. If they're not:
- develop might be missing bug fixes from the release
- main might have changes that develop doesn't know about
- Next release could lose or duplicate changes

HOW WE DETECT:
- git merge-base main develop (should be main's commit for clean state)
- git rev-list main..develop (commits in develop not in main)
- git rev-list develop..main (commits in main not in develop)

COMMON CAUSES:
- Release finish didn't complete the develop merge-back
- Manual merges that bypassed git-flow
- Hotfixes that didn't properly merge to both branches
-->
```bash
# Branch relationship analysis
main_hash=$(git rev-parse main)
develop_hash=$(git rev-parse develop)
merge_base=$(git merge-base main develop)

# Ideal state: merge_base == main_hash (develop is ahead of or equal to main)
# Problem state: main has commits that develop doesn't have
```

#### **Behind/Ahead Analysis**
<!--
BRANCH SYNC SCENARIOS:

✅ HEALTHY:
- develop is 0-N commits ahead of main (normal development)
- main and develop share common history
- No commits in main that aren't in develop

⚠️  WARNING:
- develop is behind main (missing production fixes)
- Large divergence between branches (complex merge needed)

❌ CRITICAL:
- main has commits that develop doesn't have (sync broken)
- Branches have completely diverged (major recovery needed)
-->
- Behind count: How many commits develop is missing from main
- Ahead count: How many commits develop has that main doesn't
- Divergence detection: Completely separate branch histories

### 📋 **Version Consistency Diagnosis**

#### **Cross-Branch Version Validation**
<!--
VERSION CONSISTENCY RULES:
1. VERSION file on main should match latest git tag
2. VERSION file on develop should be >= VERSION file on main
3. All version files should follow semantic versioning
4. CHANGELOG.md should have entries for all tagged versions

WHY THESE MATTER:
- Deployment systems use these for version detection
- Inconsistent versions cause deployment confusion
- Breaking versioning contracts confuses users and tools
-->
```bash
# Version consistency check across branches
main_version=$(git show main:VERSION)
develop_version=$(git show develop:VERSION)
latest_tag=$(git describe --tags --abbrev=0 main)

# Check relationships: develop_version >= main_version >= latest_tag
```

#### **Tag Validation and Integrity**
<!--
GIT TAG PROBLEMS:
- Tags exist locally but not on remote (forgotten push)
- Tags point to wrong commits (manual tag creation errors)
- Missing tags for releases (automation failures)
- Duplicate or conflicting tags

TAG VALIDATION CHECKS:
- Local vs remote tag comparison
- Tag commit hash verification
- Tag annotation vs lightweight detection
- Version tag format validation (v1.0.0 vs 1.0.0)
-->
- Local vs remote tag synchronization
- Tag commit hash verification against expected branches
- Version tag format compliance (v1.0.0 pattern)
- Orphaned or duplicate tag detection

### 🔄 **Git-Flow State Diagnosis**

#### **Active Branch Detection**
<!--
INCOMPLETE GIT-FLOW OPERATIONS:
Sometimes git-flow operations get interrupted, leaving:
- Active release branches that should have been deleted
- Feature branches that are completed but not cleaned up
- Hotfix branches that partially merged

WHAT WE LOOK FOR:
- release/* branches (should be temporary)
- feature/* branches that are already merged
- hotfix/* branches with incomplete merges
- develop/main branches in unexpected states
-->
```bash
# Active git-flow branch detection
git branch --list "feature/*" "release/*" "hotfix/*"
git branch -r --list "*/feature/*" "*/release/*" "*/hotfix/*"

# Check for merged but not deleted branches
for branch in $(git branch --merged develop --list "feature/*"); do
    # This feature is merged but still exists - cleanup candidate
done
```

#### **Merge Conflict Detection**
<!--
MERGE CONFLICT SCENARIOS:
- Incomplete merges with conflict markers in files
- Partially resolved conflicts that weren't committed
- .git/MERGE_HEAD exists (merge in progress)
- Index has unmerged paths

DETECTION METHODS:
- git status --porcelain (look for UU, AA, DD markers)
- .git/MERGE_HEAD file existence
- git ls-files --unmerged (check for unmerged index entries)
-->
- Detect incomplete merge operations
- Find files with conflict markers
- Identify merge state in .git directory

## Intelligent Error Recovery

### **Branch Synchronization Fixes**

#### **Automatic Safe Fixes (--fix flag)**
<!--
SAFE AUTOMATIC FIXES:
These fixes don't risk data loss because they only add information:
-->
```bash
# Safe sync fixes that don't lose data
git checkout develop
git pull origin develop                    # Get latest develop changes
git checkout main
git pull origin main                       # Get latest main changes

# If develop is behind main (missing production fixes):
git checkout develop
git merge main --no-ff -m "Sync develop with main production fixes"
git push origin develop
```

#### **Manual Recovery Procedures**
<!--
COMPLEX SYNC ISSUES require human judgment:
When branches have diverged significantly, automatic merging could:
- Choose wrong conflict resolutions
- Lose important development work
- Create inconsistent project state

MANUAL RECOVERY GUIDANCE provides:
- Step-by-step procedures
- Explanation of each step's purpose
- Verification commands to confirm success
- Rollback procedures if something goes wrong
-->
```
⚠️  Complex branch divergence detected - Manual recovery required

📊 Divergence Analysis:
   • main has 3 commits not in develop:
     - abc123f "Hotfix: Security patch"
     - def456g "Hotfix: Performance fix"
     - 789hijf "Release: v1.1.1 tag creation"

   • develop has 7 commits not in main:
     - aaa111a "Feature: User preferences"
     - bbb222b "Feature: Dark mode toggle"
     - ccc333c "Bugfix: Login validation"
     [... 4 more commits ...]

🔧 Manual Recovery Procedure:
   1. Backup current state: git branch backup-develop develop
   2. Merge main into develop: git checkout develop && git merge main
   3. Resolve any conflicts carefully
   4. Test thoroughly before pushing
   5. Push synchronized develop: git push origin develop
   6. Verify success: /health-check-git
```

### **Version Consistency Fixes**

#### **VERSION File Standardization**
<!--
VERSION FILE PROBLEMS:
- Different formats across branches (1.0.0 vs v1.0.0)
- develop version behind main version (missing updates)
- Version doesn't match latest git tag

AUTOMATIC FIXES:
- Standardize format to semantic versioning
- Update develop to match or exceed main version
- Align VERSION with git tag where appropriate
-->
```bash
# Automatic version consistency fixes
main_version=$(git show main:VERSION | tr -d 'v')  # Remove v prefix
develop_version=$(git show develop:VERSION | tr -d 'v')

# Ensure develop >= main version
if version_less_than "$develop_version" "$main_version"; then
    git checkout develop
    echo "$main_version" > VERSION
    git add VERSION
    git commit -m "Sync VERSION file with main branch"
    git push origin develop
fi
```

#### **Tag Recovery and Synchronization**
<!--
TAG RECOVERY SCENARIOS:
1. Local tags exist but not pushed to remote
2. Remote tags exist but not fetched locally
3. Tags point to wrong commits
4. Missing tags for known releases

RECOVERY PROCEDURES:
- Fetch missing tags from remote
- Push missing tags to remote
- Recreate corrupted tags
- Validate tag-to-commit relationships
-->
```bash
# Tag synchronization fixes
git fetch origin --tags                   # Get remote tags
git push origin --tags                    # Push local tags

# Recreate missing release tags based on VERSION file history
for release_commit in $(git log --oneline main --grep="Release" --format="%H"); do
    version=$(git show $release_commit:VERSION)
    if ! git tag -l "v$version" | grep -q "v$version"; then
        git tag -a "v$version" $release_commit -m "Recreated release tag v$version"
    fi
done
```

## Diagnostic Output Examples

### **Healthy Repository**
```
🔍 Git-Flow Health Diagnosis: HEALTHY ✅

🌿 Branch Synchronization: ✅ GOOD
   • main: Up to date (commit abc123f)
   • develop: 2 commits ahead of main (normal development)
   • No divergent history detected

📋 Version Consistency: ✅ GOOD
   • main VERSION (1.1.0) matches latest tag (v1.1.0)
   • develop VERSION (1.2.0) is appropriately ahead
   • All versions follow semantic versioning

🔄 Git-Flow State: ✅ GOOD
   • No active release/hotfix branches
   • No incomplete merge operations
   • Clean working tree across all branches

🏷️  Tag Management: ✅ GOOD
   • All tags synchronized between local and remote
   • Tags point to expected commits
   • No orphaned or duplicate tags

💡 Recommendation: Repository is in excellent state for git-flow operations!
```

### **Problems Detected**
```
🔍 Git-Flow Health Diagnosis: ISSUES FOUND ⚠️

❌ Branch Synchronization: CRITICAL ISSUES
   • main (commit def456g) has 2 commits not in develop:
     - def456g "Hotfix: Critical security patch"
     - abc123f "Release: v1.0.1 tag"
   • develop is missing production fixes!

⚠️  Version Consistency: WARNING
   • develop VERSION (1.0.0) is behind main VERSION (1.0.1)
   • This will cause version conflicts in next release

✅ Git-Flow State: GOOD
   • No active git-flow branches
   • Clean working tree

🔧 RECOMMENDED FIXES:
   1. Sync develop with main: git checkout develop && git merge main
   2. Update develop VERSION to 1.1.0 (next minor version)
   3. Commit and push changes
   4. Verify with: /health-check-git

🚨 CRITICAL: Do not start new releases until synchronization is fixed!
```

## Recovery Verification

### **Post-Fix Validation**
<!--
AFTER FIXING ISSUES, we must verify the fixes worked:
- Re-run all diagnostic checks
- Confirm branch relationships are correct
- Validate version consistency
- Test git-flow operations work properly
-->
```bash
# Comprehensive post-fix validation
/health-check-git                          # Overall repository health
/version-consistency-check                 # Cross-branch version validation
git log --oneline --graph main develop    # Visual branch relationship
```

### **Test Git-Flow Operations**
```bash
# Verify git-flow works after fixes
git flow feature start test-fix            # Should work cleanly
git flow feature finish test-fix           # Should merge to develop only
# Branch should be deleted and develop should be updated
```

## Prevention Strategies

<!--
EDUCATIONAL: How to prevent git-flow problems in the future

1. ALWAYS USE THE ENHANCED COMMANDS:
   - /gitflow-start instead of raw git flow start
   - /gitflow-finish instead of raw git flow finish
   - /release-start and /release-finish for releases

2. REGULAR HEALTH CHECKS:
   - Run /health-check-git weekly
   - Before starting any major git-flow operation
   - After completing releases or hotfixes

3. TEAM COORDINATION:
   - Communicate during releases (avoid conflicting operations)
   - Pull before starting new work
   - Push completed work promptly

4. VERSION DISCIPLINE:
   - Keep VERSION files updated
   - Follow semantic versioning strictly
   - Maintain CHANGELOG.md consistently

5. BACKUP STRATEGIES:
   - Create backup branches before major operations
   - Tag important development milestones
   - Regular pushes to remote repository
-->

### **Preventive Measures:**
1. **Regular Health Checks**: Run `/health-check-git` before major operations
2. **Enhanced Commands**: Use `/gitflow-start`, `/gitflow-finish` instead of raw git-flow
3. **Version Discipline**: Keep VERSION files and tags synchronized
4. **Team Communication**: Coordinate releases and major merges
5. **Backup Strategy**: Create backup branches before complex operations

### **Early Warning Signs:**
- `git status` shows unexpected files or states
- Branches are significantly ahead/behind remote
- Version numbers don't match between branches
- Git-flow commands produce unusual output or errors

## Integration with Git-Flow Commands

- Called automatically by `/release-finish` if issues detected
- Used by `/health-check-git` for detailed problem analysis
- Integrates with `/version-consistency-check` for comprehensive diagnosis
- Provides recovery procedures for all enhanced git-flow commands