---
description: Evaluate code changes with 4 independent AI judges. Usage: /vote [branch|commit|file|staged]
---

# 🎭 Code Jury

Evaluate the following code changes with 4 independent AI judges:

```bash
!{python3 .qwen/skills/vote/select_judges.py --lang uk}
```

Get the git diff based on the user's request and evaluate it using the 4 jury-judge sub-agents from `.qwen/agents/jury-judge.md`.

Each judge should:
1. Receive their personality JSON config
2. Evaluate the code diff independently
3. Return their verdict with score, likes, dislikes, and advice

Then aggregate all 4 results into a final verdict with weighted voting.
