---
description: Merge a PR and clean up branches
allowed-tools: Bash(gh pr merge:*),Bash(git checkout:*),Bash(git pull:*),Bash(git fetch:*),Bash(git branch:*)
---

Run these commands to merge PR $ARGUMENTS:

```bash
gh pr merge $ARGUMENTS --squash --delete-branch && git checkout main && git pull origin main && git fetch --prune origin
```

Report: "PR #$ARGUMENTS merged. On branch main."
