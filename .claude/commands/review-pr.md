---
allowed-tools: Bash(gh pr comment:*),Bash(gh pr diff:*),Bash(gh pr view:*)
description: Review a pull request
---

Perform a comprehensive code review of PR $ARGUMENTS.

## Step 1: Save the PR diff

BEFORE launching any review agents, save the diff:
```bash
gh pr diff $ARGUMENTS > /tmp/pr$ARGUMENTS.diff
```

## Step 2: Launch review agents

Launch these subagents in parallel:
- code-quality-reviewer
- performance-reviewer
- test-coverage-reviewer
- documentation-accuracy-reviewer
- security-code-reviewer

Instruct each to only provide noteworthy feedback.

## Step 3: Post comments

Review agent feedback and post only what you deem noteworthy:
- Inline comments for specific issues
- Top-level comments for general observations
- Keep feedback concise

## Agent Instructions for Inline Comments

The PR diff has been saved to `/tmp/pr$ARGUMENTS.diff`. Each agent MUST:

1. **Read the diff first** - Use `Read` tool on `/tmp/pr$ARGUMENTS.diff`

2. **For each issue requiring an inline comment**, calculate the position:
   - Find the file's `@@` hunk header line number in the diff (use `grep -n "@@"`)
   - Find your target line number in the diff
   - Position = target_line_number - hunk_header_line_number + 1

3. **Return in this exact format** (positions are REQUIRED):
   ```
   INLINE_COMMENT:
   - file: src/example/file.py
   - position: 42
   - comment: Your comment text here
   ```

**Example calculation:**
- File's `@@` line is at diff line 185
- Target code is at diff line 210
- Position = 210 - 185 + 1 = 26

Comments without calculated positions will be discarded.

---
