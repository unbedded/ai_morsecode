Generate meaningful commit message from staged changes: $ARGUMENTS

Options:
- `--stage-all` - Stage all changes before analyzing and committing

Implementation:
1. If `--stage-all` specified, run `git add .`
2. Check for staged changes with `git status --porcelain`
3. Analyze staged changes with `git diff --cached`
4. Generate conventional commit message based on:
   - Change type (feat, fix, docs, refactor, etc.)
   - Affected scope/module
   - Clear description of changes
5. Create commit with generated message including Claude Code attribution

Follows conventional commit format and project patterns from recent commit history.