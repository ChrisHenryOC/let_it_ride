---
allowed-tools: Bash(gh pr comment:*),Bash(gh pr diff:*),Bash(gh pr view:*),Bash(mkdir:*),Bash(gh api:*),Bash(git add:*),Bash(git commit:*),Bash(git push:*)
description: Review a pull request
---

Perform a comprehensive code review of PR $ARGUMENTS.

## Step 1: Setup and save the PR diff

BEFORE launching any review agents, set up the output directory and save the diff:
```bash
# Create output directory with sanitized PR title
PR_TITLE=$(gh pr view $ARGUMENTS --json title -q '.title' | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//' | sed 's/-$//')
mkdir -p code_reviews/PR$ARGUMENTS-$PR_TITLE

# Save the diff for agent review
gh pr diff $ARGUMENTS > /tmp/pr$ARGUMENTS.diff
```

## Step 2: Launch review agents

Launch these subagents in parallel:
- code-quality-reviewer
- performance-reviewer
- test-coverage-reviewer
- documentation-accuracy-reviewer
- security-code-reviewer

Instruct each agent to:
1. Only provide noteworthy feedback
2. Save detailed findings to `code_reviews/PR$ARGUMENTS-{title}/{agent-name}.md`

## Step 3: Post comments

Review agent feedback and post only what you deem noteworthy:
- Inline comments for specific issues
- Top-level comments for general observations
- Keep feedback concise

## Step 4: Consolidate and deduplicate

Before posting comments:
1. Review all agent findings from `code_reviews/PR$ARGUMENTS-*/`
2. Merge overlapping concerns (e.g., performance + code quality on same issue)
3. Remove duplicates flagged by multiple agents
4. Prioritize: Critical > High > Medium (skip Low unless significant)

**Severity definitions:**
- Critical: Security vulnerabilities, data loss, breaking changes
- High: Performance bottlenecks >10%, missing critical tests
- Medium: Code quality issues affecting maintainability
- Low: Minor suggestions (usually skip posting)

## Step 5: Commit review files to PR

After completing the review, commit the detailed review files to the PR branch:

```bash
# Get the PR branch name and check it out
PR_BRANCH=$(gh pr view $ARGUMENTS --json headRefName -q '.headRefName')
git fetch origin $PR_BRANCH
git checkout $PR_BRANCH

# Add and commit the review files
git add code_reviews/PR$ARGUMENTS-*/
git commit -m "docs: Add code review findings for PR #$ARGUMENTS

Review conducted by automated agents:
- code-quality-reviewer
- performance-reviewer
- test-coverage-reviewer
- documentation-accuracy-reviewer
- security-code-reviewer

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to the PR branch
git push origin $PR_BRANCH
```

This ensures review findings are:
- Preserved with the PR for future reference
- Available for `/fix-review` command to process
- Part of the project's review history

---

## Agent Instructions for Inline Comments

The PR diff has been saved to `/tmp/pr$ARGUMENTS.diff`. Each agent MUST:

1. **Read the diff first** - Use the `Read` tool on `/tmp/pr$ARGUMENTS.diff` (do NOT use Bash with cat)

2. **Save detailed findings** to `code_reviews/PR$ARGUMENTS-{title}/{agent-name}.md`
   Structure as:
   - Summary (2-3 sentences)
   - Findings by severity (Critical/High/Medium/Low)
   - Specific recommendations with file:line references

3. **For each issue requiring an inline comment**, calculate the position:
   - Find the file's `@@` hunk header line number in the diff
   - Find your target line number in the diff
   - Position = target_line_number - hunk_header_line_number
     (The @@ line itself is position 1, so do NOT add 1)

4. **Return in this exact format** (positions are REQUIRED):
   ```
   INLINE_COMMENT:
   - file: src/example/file.py
   - position: 42
   - comment: Your comment text here
   ```

**Example calculation:**
- File's `@@` line is at diff line 185
- Target code is at diff line 210
- Position = 210 - 185 = 25

Comments without calculated positions will be discarded.

---
