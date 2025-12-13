# Base Reviewer Template

This file contains shared context for all reviewer agents. Individual agents extend this with their specialty focus.

## Project Context

- **Project**: Let It Ride poker simulator (Python)
- **Performance target**: ≥100,000 hands/second
- **Memory target**: <4GB RAM for 10M hands
- **Standards**: Type hints required, Pydantic models, ruff linting, dataclasses with `__slots__`

## Review Process

1. Read `/tmp/pr{NUMBER}.diff` using the Read tool
2. Focus on changed lines (+ lines in diff)
3. Flag issues only in new/modified code unless critical
4. Write findings to `code_reviews/PR{NUMBER}-{title}/{agent-name}.md`

## Output Format

```markdown
# {Agent Name} Review for PR #{NUMBER}

## Summary
[2-3 sentences]

## Findings

### Critical
[Security vulnerabilities, data loss, breaking changes]

### High
[Performance >10% impact, missing critical tests]

### Medium
[Code quality affecting maintainability]

### Low
[Minor suggestions - usually skip]
```

Each finding: **Issue** - `file.py:line` - Recommendation

## Severity Definitions

- **Critical**: Security vulnerabilities, data loss, breaking changes
- **High**: Performance bottlenecks >10%, missing critical tests
- **Medium**: Code quality issues affecting maintainability
- **Low**: Minor suggestions (typically skip)
