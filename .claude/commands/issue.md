---
allowed-tools: Bash(gh issue view:*),Bash(gh issue list:*),Bash(git checkout:*),Bash(git branch:*),Bash(git push:*)
description: Analyze and fix a GitHub issue
---

Analyze and fix GitHub issue: $ARGUMENTS

## 1. IDENTIFY & APPROVE

**Required before ANY work:**
1. Find issue:
   - "next": Check `docs/implementation_todo.md` + `gh issue list --state open`
   - "LIR-N": `gh issue list --search "LIR-N in:title"`
   - Number: `gh issue view $ARGUMENTS`
2. **Use AskUserQuestion** for approval (GitHub #, LIR-N, title, description)
3. Only proceed after explicit "Yes"

## 2. PLAN

1. `gh issue view` for full details
2. For complex issues, launch **Explore agent** (quick):
   - Check `/scratchpads/INDEX.md` for related prior work (read full scratchpad only if directly relevant)
   - Search for similar patterns in source code
3. Break into tasks with **TodoWrite**
4. Create scratchpad: `/scratchpads/issue-{number}-{short-name}.md` with issue link + tasks
5. Update index: `echo "| #{number} | {Description} |" >> /scratchpads/INDEX.md`

## 3. CREATE

1. Create branch: `feature/issue-{number}-{desc}` or `fix/issue-{number}-{desc}`
2. Stage scratchpad: `git add scratchpads/issue-{number}-*.md`
3. Implement in small steps, commit after each
4. Include scratchpad in first commit

## 4. TEST

1. Write positive + negative tests
2. Run: `poetry run pytest`
3. Format/lint: `poetry run ruff format src/ tests/ && poetry run ruff check src/ tests/ --fix`
4. Type check: `poetry run mypy src/`
5. All functions need type annotations

## 5. PUSH & PR

1. Push: `git push -u origin {branch}`
2. Create PR: `gh pr create` with title `{feat|fix}: LIR-N description`, body includes `Closes #{github_issue_number}`

Note: Code review happens via `/review-pr` after PR creation.
