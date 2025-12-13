---
allowed-tools: Bash(gh pr comment:*),Bash(gh pr diff:*),Bash(gh pr view:*),Bash(mkdir:*),Bash(gh api:*),Bash(git add:*),Bash(git commit:*),Bash(git push:*),Bash(gh pr list:*)
description: Review a pull request
---

Review PR $ARGUMENTS (auto-detect from current branch if empty).

## Step 1: Setup

```bash
gh pr view $ARGUMENTS --json title,number -q '.number + " " + .title'
gh pr diff $ARGUMENTS > /tmp/pr$ARGUMENTS.diff
mkdir -p code_reviews/PR$ARGUMENTS-<sanitized-title>
```

Directory name: PR number + lowercase title with non-alphanumeric replaced by hyphens.

## Step 2: Launch Agents

Launch in parallel:
- code-quality-reviewer
- performance-reviewer
- test-coverage-reviewer
- documentation-accuracy-reviewer
- security-code-reviewer

Each agent reads `/tmp/pr$ARGUMENTS.diff` and saves findings to `code_reviews/PR$ARGUMENTS-<title>/{agent}.md`.

## Step 3: Consolidate

After agents complete, create `CONSOLIDATED-REVIEW.md`:

```markdown
# Consolidated Review for PR #$ARGUMENTS

## Summary
[2-3 sentences]

## Issue Matrix
| # | Severity | Issue | File:Line | Reviewer(s) | In PR Scope? | Actionable? |
|---|----------|-------|-----------|-------------|--------------|-------------|

## Actionable Issues
[Issues where In PR Scope AND Actionable are Yes]

## Deferred Issues
[Issues where either is No, with reason]
```

**Severity levels:** Critical (security/data loss), High (>10% perf impact, missing tests), Medium (maintainability), Low (skip).

## Step 4: Post Comment

```bash
gh pr comment $ARGUMENTS --body "[summary by severity]"
```

## Step 5: Commit Review Files

```bash
gh pr view $ARGUMENTS --json headRefName -q '.headRefName'
git fetch origin <branch> && git checkout <branch>
git add code_reviews/PR$ARGUMENTS-*/
git commit -m "docs: Add code review for PR #$ARGUMENTS"
git push origin <branch>
```

---

## Agent Instructions

Each agent:
1. Read `/tmp/pr$ARGUMENTS.diff` first
2. Save findings to `code_reviews/PR$ARGUMENTS-<title>/{agent-name}.md` with:
   - Summary (2-3 sentences)
   - Findings by severity
   - File:line references
