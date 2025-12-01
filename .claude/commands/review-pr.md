---
allowed-tools: Bash(gh pr comment:*),Bash(gh pr diff:*),Bash(gh pr view:*)
description: Review a pull request
---

Perform a comprehensive code review using subagents for key areas:

- code-quality-reviewer
- performance-reviewer
- test-coverage-reviewer
- documentation-accuracy-reviewer
- security-code-reviewer

Instruct each to only provide noteworthy feedback. Once they finish, review the feedback and post only the feedback that you also deem noteworthy.

Provide feedback using inline comments for specific issues.
Use top-level comments for general observations or praise.
Keep feedback concise.

## Agent Instructions for Inline Comments

Each agent MUST return issues requiring inline comments in this structured format:

```
INLINE_COMMENT:
- file: <path>
- position: <calculated position in diff>
- comment: <the comment text>
```

To calculate position:
1. The diff hunk header (@@) line is position 1
2. Count lines from there to the target line
3. Position = target_line_in_diff - hunk_header_line + 1

Agents should save the PR diff at the start of their analysis and reference it when identifying issues. This eliminates the need for position lookups after agents complete.

---
