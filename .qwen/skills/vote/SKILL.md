---
name: code-jury
description: Evaluate code changes with 4 independent AI judges (like America's Got Talent). Each judge has a unique personality and expertise. Use PROACTIVELY when asked to review, evaluate, or vote on code changes, commits, or branches.
---

# 🎭 Code Jury

**4 independent AI judges evaluate code changes — like America's Got Talent!**

## How It Works

1. **Select 4 random judges** from 10 personality types using the judge selector
2. **Spawn 4 sub-agents** in parallel, each with their personality JSON
3. **Each judge evaluates independently** using their own model (haiku/sonnet/inherit)
4. **Aggregate results** into a unified verdict with weighted voting

## Step-by-Step

### Step 1: Get the code diff

Run `git diff HEAD` for unstaged changes, or use the appropriate git command based on what the user asked.

### Step 2: Select judges

Run the judge selector to get 4 random judges with localized names:

```bash
python3 .qwen/skills/vote/select_judges.py --lang <detected_lang>
```

This outputs 4 judge configs with `assigned_name`, `assigned_gender`, and `model`.

### Step 3: Spawn 4 sub-agents

For EACH judge, delegate to the `jury-judge` sub-agent with:
- The judge's personality JSON (including assigned name, gender, score_range, focus, vote_weight)
- The code diff to evaluate

Example delegation:
```
Use the jury-judge sub-agent with this personality config:
{JSON here}

And evaluate this code diff:
{diff here}
```

### Step 4: Aggregate results

Collect all 4 verdicts and compute:

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
  📊 {score}/10 | {verdict}

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
| Strict Critic | 1.5x | inherit | Architecture, errors, security |
| Supportive Mentor | 1.0x | inherit | Potential, best practices |
| Detail-Oriented | 1.2x | inherit | Style, docs, tests, DRY |
| Creative Engineer | 1.0x | inherit | Creativity, performance |
| Security Expert | 1.8x | inherit | Vulnerabilities, validation |
| Performance Optimizer | 1.3x | inherit | Algorithms, memory, CPU |
| Testing Expert | 1.4x | inherit | Unit tests, edge cases |
| Architecture Guru | 1.6x | inherit | SOLID, patterns, modularity |
| UX Advocate | 1.1x | inherit | API design, UX, error messages |
| Maintenance Focus | 1.2x | inherit | Readability, tech debt |

## Language Support

Names are localized. Use `--lang` flag with the selector:
- `uk` — Ukrainian names
- `en` — English names
- `ar` — Arabic names
- `ru` — Russian names
- `pl` — Polish names
- `es` — Spanish names
- `de` — German names
- `fr` — French names
- `it` — Italian names

## Files

- `select_judges.py` — selects 4 random judges with names
- `.qwen/agents/jury-judge.md` — sub-agent that evaluates code
- `scripts/judge_profiles/*.json` — name pools per language
