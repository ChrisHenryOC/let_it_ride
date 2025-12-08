---
description: Analyze command metrics and propose improvements
---

Analyze collected command metrics and generate an effectiveness report.

## Step 1: Load Metrics Data

Read the metrics log:
```bash
cat .claude/metrics/command_log.jsonl 2>/dev/null || echo "NO_METRICS_FILE"
```

If the file does not exist or is empty, report:
> No metrics have been collected yet. Run some commands (e.g., `/review-pr`, `/issue`, `/merge-pr`) and they will automatically log metrics.

Then exit.

## Step 2: Parse and Calculate Statistics

For each command type found in the log, calculate:

### Execution Metrics
- Total executions
- Success rate: `success / total`
- Partial success rate: `partial_success / total`
- Failure rate: `failure / total`
- Abort rate: `aborted / total`
- Average steps completed vs total
- Average tool calls per execution
- Duration distribution by bracket

### Clarification Analysis
- Total clarifications required across all executions
- Clarification rate: `clarifications / executions`
- Most common clarification types (ranked by frequency)

## Step 3: Identify Patterns

Analyze the `observations` fields across all entries:

### Recurring Issues (High Priority)
- Errors that appear in multiple executions
- Warnings that repeat across runs
- Edge cases hit frequently (3+ occurrences)

### Prompt Improvement Signals
- Ambiguities mentioned more than once → unclear instructions
- Missing instructions cited repeatedly → gaps in command docs
- Improvement suggestions that recur → validated enhancement ideas

### Command-Specific Insights
- Which commands have lowest success rates?
- Which commands require most user clarifications?
- Which commands take longest (by duration bracket)?
- Which commands have highest tool call counts?

## Step 4: Generate Report

Create a report at `.claude/metrics/analysis_reports/`:
```bash
mkdir -p .claude/metrics/analysis_reports
```

File name: `{YYYY-MM-DD}_analysis.md`

### Report Structure

```markdown
# Command Metrics Analysis Report

**Generated:** {timestamp}
**Period:** {earliest_entry_date} to {latest_entry_date}
**Total Executions:** {count}

## Executive Summary

[2-3 sentences highlighting the most important findings]

## Command Performance

### /review-pr
- Executions: X
- Success Rate: X%
- Avg Tool Calls: X
- Avg Duration: X
- Clarification Rate: X%

[Repeat for each command type found]

## Recurring Patterns

### Most Common Clarification Types
| Rank | Type | Count | % of Clarifications |
|------|------|-------|---------------------|
| 1 | {type} | {n} | {pct}% |

### Frequently Hit Edge Cases
| Count | Edge Case | Command(s) |
|-------|-----------|------------|
| {n} | {description} | {commands} |

### Repeated Errors
| Count | Error | Command(s) |
|-------|-------|------------|
| {n} | {error} | {commands} |

### Repeated Warnings
| Count | Warning | Command(s) |
|-------|---------|------------|
| {n} | {warning} | {commands} |

## Improvement Recommendations

### High Priority (Recurring Issues)

For each recommendation:
1. **{Command}**: {Specific recommendation}
   - Evidence: {X occurrences of Y}
   - Impact: {What improves if fixed}

### Medium Priority (Optimization)
[List recommendations with evidence]

### Low Priority (Enhancement)
[List suggestions from improvement_suggestions field]

## Proposed Edits

For each high-priority recommendation where a specific edit can be proposed:

### Proposal {N}: {Title}

**File:** `.claude/commands/{command}.md`
**Section:** {Section name or line range}

**Problem:** {What the data shows}

**Current text:**
```
[existing text from command file]
```

**Proposed text:**
```
[improved text]
```

**Rationale:** {Why this change addresses the identified pattern}
```

## Step 5: Present Findings

Display the full report to the console.

If there are high-priority recommendations with proposed edits, use AskUserQuestion:

**Question:** "Would you like me to apply the proposed command improvements?"

**Options:**
- A) Apply all high-priority edits
- B) Review each edit individually
- C) Save report only, no edits

## Step 6: Apply Edits (if requested)

### If user selects A (Apply all):
1. For each proposed edit, modify the target command file
2. Commit all changes together

### If user selects B (Review individually):
1. For each proposed edit, show the before/after and ask:
   - "Apply this edit to {file}?" [Yes / No / Modify]
2. Apply approved edits
3. Commit approved changes

### Commit format:
```bash
git add .claude/commands/ .claude/metrics/analysis_reports/
git commit -m "refactor: Improve command files based on metrics analysis

Applied recommendations from metrics analysis.
Analysis period: {start} to {end} ({N} executions)

Changes:
- {list of applied changes}

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

## Step 7: Archive Metrics (Optional)

After generating the report, use AskUserQuestion:

**Question:** "Archive processed metrics to start fresh data collection?"

**Options:**
- Yes - Move log to archive, start fresh
- No - Keep accumulating data

### If Yes:
```bash
mkdir -p .claude/metrics/archive
mv .claude/metrics/command_log.jsonl .claude/metrics/archive/command_log_$(date +%Y-%m-%d).jsonl
```

---

## METRICS LOGGING (Required)

Before presenting the final outcome, log metrics per `.claude/memories/metrics-logging-protocol.md`:

1. Ensure `.claude/metrics/` directory exists
2. Construct the metrics JSON reflecting this execution (command name: "analyze-metrics", steps_total: 7)
3. Append to `.claude/metrics/command_log.jsonl`

Pay special attention to the `observations` fields - these drive continuous improvement.
