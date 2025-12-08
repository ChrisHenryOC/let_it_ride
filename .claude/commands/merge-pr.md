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

---

## METRICS LOGGING (Required)

Before presenting the final outcome, log metrics per `.claude/memories/metrics-logging-protocol.md`:

1. Ensure `.claude/metrics/` directory exists
2. Construct the metrics JSON reflecting this execution (command name: "merge-pr", steps_total: 4 - merge/checkout/delete-local/prune)
3. Append to `.claude/metrics/command_log.jsonl`

Pay special attention to the `observations` fields - these drive continuous improvement.
