Please review comments tagged with "@claude" in the Pull Request: $ARGUMENTS.

Follow these steps:

# SETUP

Save the PR diff for reference:
```bash
gh pr diff $ARGUMENTS > /tmp/pr$ARGUMENTS.diff
```

Check for existing review artifacts:
```bash
ls code_reviews/ | grep "PR$ARGUMENTS" || echo "No existing review directory"
```

Identify @claude comments and their IDs for replying later:
```bash
gh api repos/{owner}/{repo}/pulls/$ARGUMENTS/comments --jq '.[] | select(.body | contains("@claude")) | {id, path, body: .body[:80]}'
```

# PLAN
1. Review overall the PR findings
2. Review unresolved comments with "@claude" in the reply
3. Ask clarifying questions if necessary
4. Understand the prior art for this issue
    - Search the scratchpads for previous thoughts related to the issue
    - Search PRs to see if you can find history on this issue
    - Search the codebase for relevant files
5. Think harder about how to break the issue down into a series of small, manageable tasks.
6. Note comment IDs that need replies after fixes are made

# CREATE
- Solve the issue in small, manageable steps, according to your plan
- Commit your changes after each step, with a descriptive commit message
- After fixing each @claude comment, reply to acknowledge:
  ```bash
  gh api repos/{owner}/{repo}/pulls/$ARGUMENTS/comments/{COMMENT_ID}/replies \
    --method POST -f body="Fixed in $(git rev-parse --short HEAD). [description of change]"
  ```

# TEST
1. Update any tests that need to be changed based on the implemented code changes
2. Create any new tests as needed
3. Tests should be committed along with the code, with a descriptive commit message.
4. Ensure all code and tests pass linting and type checking
    - Functions should always be decorated with types for parameters and return values

# PUSH
1. Push commits to the existing PR branch
2. Verify all @claude comments have been replied to

Remember to use the GitHub CLI (`gh`) for all GitHub-related tasks.
