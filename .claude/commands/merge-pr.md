---
description: Merge a PR and clean up branches
---

Merge PR $ARGUMENTS and clean up associated branches.

**IMPORTANT:** Due to zsh parsing issues, execute these as SEPARATE Bash calls (do NOT use shell variable assignment with `$(...)` in a single call):

1. Merge the PR (squash merge):
```bash
gh pr merge $ARGUMENTS --squash --delete-branch
```

2. Switch to main and pull latest:
```bash
git checkout main && git pull origin main
```

3. Get the PR branch name:
```bash
gh pr view $ARGUMENTS --json headRefName -q '.headRefName'
```

4. Delete the local branch (use the actual branch name from step 3):
```bash
git branch -d "<branch-name>" 2>/dev/null || echo "Local branch already deleted or not found"
```

5. Prune stale remote tracking branches:
```bash
git fetch --prune origin
```

Report the merge status and confirm cleanup.
