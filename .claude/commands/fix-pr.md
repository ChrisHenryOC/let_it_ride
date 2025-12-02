Please review comments tagged with "@claude" in the Pull Request: $ARGUMENTS.

Follow these steps:

# PLAN
1. Review overall the PR findings
2. Review unresolved comments with "@claude" in the reply
3. Ask clarifying questions if necessary
4. Understand the prior art for this issue
    - Search the scratchpads for previous thoughts related to the issue
    - Search PRs to see if you can find history on this issue
    - Search the codebas for relevant files
5. Think harder about how to break the issue down into a series of small, manageable tasks.

# CREATE
- Solve the issue in small, manageable steps, according to your plan
- Commit your changes after each step, with a descriptive commit message

# TEST
1. Update any tests that need to be changed based on the implemented code changes
2. Create any new tests as needed
2. Tests should be committed along with the code, with a descriptive commit message.
3. Ensure all code and tests pass linting and type checking
    - Functions should always be decorated with types for parameters and return values

# PUSH
1. Create a new PR for the work from the branch, referencing the issue name in the PR title
2. Request review for that PR

Remember to use the GitHub CLI (`gh`) for all GitHub-related tasks.