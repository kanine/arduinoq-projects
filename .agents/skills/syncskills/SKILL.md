---
name: syncskills
description: Two-way sync skills between .agents/skills/ and .claude/skills/. Use when the user asks to sync skills, run sync-skills, or update the skills directories.
allowed-tools: Bash
---

Run the two-way skills sync from the project root:

```bash
bash scripts/sync-skills.sh
```

This syncs skills between `.agents/skills/` and `.claude/skills/` in both directions — newest file wins on conflict. Report what was updated based on the script output.
