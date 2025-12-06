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

Provide a complete summary with:

## Issues Fixed
| # | Severity | Issue | Reviewer(s) |
|---|----------|-------|-------------|
| 1 | High | ... | test-coverage |
| 2 | Medium | ... | code-quality, performance |

## Initially Deferred Items
| # | Severity | Issue | Decision | Outcome |
|---|----------|-------|----------|---------|
| 1 | Medium | Add hypothesis tests | A) Fix now | Fixed in this PR |
| 2 | Medium | GameHandResult slots | B) Create issue | New issue LIR-XX (GitHub #YY) |
| 3 | Medium | Registry pattern refactor | B) Create issue | Added to LIR-XX (GitHub #YY) |
| 4 | Low | Minor style suggestion | C) Skip | No action taken |

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
- Review EACH deferred item individually with the user (A/B/C decision)
- For "B) Create issue" items: always update implementation_todo.md with proper sequencing
- For "A) Fix now" items: add back to todo list and implement before finalizing
