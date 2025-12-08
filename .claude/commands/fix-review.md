Fix high and medium severity issues from code review files for PR: $ARGUMENTS

Follow these steps:

# SETUP

Save the PR diff for reference:
```bash
gh pr diff $ARGUMENTS > /tmp/pr$ARGUMENTS.diff
```

Find the review directory:
```bash
REVIEW_DIR=$(ls -d code_reviews/PR$ARGUMENTS-* 2>/dev/null | head -1)
echo "Review directory: $REVIEW_DIR"
```

List all review files:
```bash
ls "$REVIEW_DIR"
```

Check for @claude comments on the PR and note their IDs for replying later:
```bash
gh api repos/{owner}/{repo}/pulls/$ARGUMENTS/comments --jq '.[] | select(.body | contains("@claude")) | {id, path, body: .body[:80]}'
```

# GATHER FINDINGS

## From Review Files

Read ALL review files in the review directory. For EACH file, extract ALL issues marked as:
1. **Critical** (must fix)
2. **High** (must fix)
3. **Medium** (should fix)

Skip Low severity issues unless specifically requested.

## From @claude PR Comments

If any @claude comments were found in SETUP, treat each as a **High** severity issue:
- Record the comment ID for replying after the fix
- Extract the file path and requested change from the comment
- Add to the issue matrix with "PR Comment" as the reviewer

# BUILD ISSUE MATRIX

**CRITICAL**: Before implementing ANY fixes, build a complete matrix of ALL high and medium issues.

Create a markdown table with ALL findings from ALL reviewers:

| # | Reviewer | Severity | Issue Summary | File:Line | In PR Scope? | Actionable? | Comment ID |
|---|----------|----------|---------------|-----------|--------------|-------------|------------|

Note: "Comment ID" is only populated for @claude PR comments (needed for replies).

For each issue, determine:
- **In PR Scope?**: Is the file/code mentioned actually part of this PR's changes?
- **Actionable?**: Can this be fixed without:
  - Adding new dependencies
  - Changing files outside the PR
  - Major architectural changes

Mark issues as "Deferred" if they are out of scope or require significant work beyond the PR.

# CONSOLIDATE AND DEDUPLICATE

1. Group related issues that multiple reviewers flagged (e.g., performance + code-quality on same function)
2. Identify duplicates (same issue, different wording)
3. Create final deduplicated list with combined recommendations

# CREATE TODO LIST

Use the TodoWrite tool to create a task list of ALL actionable issues:
- One todo per unique issue (or grouped issues)
- Include severity in the todo description (e.g., "[High] Fix docstring mismatch")
- Mark deferred items separately

# IMPLEMENT

For each issue (in priority order: Critical > High > Medium):

1. **Mark todo as in_progress**
2. **Read the relevant file** before making changes
3. **Implement the fix** following project conventions
4. **Mark todo as completed** immediately after fixing
5. **Reply to @claude comments** (if the issue came from a PR comment):
   ```bash
   gh api repos/{owner}/{repo}/pulls/$ARGUMENTS/comments/{COMMENT_ID}/replies \
     --method POST -f body="Fixed in $(git rev-parse --short HEAD). [description of change]"
   ```

# VALIDATE, COMMIT, AND PUSH

After all fixes are implemented, run validation once:
```bash
poetry run pytest tests/unit/ -x -q
poetry run mypy src/
poetry run ruff check src/ tests/
```

Then commit and push:
```bash
git add -A
git commit -m "fix: [description of what was fixed]

Addresses review findings:
- [Reviewer: severity] Issue description

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
git push
```

# HANDLE DEFERRED ITEMS

For EACH deferred item, review it with the user individually using AskUserQuestion.

## Review Process

For each deferred item, present the following context and options:

**Context to show:**
- Issue summary and severity
- Which reviewer(s) flagged it
- Why it was marked as deferred (out of scope, needs new dependency, architectural change, etc.)
- File/location affected

**Ask:** "How should we handle this deferred item: [Issue Summary]?"

**Options:**
- **A) Fix now**: Implement the fix in this PR (add to todo list and implement immediately)
- **B) Create issue**: Create a new GitHub issue and sequence it into implementation_todo.md
- **C) Skip**: Defer with no action (document as "Skipped" in final summary)

## Processing Each Choice

### If user selects A) Fix now:
1. Add the item to the TodoWrite list
2. Implement the fix following the same process as other issues
3. Include in the commit with other fixes
4. Move to next deferred item

### If user selects B) Create issue:
1. Search for related existing LIR issues:
   ```bash
   gh issue list --state open --search "[relevant keywords]"
   ```
2. Ask user: "Should this be added to an existing issue or create a new one?"
   - If existing: Use `gh issue edit ISSUE_NUMBER --body "..."` to append
   - If new: Determine next LIR number from `docs/implementation_todo.md`
3. Create the issue if new:
   ```bash
   gh issue create --title "LIR-XX: [Title]" --body "[Description from review finding]"
   ```
4. Update `docs/implementation_todo.md`:
   - Add the new LIR-XX entry to the appropriate phase
   - Update the execution order if needed
   - Update the Summary section counts
5. Move to next deferred item

### If user selects C) Skip:
1. Document reason for skipping (optional: ask user for reason)
2. Record as "Skipped" in final summary
3. Move to next deferred item

## After All Deferred Items Reviewed

Commit any implementation_todo.md changes:
```bash
git add docs/implementation_todo.md
git commit -m "docs: Update implementation todo with deferred items from PR $ARGUMENTS review

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
git push
```

# FINAL SUMMARY

Build a complete summary with:

## Issues Fixed
| # | Severity | Issue | Reviewer(s) | Replied? |
|---|----------|-------|-------------|----------|

## Initially Deferred Items
| # | Severity | Issue | Decision | Outcome |
|---|----------|-------|----------|---------|

## Validation
- Tests: passed/failed
- Type checking: passed/failed
- Linting: passed/failed

# POST SUMMARY TO PR

Post the final summary as a comment on the PR using a HEREDOC:

```bash
gh pr comment $ARGUMENTS --body "$(cat <<'EOF'
## Code Review Fixes Applied

[Paste the complete final summary here, including:]
- Issues Fixed table
- Initially Deferred Items table
- Validation results

---
🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Then display the same summary to the console for the user.

---

**Critical Reminders:**
- Build the COMPLETE issue matrix BEFORE implementing ANY fixes
- Don't silently skip issues - either fix them or explicitly defer with user consent
- For "B) Create issue": always update `docs/implementation_todo.md`
- Reply to ALL @claude PR comments after fixing

---

## METRICS LOGGING (Required)

Before presenting the final outcome, log metrics per `.claude/memories/metrics-logging-protocol.md`:

1. Ensure `.claude/metrics/` directory exists
2. Construct the metrics JSON reflecting this execution (command name: "fix-review", steps_total: 8 - SETUP/GATHER/BUILD-MATRIX/CONSOLIDATE/TODO/IMPLEMENT/VALIDATE/DEFERRED/SUMMARY)
3. Append to `.claude/metrics/command_log.jsonl`

Pay special attention to the `observations` fields - these drive continuous improvement.
