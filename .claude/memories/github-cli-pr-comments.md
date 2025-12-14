# GitHub CLI: PR Inline Comments

## Posting Inline Comments

Use `position` (integer) not `line` or `subject_type`. Position is the line number **within the diff hunk**, not the file line number.

**Calculate position:**
1. `gh pr diff PR_NUMBER > /tmp/pr.diff`
2. Find `@@` hunk header line number for target file
3. `position = target_line_in_diff - hunk_header_line`

**Example:** `@@` at line 182, target at line 223 → position = `223 - 181 = 42` (the @@ line is position 1)

```bash
# Find position
gh pr diff PR_NUMBER > /tmp/pr.diff
cat -n /tmp/pr.diff | grep -A 5 "code to comment on"

# Post comment (use -F for integer)
gh api repos/OWNER/REPO/pulls/PR_NUMBER/comments \
  --method POST \
  -f body="Comment" \
  -f path="path/to/file.py" \
  -f commit_id="$(gh pr view PR_NUMBER --json headRefOid -q .headRefOid)" \
  -F position=42
```

## Responding to PR Comments

```bash
# Find comment ID
gh api repos/OWNER/REPO/pulls/PR_NUMBER/comments --jq '.[] | {id, body: .body[:50]}'

# Reply
gh api repos/OWNER/REPO/pulls/PR_NUMBER/comments/COMMENT_ID/replies \
  --method POST \
  -f body="Done. Updated X to do Y."
```
