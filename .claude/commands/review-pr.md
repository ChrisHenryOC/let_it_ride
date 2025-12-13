---
allowed-tools: Bash(gh pr comment:*),Bash(gh pr diff:*),Bash(gh pr view:*),Bash(mkdir:*),Bash(gh api:*),Bash(git add:*),Bash(git commit:*),Bash(git push:*),Bash(gh pr list:*)
description: Review a pull request
---

Perform a comprehensive code review of PR $ARGUMENTS.

## Step 0: Resolve PR Number

If $ARGUMENTS is empty or not provided, auto-detect the PR for the current branch.

**IMPORTANT:** Due to zsh parsing issues, execute these as SEPARATE Bash calls:

1. Get the current branch:
```bash
git branch --show-current
```

2. Find PR for the branch (use the actual branch name from step 1):
```bash
gh pr list --head "<branch-name>" --json number -q '.[0].number'
```

If a PR number is returned, use it for the rest of the review. If no PR is found, ask the user to provide a PR number.

Once resolved, use the PR number for all subsequent steps (replacing $ARGUMENTS if it was empty).

## Step 1: Setup and save the PR diff

BEFORE launching any review agents, set up the output directory and save the diff.

**IMPORTANT:** Due to zsh parsing issues with complex command substitution, execute these as SEPARATE Bash calls:

1. First, get and sanitize the PR title:
```bash
gh pr view $ARGUMENTS --json title -q '.title'
```

2. Then, using the title from step 1, create a sanitized directory name by:
   - Converting to lowercase
   - Replacing non-alphanumeric chars with hyphens
   - Collapsing multiple hyphens
   - **Prefixing with PR number**
   - Example: "feat: LIR-28 JSON Export" for PR 124 becomes "PR124-feat-lir-28-json-export"

3. Create the directory (use the PR number prefix + sanitized title, NOT a shell variable):
```bash
mkdir -p code_reviews/PR124-feat-lir-28-json-export
```

4. Save the diff for agent review:
```bash
gh pr diff $ARGUMENTS > /tmp/pr$ARGUMENTS.diff
```

**Do NOT use complex `$(...)` command substitution with pipes in a single Bash call - it causes zsh parse errors.**

## Step 2: Launch review agents

Launch these subagents in parallel:
- code-quality-reviewer
- performance-reviewer
- test-coverage-reviewer
- documentation-accuracy-reviewer
- security-code-reviewer

Instruct each agent to:
1. Only provide noteworthy feedback
2. Save detailed findings to `code_reviews/PR{number}-{sanitized-title}/{agent-name}.md` (use the directory created in Step 1)

## Step 3: Consolidate and deduplicate

**IMPORTANT: This step creates the CONSOLIDATED-REVIEW.md file that /fix-review depends on.**

After all agents complete:

1. **Read all agent review files** from the directory created in Step 1 (e.g., `code_reviews/PR124-feat-lir-28-json-export/`)
2. **Build an issue matrix** by extracting all Critical, High, and Medium severity issues
3. **Merge overlapping concerns** (e.g., if performance and code-quality flagged the same issue)
4. **Remove duplicates** flagged by multiple agents (count as `duplicate_merges` in metrics)
5. **For each unique issue, determine:**
   - **In PR Scope?**: Is the file/code mentioned actually part of this PR's changes?
   - **Actionable?**: Can this be fixed without adding new dependencies, changing files outside the PR, or major architectural changes?

6. **CREATE the consolidated review file** using the Write tool in the same directory:

```bash
# File path: code_reviews/PR{number}-{sanitized-title}/CONSOLIDATED-REVIEW.md
# Example: code_reviews/PR124-feat-lir-28-json-export/CONSOLIDATED-REVIEW.md
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
ls -la code_reviews/PR{number}-*/CONSOLIDATED-REVIEW.md
# Example: ls -la code_reviews/PR124-*/CONSOLIDATED-REVIEW.md
```

## Step 4: Post summary comment

Post a summary comment on the PR with consolidated findings:
```bash
gh pr comment $ARGUMENTS --body "[summary of key findings by severity]"
```

## Step 5: Commit review files to PR

After completing the review, commit the detailed review files to the PR branch.

**IMPORTANT:** Due to zsh parsing issues, execute these as SEPARATE Bash calls:

1. First, get the PR branch name:
```bash
gh pr view $ARGUMENTS --json headRefName -q '.headRefName'
```

2. Fetch and checkout the branch (use the actual branch name from step 1):
```bash
git fetch origin <branch-name>
git checkout <branch-name>
```

3. Add the review files (use the directory created in Step 1):
```bash
git add code_reviews/PR{number}-{sanitized-title}/
# Example: git add code_reviews/PR124-feat-lir-28-json-export/
```

4. Commit with a heredoc message:
```bash
git commit -m "$(cat <<'EOF'
docs: Add code review findings for PR #$ARGUMENTS

Review conducted by automated agents:
- code-quality-reviewer
- performance-reviewer
- test-coverage-reviewer
- documentation-accuracy-reviewer
- security-code-reviewer

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

5. Push to the PR branch:
```bash
git push origin <branch-name>
```

**Do NOT use `$(...)` command substitution to set shell variables - it causes zsh parse errors.**

This ensures review findings are:
- Preserved with the PR for future reference
- Available for `/fix-review` command to process
- Part of the project's review history

---

## Agent Instructions

The PR diff has been saved to `/tmp/pr$ARGUMENTS.diff`. Each agent MUST:

1. **Read the diff first** using the `Read` tool on `/tmp/pr$ARGUMENTS.diff`
2. **Save detailed findings** to `code_reviews/PR{number}-{sanitized-title}/{agent-name}.md`:
   - Use the directory created in Step 1 (e.g., `code_reviews/PR124-feat-lir-28-json-export/`)
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
4. **CRITICAL: Include observations.errors** - Capture ALL errors encountered during execution:
   - Bash command failures (exit code != 0)
   - Tool errors (parse errors, permission errors, etc.)
   - Agent failures or timeouts
   - Any workarounds you had to apply
   - Example: `"errors": ["Bash parse error near '(' - worked around with separate commands"]`
5. Include **observations.edge_cases_hit** for any unexpected scenarios
6. Include **observations.improvement_suggestions** for command template improvements
7. Append to `.claude/metrics/command_log.jsonl`

**IMPORTANT:** Even if you work around an error successfully, still log it. Error patterns drive command improvements.
