# GitHub PR Review API Syntax

## Posting a review with inline comments

Use JSON input via heredoc to properly pass the comments array:

```bash
cat <<'JSONEOF' | gh api repos/OWNER/REPO/pulls/PR_NUMBER/reviews --method POST --input -
{
  "event": "COMMENT",
  "comments": [
    {
      "path": "path/to/file.py",
      "line": 71,
      "body": "Your comment here with **markdown** support"
    },
    {
      "path": "path/to/another/file.py",
      "line": 42,
      "body": "Another comment"
    }
  ]
}
JSONEOF
```

## Event types
- `COMMENT` - Just leave comments without approval/rejection
- `APPROVE` - Approve the PR
- `REQUEST_CHANGES` - Request changes

## Top-level comment only (no inline)

```bash
gh pr review PR_NUMBER --comment --body "Your review summary here"
```

## Replying to existing PR comments

Use JSON input with `in_reply_to` field containing the comment ID:

```bash
cat <<'JSONEOF' | gh api repos/OWNER/REPO/pulls/PR_NUMBER/comments --method POST --input -
{
  "body": "Your reply here with **markdown** support",
  "in_reply_to": 2573671317
}
JSONEOF
```

To find comment IDs, fetch existing comments:
```bash
gh api repos/OWNER/REPO/pulls/PR_NUMBER/comments
```

Look for the `id` field in each comment object, and `in_reply_to_id` to see thread structure.

## Key notes
- The `comments` field must be a JSON array, not a string
- Use `--input -` to read JSON from stdin
- Use heredoc with `'JSONEOF'` (quoted) to prevent shell expansion
- Line numbers refer to the line in the diff, not the original file
- For replies, use `/pulls/PR_NUMBER/comments` endpoint (not `/reviews`)
- The `in_reply_to` field takes the integer comment ID
