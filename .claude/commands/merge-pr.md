---
description: Merge a PR and clean up branches
---

Merge PR $ARGUMENTS and clean up associated branches.

```bash
# Merge the PR (squash merge)
gh pr merge $ARGUMENTS --squash --delete-branch

# Switch to main and pull latest
git checkout main
git pull origin main

# Delete the local branch if it exists
PR_BRANCH=$(gh pr view $ARGUMENTS --json headRefName -q '.headRefName')
git branch -d "$PR_BRANCH" 2>/dev/null || echo "Local branch already deleted or not found"

# Prune any other stale remote tracking branches
git fetch --prune origin
```

Report the merge status and confirm cleanup.
