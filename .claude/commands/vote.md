---
name: vote
description: Evaluate code changes with 4 independent AI judges (like America's Got Talent)
---

# 🎭 Vote — Code Review Jury

Run the vote skill to evaluate code changes:

```bash
python3 .claude/skills/vote/scripts/vote.py
```

## Options

If the user specifies something specific, add arguments:

| Request | Command |
|---------|---------|
| Unstaged changes | `python3 .claude/skills/vote/scripts/vote.py` |
| Last commit | `python3 .claude/skills/vote/scripts/vote.py --commit HEAD` |
| Last N commits | `python3 .claude/skills/vote/scripts/vote.py --last 3` |
| Branch changes | `python3 .claude/skills/vote/scripts/vote.py --branch feature-name` |
| Specific file | `python3 .claude/skills/vote/scripts/vote.py --file path/to/file.py` |
| Staged changes | `python3 .claude/skills/vote/scripts/vote.py --staged` |
| View history | `python3 .claude/skills/vote/scripts/vote.py --history` |
| View session | `python3 .claude/skills/vote/scripts/vote.py --session <id>` |

## How it works

1. 4 judges are randomly selected from 10 personality types
2. Each judge evaluates the code independently
3. Results include: score (1-10), ✅/❌ verdict, likes, dislikes
4. Branch history shows progress across multiple attempts

## Judges

| Personality | Emoji | Weight | Focus |
|-------------|-------|--------|-------|
| Strict Critic | 👩‍⚖️ | 1.5x | Architecture, errors, security |
| Supportive Mentor | 👨‍🏫 | 1.0x | Potential, best practices |
| Detail-Oriented | 🔍 | 1.2x | Style, docs, tests |
| Creative Engineer | 🎨 | 1.0x | Creativity, performance |
| Security Expert | 🛡️ | 1.8x | Vulnerabilities, validation |
| Performance Optimizer | ⚡ | 1.3x | Algorithms, memory |
| Testing Expert | 🧪 | 1.4x | Unit tests, edge cases |
| Architecture Guru | 🏛️ | 1.6x | SOLID, patterns |
| User Advocate | 👤 | 1.1x | API design, UX |
| Maintenance Focus | 🔧 | 1.2x | Readability, tech debt |

## Language Support

Judges adapt to the user's language: Ukrainian, English, Arabic, Russian, Polish, Spanish, German, French, Italian.
