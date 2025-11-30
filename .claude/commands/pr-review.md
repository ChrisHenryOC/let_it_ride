# PR Review Command
Review GitHub Pull Request: $ARGUMENTS.

Review the pull request thoroughly, providing actionable feedback on code quality, security, and best practices.

## Instructions

1. **Fetch the PR details** using `gh pr view <PR_NUMBER> --json title,body,files,additions,deletions,commits`

2. **Get the diff** using `gh pr diff <PR_NUMBER>`

3. **Review each changed file** for the criteria below

4. **Provide a structured review** with the format specified

## Review Criteria

### Code Quality
- Clear, descriptive naming (variables, functions, classes)
- Appropriate function/method length (flag if >50 lines)
- Single responsibility principle adherence
- DRY violations (duplicated code)
- Dead code or commented-out code
- Proper error handling (no bare except, meaningful error messages)
- Type hints present and accurate (Python)
- Docstrings for public APIs

### Security Concerns
- Hardcoded secrets, API keys, or credentials
- SQL injection vulnerabilities
- Command injection (subprocess with shell=True, unsanitized input)
- Path traversal vulnerabilities
- Insecure deserialization (pickle, yaml.load without SafeLoader)
- Missing input validation
- Sensitive data in logs
- Insecure randomness (random module for security-sensitive operations)

### Best Practices
- Follows project conventions and style
- Tests included for new functionality
- Tests cover edge cases and error conditions
- No breaking changes to public APIs without justification
- Dependencies added are justified and from trusted sources
- Configuration changes are documented
- Migrations are reversible (if applicable)

### Performance
- Obvious O(n²) or worse algorithms where linear is possible
- N+1 query patterns
- Missing database indexes for new queries
- Large files or data loaded into memory unnecessarily
- Blocking operations in async code

### Documentation
- README updates if user-facing changes
- Inline comments for complex logic
- API documentation for new endpoints/functions

## Output Format

Structure your review as follows:

```markdown
## PR Review: #<NUMBER> - <TITLE>

### Summary
<1-2 sentence overview of the PR and overall assessment>

### 🟢 Strengths
- <What's done well>

### 🔴 Critical Issues (Must Fix)
<Security vulnerabilities or bugs that must be addressed>

#### Issue 1: <Title>
**File:** `path/to/file.py:L42`
**Problem:** <Description>
**Suggestion:** 
```python
# Suggested fix
```

### 🟡 Recommendations (Should Fix)
<Best practice violations, code quality issues>

### 🔵 Suggestions (Consider)
<Minor improvements, style preferences>

### 📋 Checklist
- [ ] Tests pass
- [ ] No security vulnerabilities
- [ ] Code follows project conventions
- [ ] Documentation updated (if needed)

### Verdict
<APPROVE / REQUEST_CHANGES / COMMENT>
<Brief justification>
```

## Usage

```
/pr-review 42
/pr-review 42 --focus security
/pr-review 42 --focus performance
```

If a focus area is specified, prioritize that aspect but still note critical issues in other areas.