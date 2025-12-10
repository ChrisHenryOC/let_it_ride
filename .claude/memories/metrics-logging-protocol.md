# Metrics Logging Protocol

This protocol defines how to log metrics at the end of every slash command execution. These metrics enable continuous improvement of command effectiveness.

## When to Log

Log metrics as the **FINAL step** of every command, immediately before presenting the final summary to the user. Log even on failure - failure data is especially valuable.

## How to Log

1. Create the metrics directory if it does not exist:
   ```bash
   mkdir -p .claude/metrics
   ```

2. Construct a single-line JSON object following the schema below

3. Append to the log file:
   ```bash
   echo '{"timestamp":"...","command":{...},...}' >> .claude/metrics/command_log.jsonl
   ```

## Schema

### timestamp (required)
ISO 8601 format: `2025-12-08T14:32:15Z`

### command (required)
- `name`: Command name without slash (e.g., "review-pr", "issue", "merge-pr", "fix-review")
- `arguments`: Raw arguments exactly as passed

### context
- `branch`: Current git branch (`git branch --show-current`)
- `repo_state`: One of "clean", "dirty", "untracked", "staged"
- `related_pr`: PR number if applicable, otherwise null
- `related_issue`: Issue identifier if applicable (e.g., "LIR-15" or "#42"), otherwise null

### outcome (required)
- `status`: One of:
  - `success`: All steps completed successfully
  - `partial_success`: Main goal achieved but with skipped/failed substeps
  - `failure`: Could not complete the main objective
  - `aborted`: User cancelled or command was interrupted
- `failure_reason`: Brief explanation if not success, otherwise null

### metrics
- `steps_completed`: Count of major steps finished
- `steps_total`: Expected steps per the command definition
- `tool_calls`: Approximate number of tool invocations
- `clarifications_required`: Times you asked the user for clarification
- `duration_estimate`: One of "<1min", "1-5min", "5-15min", ">15min"

### review_metrics (for /review-pr command)
- `issues_by_severity`: Object with counts per severity level
  - Example: `{"critical": 0, "high": 2, "medium": 3, "low": 5}`
- `actionable_count`: Number of issues marked as actionable (can be fixed in this PR)
- `deferred_count`: Number of issues marked as deferred (need user decision)
- `duplicate_merges`: Number of issues identified as duplicates and merged during consolidation
- `agents_completed`: Array of agent names that completed successfully
  - Example: `["code-quality", "performance", "test-coverage", "docs", "security"]`

### fix_metrics (for /fix-review command)
- `issues_fixed`: Number of issues fixed in the PR
- `issues_deferred`: Number of issues presented to user as deferred items
- `deferred_decisions`: Object with counts of user decisions
  - Example: `{"fix_now": 1, "create_issue": 1, "skip": 2}`
- `new_issues_created`: Array of issue identifiers created for deferred items
  - Example: `["LIR-55", "LIR-56"]` or `[]` if none created
- `used_consolidated_review`: Boolean - true if CONSOLIDATED-REVIEW.md was used, false if legacy mode

### observations (most important for improvement)

Reflect honestly on the execution:

- `clarification_types`: Array of categories when clarification was needed:
  - `ambiguous_argument`: Argument meaning was unclear
  - `missing_context`: Needed information not provided
  - `conflicting_instructions`: Command instructions contradicted each other
  - `external_dependency`: Blocked by external system/API
  - `permission_issue`: Lacked necessary permissions
  - `unexpected_state`: Repo/PR/issue in unexpected state
  - `scope_clarification`: Unclear what was in/out of scope
  - `other`: Doesn't fit other categories

- `edge_cases_hit`: Array of unexpected scenarios that needed handling (e.g., "branch already deleted", "PR already merged", "no changes to commit")

- `errors`: Array of error messages encountered

- `warnings`: Array of non-fatal issues

- `ambiguities`: Array of instructions in the command file that were unclear or could be interpreted multiple ways

- `missing_instructions`: Array of steps you had to improvise that should be documented in the command file

- `improvement_suggestions`: Array of ideas to make the command better

## Example Log Entry

After completing `/merge-pr 108`:

```json
{"timestamp":"2025-12-08T14:32:15Z","command":{"name":"merge-pr","arguments":"108"},"context":{"branch":"main","repo_state":"clean","related_pr":108,"related_issue":null},"outcome":{"status":"success","failure_reason":null},"metrics":{"steps_completed":4,"steps_total":4,"tool_calls":4,"clarifications_required":0,"duration_estimate":"<1min"},"observations":{"clarification_types":[],"edge_cases_hit":["local branch already deleted"],"errors":[],"warnings":[],"ambiguities":[],"missing_instructions":[],"improvement_suggestions":[]}}
```

After a `/review-pr` with issues:

```json
{"timestamp":"2025-12-08T15:45:00Z","command":{"name":"review-pr","arguments":"112"},"context":{"branch":"main","repo_state":"clean","related_pr":112,"related_issue":"LIR-25"},"outcome":{"status":"partial_success","failure_reason":"security-reviewer agent timed out"},"metrics":{"steps_completed":5,"steps_total":6,"tool_calls":28,"clarifications_required":1,"duration_estimate":"5-15min"},"review_metrics":{"issues_by_severity":{"critical":0,"high":2,"medium":4,"low":3},"actionable_count":4,"deferred_count":2,"duplicate_merges":1,"agents_completed":["code-quality","performance","test-coverage","docs"]},"observations":{"clarification_types":["scope_clarification"],"edge_cases_hit":[],"errors":["Agent security-code-reviewer exceeded timeout"],"warnings":["Large diff (2000+ lines) may have impacted review quality"],"ambiguities":["Unclear whether to review test files"],"missing_instructions":["No guidance on handling agent timeouts"],"improvement_suggestions":["Add timeout handling with retry logic","Specify test file review policy"]}}
```

After a `/fix-review`:

```json
{"timestamp":"2025-12-08T16:30:00Z","command":{"name":"fix-review","arguments":"112"},"context":{"branch":"feature/lir-25","repo_state":"clean","related_pr":112,"related_issue":"LIR-25"},"outcome":{"status":"success","failure_reason":null},"metrics":{"steps_completed":8,"steps_total":8,"tool_calls":45,"clarifications_required":2,"duration_estimate":"5-15min"},"fix_metrics":{"issues_fixed":4,"issues_deferred":2,"deferred_decisions":{"fix_now":1,"create_issue":0,"skip":1},"new_issues_created":[],"used_consolidated_review":true},"observations":{"clarification_types":["deferred_item_handling"],"edge_cases_hit":[],"errors":[],"warnings":[],"ambiguities":[],"missing_instructions":[],"improvement_suggestions":[]}}
```

## Critical Reminders

- **Always log** - Even failures and aborts produce valuable data
- **Be honest** - Observations drive real improvements; don't minimize issues
- **Single line** - Keep JSON on one line (JSONL format)
- **Escape carefully** - Use proper JSON escaping for quotes and special characters in strings
- **Don't skip** - Logging is mandatory for all command executions
