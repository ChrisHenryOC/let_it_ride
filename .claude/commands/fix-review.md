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

## Check for Consolidated Review (Preferred)

First, check if a consolidated review file exists:

```bash
CONSOLIDATED_FILE="$REVIEW_DIR/CONSOLIDATED-REVIEW.md"
if [ -f "$CONSOLIDATED_FILE" ]; then
    echo "Found consolidated review file"
fi
```

**If `CONSOLIDATED-REVIEW.md` exists:**
1. Read it using the Read tool
2. Extract the Issue Matrix table directly - it already contains all issues with severity, scope, and actionability determined
3. Skip to "## From @claude PR Comments" section to check for additional issues
4. Skip the "# CONSOLIDATE AND DEDUPLICATE" section entirely (already done by /review-pr)

**If `CONSOLIDATED-REVIEW.md` does NOT exist (legacy reviews):**
1. Continue with the standard flow below to read all individual review files
2. Proceed through consolidation and deduplication as normal

## From Review Files (Legacy - skip if using consolidated review)

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

**Skip this section entirely if using CONSOLIDATED-REVIEW.md** (already done by /review-pr).

If NOT using consolidated review (legacy mode):

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

**If there are NO deferred items, skip this entire section and proceed to FINAL SUMMARY.**

## Search for Related Issues First

Before presenting deferred items to the user, search for existing GitHub issues that might be related:

```bash
gh issue list --state open --limit 30 --json number,title,body --jq '.[] | "\(.number): \(.title)"'
```

For each deferred item, identify keywords from the issue (e.g., "performance", "optimization", "aggregation", "test coverage") and check if any open issues cover similar work. Note any matches to present as options.

## Context to Show (Before Asking)

Before presenting the batched questions, display the full context for ALL deferred items:
- Issue summary and severity
- Which reviewer(s) flagged it
- Why it was marked as deferred (out of scope, needs new dependency, architectural change, etc.)
- File/location affected
- **Related existing issues** (if any were found in the search above)

This gives the user complete context before making decisions.

## Batch Question Format

Use AskUserQuestion with up to 4 questions per call. Each question represents one deferred item.

For each deferred item, create a question:
- **header**: Severity label (e.g., "High", "Medium")
- **question**: "[Issue Summary] - [Reason deferred]. How to handle?"
- **multiSelect**: false
- **options** (4 choices):
  - A) Fix now: "Implement in this PR"
  - B) Add to existing issue: "Add to [LIR-XX: Title]" (only if a related issue was found)
  - C) Create new issue: "Create new GitHub issue for later"
  - D) Skip: "No action needed"

**Note**: If no related existing issue was found, omit option B and use only 3 options.

Example with related issue found:
```
questions: [
  {
    header: "High",
    question: "Redundant aggregation computation - requires architectural change. How to handle?",
    multiSelect: false,
    options: [
      {label: "Fix now", description: "Implement in this PR"},
      {label: "Add to LIR-35", description: "Add to existing Performance Optimization issue (#38)"},
      {label: "Create new issue", description: "Create new GitHub issue for later"},
      {label: "Skip", description: "No action needed"}
    ]
  }
]
```

Example without related issue:
```
questions: [
  {
    header: "Medium",
    question: "Missing integration test - out of PR scope. How to handle?",
    multiSelect: false,
    options: [
      {label: "Fix now", description: "Implement in this PR"},
      {label: "Create new issue", description: "Create new GitHub issue for later"},
      {label: "Skip", description: "No action needed"}
    ]
  }
]
```

**Batching rule**: If more than 4 deferred items exist, use multiple AskUserQuestion calls in batches of 4. Process each batch's responses before moving to the next batch.

## Processing Batch Responses

After receiving all responses for a batch:
1. Group items by decision (Fix now / Add to existing / Create new / Skip)
2. Process all "Fix now" items together - add to TodoWrite and implement
3. Process all "Add to existing issue" items together - append to existing issues
4. Process all "Create new issue" items together - create issues and update implementation_todo.md
5. Document all "Skip" items together in final summary

## Processing Each Choice

### If user selects A) Fix now:
1. Add the item to the TodoWrite list
2. Implement the fix following the same process as other issues
3. Include in the commit with other fixes
4. Move to next deferred item

### If user selects B) Add to existing issue:
1. Get the current issue body:
   ```bash
   gh issue view ISSUE_NUMBER --json body -q '.body'
   ```
2. Append the deferred item details to the issue body using `gh issue edit`:
   ```bash
   gh issue edit ISSUE_NUMBER --body "[existing body]

   ## Additional Item from PR #$ARGUMENTS Review
   **Issue**: [Description from review finding]
   **File**: [file:line]
   **Reviewer**: [reviewer name]
   **Recommendation**: [specific recommendation]"
   ```
3. Record as "Added to [LIR-XX]" in final summary
4. Move to next deferred item

### If user selects C) Create new issue:
1. Determine next LIR number from `docs/implementation_todo.md`
2. Create the issue:
   ```bash
   gh issue create --title "LIR-XX: [Title]" --body "[Description from review finding]"
   ```
3. Update `docs/implementation_todo.md`:
   - Add the new LIR-XX entry to the appropriate phase
   - Update the execution order if needed
   - Update the Summary section counts
4. Record as "Created [LIR-XX]" in final summary
5. Move to next deferred item

### If user selects D) Skip:
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

Decision values: "Fix now", "Add to existing", "Create new issue", "Skip"
Outcome examples: "Fixed in commit abc123", "Added to LIR-35 (#38)", "Created LIR-56 (#117)", "Skipped - not needed"

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
2. Construct the metrics JSON reflecting this execution (command name: "fix-review", steps_total: 8)
3. Include **fix_metrics** object with:
   - `issues_fixed`: Number of issues fixed in this PR
   - `issues_deferred`: Number of issues presented to user as deferred
   - `deferred_decisions`: {"fix_now": N, "add_to_existing": N, "create_issue": N, "skip": N}
   - `new_issues_created`: Array of new issue identifiers created (e.g., ["LIR-XX"])
   - `existing_issues_updated`: Array of issue identifiers that had items added (e.g., ["LIR-35"])
   - `used_consolidated_review`: true if CONSOLIDATED-REVIEW.md was used, false otherwise
4. Append to `.claude/metrics/command_log.jsonl`

Pay special attention to the `observations` fields - these drive continuous improvement.
