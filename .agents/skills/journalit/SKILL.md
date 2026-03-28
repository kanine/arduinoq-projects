---
name: journalit
description: Create a developer journal entry summarising all git commits since the last journal file. Use when the user asks to write a journal entry, log today's commits, update the dev journal, or says "journalit".
allowed-tools: Bash, Read, Edit, Glob
---
 
Create a journal entry in `docs/developer/daily/` summarising all commits since the last journal file.
 
1. List all files in `docs/developer/daily/` matching `journal-*.md` and identify the most recent one by filename date. Note that date as the "since" date. If the directory doesn't exist, create it with `mkdir -p docs/developer/daily/`.
2. Run `git log --oneline --after="<since date> 23:59:59"` to get all commits made after that date up to now. If no journal files exist, use all commits on today's date.
3. For each commit hash, run `git show --stat --format="%s%n%n%b" <hash>` to get the subject, body, and changed files.
4. Determine today's date and the timestamp of the first and last commit in the range. If there are no commits in the range, report that and stop.
5. Create `docs/developer/daily/journal-<today>.md` with:
   - A heading: `# Journal — <today>`
   - A blockquote: `> Summarises commits from <first commit datetime> to <last commit datetime> / N commits`
   - Commits grouped by theme (plugin work, tooling, documentation, bug fixes, etc.) — not listed one-by-one but summarised meaningfully per group
   - Each group has a heading, the relevant commit hashes in parentheses, and 3–6 bullet points explaining what was done and why
6. After writing the file, stage and commit it with message: `add journal entry for <today>`
7. Push to origin/main and confirm the commit hash.
8. Check the current local time. If it is 21:00 or later, invoke the backup-db skill to run a database backup after the journal is committed.