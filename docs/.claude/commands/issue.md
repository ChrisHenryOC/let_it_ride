Please analyze and fix the GitHub issue: $ARGUMENTS.

Follow these steps:

# PLAN
1. Use `gh issue view` to get the issue details
2. Understand the problem described in the issue
3. Ask clarifying questions if necessary
4. Understand the prior art for this issue
    - Search the scratchpads for previous thoughts related to the issue
    - Search PRs to see if you can find history on this issue
    - Search the codebas for relevant files
5. Think harder about how to break the issue down into a series of small, manageable tasks.
6. Document your plan in a new scratchpad
    - Include the issue name in the filename
    - Include a link to the issue in the scratchpad

# CREATE
- Create a new branch for the issue
- Solve the issue in small, manageable steps, according to your plan
- Commit your changes after each step, with a descriptive commit message

# TEST
1. Write and run tests to verify the fix
    - Tests may be described in the issue, check there first
    - Add more tests if they are needed
        - Negative tests (tests that should always fail) need to be written and testing needs to confirm they fail
        - Positive tests (tests that should always pass) need to be written and testing needs to confirm they pass
2. Tests should be committed along with the code, with a descriptive commit message.
3. Ensure all code and tests pass linting and type checking
    - Functions should always be decorated with types for parameters and return values

# PUSH
1. Create a new PR for the work from the branch, referencing the issue name in the PR title
2. Request review for that PR

Remember to use the GitHub CLI (`gh`) for all GitHub-related tasks.