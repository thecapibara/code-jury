---
name: code-jury
description: Evaluate code changes with 4 independent AI judges (like America's Got Talent). Each judge has a unique personality and expertise. Use PROACTIVELY when asked to review, evaluate, or vote on code.
---

# 🎭 Code Jury

**4 independent AI judges evaluate code changes — like America's Got Talent!**

## How It Works

1. **Select 4 random judges** from 10 personality types
2. **Spawn 4 sub-agents** (haiku for lightweight, sonnet for heavyweight)
3. **Each judge evaluates independently**
4. **Aggregate results** with weighted voting

## Step-by-Step

### Step 1: Get the code diff

Run appropriate git command based on user request:
- Unstaged: `git diff HEAD`
- Last commit: `git show HEAD`
- Branch: `git diff main...feature`
- etc.

### Step 2: Select judges

Run the judge selector:

```bash
python3 .claude/skills/vote/select_judges.py --lang <lang>
```

This outputs 4 judge configs with assigned names and `model` field (haiku or sonnet).

### Step 3: Spawn 4 sub-agents in parallel

For each judge, use the appropriate sub-agent based on `model` field:
- `model: haiku` → use `jury-judge-haiku` sub-agent
- `model: sonnet` → use `jury-judge-sonnet` sub-agent

Spawn ALL 4 in parallel. Each gets:
- The judge's personality JSON (with assigned name, gender, etc.)
- The code diff

Example:
```
Use the jury-judge-haiku sub-agent with this personality config:
{"name": "Alex", "gender": "male", "type": "supportive", ...}

Evaluate this code diff:
{diff here}
```

### Step 4: Aggregate results

**Weighted score:** `sum(score * vote_weight) / sum(vote_weight)`

**Pass threshold:** weighted "Yes" votes >= 60% of total weight

**Format the output:**

```
🎭 Code Jury Results
============================================================

{For each judge:}
{emoji} {name} ({personality_title}) (weight: {vote_weight}x)
  ✅ {likes}
  ❌ {dislikes}
  📊 {score}/10 | {✅ Yes / ❌ No}

============================================================
📊 Summary: {weighted_yes} ✅ Yes | {weighted_no} ❌ No (weighted)
🎯 Average Score: {avg}/10

{🎉 Passed or 😔 Failed message}

💡 Top improvement tips:
  • {most common issue}
  • {second most common issue}
```

## Judge Types & Models

| Personality | Weight | Model | Focus |
|-------------|--------|-------|-------|
| Strict Critic | 1.5x | **Sonnet** | Architecture, errors, security |
| Supportive Mentor | 1.0x | Haiku | Potential, best practices |
| Detail-Oriented | 1.2x | Haiku | Style, docs, tests, DRY |
| Creative Engineer | 1.0x | Haiku | Creativity, performance |
| Security Expert | 1.8x | **Sonnet** | Vulnerabilities, validation |
| Performance Optimizer | 1.3x | **Sonnet** | Algorithms, memory, CPU |
| Testing Expert | 1.4x | **Sonnet** | Unit tests, edge cases |
| Architecture Guru | 1.6x | **Sonnet** | SOLID, patterns, modularity |
| UX Advocate | 1.1x | Haiku | API design, UX |
| Maintenance Focus | 1.2x | Haiku | Readability, tech debt |

## Files

- `.claude/agents/jury-judge-haiku.md` — lightweight sub-agent
- `.claude/agents/jury-judge-sonnet.md` — expert sub-agent
- `select_judges.py` — selects 4 random judges
- `scripts/judge_profiles/*.json` — name pools per language
