---
allowed-tools: Bash(gh pr comment:*),Bash(gh pr diff:*),Bash(gh pr view:*),Bash(mkdir:*),Bash(gh api:*),Bash(git add:*),Bash(git commit:*),Bash(git push:*),Bash(gh pr list:*)
description: Review a pull request
---

Perform a comprehensive code review of PR $ARGUMENTS.

## Step 0: Resolve PR Number

If $ARGUMENTS is empty or not provided:

```bash
# Try to find PR for current branch
CURRENT_BRANCH=$(git branch --show-current)
PR_NUMBER=$(gh pr list --head "$CURRENT_BRANCH" --json number -q '.[0].number')
if [ -n "$PR_NUMBER" ]; then
    echo "Auto-detected PR #$PR_NUMBER for branch $CURRENT_BRANCH"
    # Use PR_NUMBER as the PR to review
fi
```

If no PR is found for the current branch, ask the user to provide a PR number.

Once resolved, use the PR number for all subsequent steps (replacing $ARGUMENTS if it was empty).

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

## Step 3: Consolidate and deduplicate

**IMPORTANT: This step creates the CONSOLIDATED-REVIEW.md file that /fix-review depends on.**

After all agents complete:

1. **Read all agent review files** from `code_reviews/PR$ARGUMENTS-{title}/`
2. **Build an issue matrix** by extracting all Critical, High, and Medium severity issues
3. **Merge overlapping concerns** (e.g., if performance and code-quality flagged the same issue)
4. **Remove duplicates** flagged by multiple agents (count as `duplicate_merges` in metrics)
5. **For each unique issue, determine:**
   - **In PR Scope?**: Is the file/code mentioned actually part of this PR's changes?
   - **Actionable?**: Can this be fixed without adding new dependencies, changing files outside the PR, or major architectural changes?

6. **CREATE the consolidated review file** using the Write tool:

```bash
# File path: code_reviews/PR$ARGUMENTS-{title}/CONSOLIDATED-REVIEW.md
```

**Required file format:**

```markdown
# Consolidated Code Review for PR #$ARGUMENTS

## Summary
[2-3 sentence summary of overall findings]

## Issue Matrix

| # | Severity | Issue Summary | File:Line | Reviewer(s) | In PR Scope? | Actionable? | Details |
|---|----------|---------------|-----------|-------------|--------------|-------------|---------|
| 1 | Critical | [issue] | file.py:42 | [agent] | Yes/No | Yes/No | [agent].md#C1 |
| 2 | High     | [issue] | file.py:85 | [agent1], [agent2] | Yes/No | Yes/No | [agent1].md#H1 |

## Actionable Issues (Fix in this PR)

Issues where both "In PR Scope?" AND "Actionable?" are Yes:

1. **[Issue Summary]** (Severity) - `file.py:line`
   - Reviewer(s): [agent names]
   - Recommendation: [brief fix description]

## Deferred Issues (Require user decision)

Issues where "Actionable?" is No OR "In PR Scope?" is No:

1. **[Issue Summary]** (Severity) - `file.py:line`
   - Reason: [out of scope / needs new dependency / architectural change / etc.]
   - Reviewer(s): [agent names]
```

**Severity definitions:**
- Critical: Security vulnerabilities, data loss, breaking changes
- High: Performance bottlenecks >10%, missing critical tests
- Medium: Code quality issues affecting maintainability
- Low: Minor suggestions (usually skip)

**VERIFICATION:** Before proceeding to Step 4, confirm the file exists:
```bash
ls -la code_reviews/PR$ARGUMENTS-*/CONSOLIDATED-REVIEW.md
```

## Step 4: Post summary comment

Post a summary comment on the PR with consolidated findings:
```bash
gh pr comment $ARGUMENTS --body "[summary of key findings by severity]"
```

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

## Agent Instructions

The PR diff has been saved to `/tmp/pr$ARGUMENTS.diff`. Each agent MUST:

1. **Read the diff first** using the `Read` tool on `/tmp/pr$ARGUMENTS.diff`
2. **Save detailed findings** to `code_reviews/PR$ARGUMENTS-{title}/{agent-name}.md`:
   - Summary (2-3 sentences)
   - Findings by severity (Critical/High/Medium/Low)
   - Specific recommendations with file:line references

---

## METRICS LOGGING (Required)

Before presenting the final outcome, log metrics per `.claude/memories/metrics-logging-protocol.md`:

1. Ensure `.claude/metrics/` directory exists
2. Construct the metrics JSON reflecting this execution (command name: "review-pr", steps_total: 6)
   - Step 0: Resolve PR number
   - Step 1: Setup and save diff
   - Step 2: Launch review agents
   - Step 3: Consolidate and create CONSOLIDATED-REVIEW.md
   - Step 4: Post summary comment
   - Step 5: Commit review files
3. Include **review_metrics** object with:
   - `issues_by_severity`: {"critical": N, "high": N, "medium": N, "low": N}
   - `actionable_count`: Number of issues marked as actionable (from CONSOLIDATED-REVIEW.md)
   - `deferred_count`: Number of issues marked as deferred (from CONSOLIDATED-REVIEW.md)
   - `duplicate_merges`: Number of duplicate issues merged during consolidation
   - `agents_completed`: Array of agent names that completed successfully
   - `consolidated_review_created`: true/false - whether CONSOLIDATED-REVIEW.md was created
4. Append to `.claude/metrics/command_log.jsonl`

Pay special attention to the `observations` fields - these drive continuous improvement.
