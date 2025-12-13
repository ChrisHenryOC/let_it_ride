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

---

## METRICS LOGGING (Required)

Before presenting the final outcome, log metrics per `.claude/memories/metrics-logging-protocol.md`:

1. Ensure `.claude/metrics/` directory exists
2. Construct the metrics JSON reflecting this execution (command name: "merge-pr", steps_total: 5 - merge/checkout/get-branch/delete-local/prune)
3. **CRITICAL: Include observations.errors** - Capture ALL errors encountered during execution:
   - Bash command failures (exit code != 0)
   - Tool errors (parse errors, permission errors, zsh issues, etc.)
   - Merge conflicts or failures
   - Any workarounds you had to apply
   - Example: `"errors": ["Branch already deleted on remote"]`
4. Include **observations.edge_cases_hit** for unexpected scenarios
5. Include **observations.improvement_suggestions** for command template improvements
6. Append to `.claude/metrics/command_log.jsonl`

**IMPORTANT:** Even if you work around an error successfully, still log it. Error patterns drive command improvements.
