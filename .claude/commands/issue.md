---
allowed-tools: Bash(gh issue view:*),Bash(gh issue list:*),Bash(git checkout:*),Bash(git branch:*),Bash(git push:*)
description: Analyze and fix a GitHub issue
---

Please analyze and fix the GitHub issue: $ARGUMENTS.

# IDENTIFY THE ISSUE

## MANDATORY USER APPROVAL CHECKPOINT

**STOP! Before doing ANY work, you MUST get explicit user approval for the issue.**

This applies to ALL cases - "next", LIR identifiers, and issue numbers.

1. First, identify the issue:
   - **If "next":** Read `docs/implementation_todo.md` and `gh issue list --state open` to find the next issue
   - **If "LIR-N" format:** `gh issue list --search "LIR-N in:title"` to find the GitHub issue
   - **If a number:** `gh issue view $ARGUMENTS` directly

2. **THEN IMMEDIATELY USE AskUserQuestion** to get approval:
   - Present: GitHub issue number, LIR identifier, title, and brief description
   - Ask: "Should I proceed with this issue?"
   - Options: "Yes, proceed" / "No, choose different issue"
   - **DO NOT SKIP THIS STEP. DO NOT PROCEED WITHOUT USER CONFIRMATION.**

3. If user declines, ask which issue they prefer and repeat step 2

4. Only after explicit "Yes" confirmation, proceed to the PLAN phase

# PLAN

1. Use `gh issue view` to get full issue details
2. For complex issues, launch an **Explore agent** (thoroughness: medium) to understand context:
   - Search `/scratchpads/` for previous thoughts on this issue
   - Search closed PRs for related history
   - Find relevant source files and existing patterns
3. Ask clarifying questions if the issue is ambiguous
4. Break the issue into small, manageable tasks using the **TodoWrite tool**
5. For complex architectural decisions, use the **Plan agent**
6. Document your plan in a scratchpad: `/scratchpads/issue-{number}-{short-name}.md`
   - Include link to the GitHub issue
   - List the planned tasks

# CREATE

**CHECKPOINT:** Before writing any code, verify the scratchpad exists:
- File: `/scratchpads/issue-{number}-{short-name}.md`
- Must contain: GitHub issue link, planned tasks
- If missing, create it now before proceeding

- Create branch: `feature/issue-{number}-{short-description}` or `fix/issue-{number}-...`
- Implement in small steps according to your plan
- Commit after each logical step with descriptive messages

# TEST

1. Check the issue for specified test requirements
2. Write tests:
   - Positive tests (verify correct behavior)
   - Negative tests (verify error handling)
3. Run the full test suite: `poetry run pytest`
4. Format and lint code:
   ```bash
   poetry run ruff format src/ tests/ && poetry run ruff check src/ tests/ --fix
   ```
   If any files were modified, stage and amend the previous commit
5. Ensure type checking passes: `poetry run mypy src/`
6. All functions must have type annotations for parameters and return values
7. Launch **test-coverage-reviewer agent** for coverage verification

# VERIFY

Before creating the PR, launch the **code-quality-reviewer agent** to check your implementation.

# PUSH

1. Push branch: `git push -u origin {branch-name}`
2. Create PR with `gh pr create`:
   - Title: `{feat|fix}: LIR-N description`
   - Body must include: `Closes #{github_issue_number}`
3. Note the PR number for `/review-pr`

---

## METRICS LOGGING (Required)

Before presenting the final outcome, log metrics per `.claude/memories/metrics-logging-protocol.md`:

1. Ensure `.claude/metrics/` directory exists
2. Construct the metrics JSON reflecting this execution (command name: "issue", steps_total: 6 - IDENTIFY/PLAN/CREATE/TEST/VERIFY/PUSH)
3. Append to `.claude/metrics/command_log.jsonl`

Pay special attention to the `observations` fields - these drive continuous improvement.