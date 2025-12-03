---
allowed-tools: Bash(gh issue view:*),Bash(gh issue list:*),Bash(git checkout:*),Bash(git branch:*),Bash(git push:*)
description: Analyze and fix a GitHub issue
---

Please analyze and fix the GitHub issue: $ARGUMENTS.

# IDENTIFY THE ISSUE

1. Determine if $ARGUMENTS is a LIR identifier or GitHub issue number:
   - If "LIR-N" format: `gh issue list --search "LIR-N in:title"` to find the GitHub issue
   - If a number: `gh issue view $ARGUMENTS` directly
2. Confirm the issue title and description match expectations before proceeding

# PLAN

1. Use `gh issue view` to get full issue details
2. Launch an **Explore agent** (thoroughness: medium) to understand context:
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

- Create branch: `feature/issue-{number}-{short-description}` or `fix/issue-{number}-...`
- Implement in small steps according to your plan
- Commit after each logical step with descriptive messages

# TEST

1. Check the issue for specified test requirements
2. Write tests:
   - Positive tests (verify correct behavior)
   - Negative tests (verify error handling)
3. Run the full test suite: `poetry run pytest`
4. Ensure linting passes: `poetry run ruff check src/ tests/`
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
3. Note the PR number for review

# REVIEW (separate session)

After creating the PR, start a fresh session for unbiased review:
1. Run `/clear` to reset context
2. Run `/review-pr {pr_number}` for automated review

Remember to use the GitHub CLI (`gh`) for all GitHub-related tasks.