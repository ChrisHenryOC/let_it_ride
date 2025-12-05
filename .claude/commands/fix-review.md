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

# GATHER FINDINGS

Read ALL review files in the review directory. For EACH file, extract ALL issues marked as:
1. **Critical** (must fix)
2. **High** (must fix)
3. **Medium** (should fix)

Skip Low severity issues unless specifically requested.

# BUILD ISSUE MATRIX

**CRITICAL**: Before implementing ANY fixes, build a complete matrix of ALL high and medium issues.

Create a markdown table with ALL findings from ALL reviewers:

| # | Reviewer | Severity | Issue Summary | File:Line | In PR Scope? | Actionable? |
|---|----------|----------|---------------|-----------|--------------|-------------|
| 1 | code-quality | Medium | Description... | file.py:123 | Yes/No | Yes/No |
| 2 | performance | Medium | Description... | file.py:456 | Yes/No | Yes/No |
| ... | ... | ... | ... | ... | ... | ... |

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
- Include severity in the todo description
- Mark deferred items separately

Example:
```
1. [High] Fix TypeError/ValueError docstring mismatch in from_dict
2. [Medium] Add type-specific count functions (addresses code-quality + performance)
3. [Medium] Use Counter for distribution counting
4. [Deferred] Add hypothesis property-based tests (requires new dependency)
```

# IMPLEMENT

For each issue (in priority order: Critical > High > Medium):

1. **Mark todo as in_progress**
2. **Read the relevant file** before making changes
3. **Implement the fix** following project conventions
4. **Mark todo as completed** immediately after fixing
5. **Run validation** after each fix:
   ```bash
   poetry run pytest tests/unit/ -x -q
   poetry run mypy src/
   poetry run ruff check src/ tests/
   ```

# COMMIT

After each logical group of fixes:
```bash
git add -A
git commit -m "fix: [description of what was fixed]

Addresses review findings:
- [Reviewer: severity] Issue description
- [Reviewer: severity] Issue description

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

# PUSH

Push all commits to the PR branch:
```bash
git push
```

# HANDLE DEFERRED ITEMS

If there are any deferred items, use AskUserQuestion to ask:

"Which deferred items should be scheduled for future work?"

Present options:
- Each deferred item as a selectable option (multiSelect: true)
- User selects which items should be tracked for future implementation

For items the user selects:
1. Determine if it fits an existing issue (search for related LIR issues)
2. If yes: Use `gh issue edit` to append the task to that issue's body
3. If no: Use `gh issue create` to create a new LIR-numbered issue
4. Update `docs/implementation_todo.md` to reflect any changes

Items not selected are documented as "Skipped" in the final summary.

# FINAL SUMMARY

Provide a complete summary with:

## Issues Fixed
| # | Severity | Issue | Reviewer(s) |
|---|----------|-------|-------------|
| 1 | High | ... | test-coverage |
| 2 | Medium | ... | code-quality, performance |

## Issues Deferred
| # | Severity | Issue | Disposition |
|---|----------|-------|-------------|
| 1 | Medium | Add hypothesis tests | Added to LIR-XX (GitHub #YY) |
| 2 | Medium | GameHandResult slots | New issue LIR-XX created (GitHub #YY) |
| 3 | Low | Minor style suggestion | Skipped |

## Validation
- Tests: X passed
- Type checking: passed/failed
- Linting: passed/failed

---

**Remember:**
- Build the COMPLETE issue matrix BEFORE implementing ANY fixes
- Use TodoWrite to track ALL issues systematically
- Mark each todo complete IMMEDIATELY after fixing
- Document ALL deferred issues with clear reasons
- Don't silently skip issues - either fix them or document why they're deferred
- Always ask user about deferred items before finalizing
