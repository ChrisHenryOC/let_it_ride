Fix high and medium severity issues from code review for PR $ARGUMENTS.

# SETUP

```bash
gh pr diff $ARGUMENTS > /tmp/pr$ARGUMENTS.diff
ls -d code_reviews/PR$ARGUMENTS-* 2>/dev/null | head -1
```

Check for @claude comments:
```bash
gh api repos/{owner}/{repo}/pulls/$ARGUMENTS/comments --jq '.[] | select(.body | contains("@claude")) | {id, path, body: .body[:80]}'
```

# GATHER FINDINGS

Read `CONSOLIDATED-REVIEW.md` from the review directory. It contains the Issue Matrix with severity, scope, and actionability already determined.

Also add any @claude PR comments as High severity issues (record comment ID for later reply).

# BUILD ISSUE MATRIX

Before implementing fixes, create a matrix of ALL issues:

| # | Reviewer | Severity | Issue | File:Line | In PR Scope? | Actionable? |
|---|----------|----------|-------|-----------|--------------|-------------|

**Actionable** = Can fix without adding dependencies, changing files outside PR, or major refactoring.

# CREATE TODO LIST

Use TodoWrite to track actionable issues:
- One todo per issue with severity prefix (e.g., "[High] Fix docstring")
- Mark deferred items separately

# IMPLEMENT

For each issue (Critical > High > Medium):
1. Mark todo in_progress
2. Read the file before editing
3. Implement the fix
4. Mark todo completed
5. Reply to @claude comments if applicable:
   ```bash
   gh api repos/{owner}/{repo}/pulls/$ARGUMENTS/comments/{ID}/replies --method POST -f body="Fixed. [description]"
   ```

# VALIDATE AND COMMIT

```bash
poetry run pytest tests/unit/ -x -q && poetry run mypy src/ && poetry run ruff check src/ tests/
git add -A && git commit -m "fix: Address review findings" && git push
```

# HANDLE DEFERRED ITEMS

Skip if no deferred items or all are Low severity (auto-skip Low items).

For High/Medium deferred items, use AskUserQuestion with options:
- Fix now
- Add to existing issue (if related issue found)
- Create new issue
- Skip

**If "Create new issue"**: Also update `docs/implementation_todo.md` with new LIR entry.

# FINAL SUMMARY

Post to PR with:
- Issues Fixed table
- Deferred Items table (with decisions/outcomes)
- Validation results

```bash
gh pr comment $ARGUMENTS --body "$(cat <<'EOF'
## Code Review Fixes Applied
[summary tables]
EOF
)"
```

**Reminders:**
- Build complete matrix BEFORE implementing
- Reply to all @claude comments
- Update implementation_todo.md for new issues
