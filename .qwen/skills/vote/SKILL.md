---
name: vote
description: Evaluate code changes with 4 independent AI judges (like America's Got Talent). Each judge has a unique personality and expertise. Use PROACTIVELY when asked to review, evaluate, or vote on code changes, commits, or branches.
---

# 🎭 Code Jury

**4 independent AI judges evaluate code changes — like America's Got Talent!**

## How It Works

1. **Select 4 random judges** from 10 personality types
2. **Assign names** from the detected language
3. **Spawn 4 sub-agents** in parallel with their personality + name
4. **Aggregate results** with weighted voting + common issue bonus

## Step-by-Step

### Step 1: Detect language from user's message

Look at the user's language and map to code:
- Ukrainian → `uk`
- English → `en`
- Russian → `ru`
- Arabic → `ar`
- Polish → `pl`
- Spanish → `es`
- German → `de`
- French → `fr`
- Italian → `it`

### Step 2: Get the code diff

Run appropriate git command based on user request.

### Step 3: Select judges and assign names

Run:
```bash
python3 .qwen/skills/vote/select_judges.py --lang <code>
```

This outputs 4 judge configs. Each judge has:
- `assigned_name` — localized name (e.g., "Оксана", "Alex")
- `assigned_gender` — "male" or "female"
- `personality.type` — strict, supportive, etc.
- `personality.title_male` / `title_female` — personality title
- `personality.emoji_male` / `personality.emoji_female` — emoji
- `personality.score_range` — [min, max]
- `personality.focus` — expertise areas
- `personality.vote_weight` — weight (e.g., 1.5)
- `model` — "haiku" or "sonnet" (for Claude) or "inherit" (for Qwen)

### Step 4: Spawn 4 sub-agents

For each judge, spawn the appropriate sub-agent:
- **Claude:** `jury-judge-haiku` if model=haiku, `jury-judge-sonnet` if model=sonnet
- **Qwen:** `jury-judge` (inherits model)

Pass to each sub-agent:
```
You are {assigned_name}. Your personality: {personality.description}
Your role: {personality.title_female or title_female based on gender}
Focus on: {personality.focus}
Score range: {personality.score_range}
Vote weight: {personality.vote_weight}x

Evaluate this code diff:
{diff}
```

Spawn ALL 4 in parallel. They work independently.

### Step 5: Aggregate results

Collect all 4 verdicts and compute:

**1. Weighted score:** `sum(score * vote_weight) / sum(vote_weight)`

**2. Common issue bonus:** If 3+ judges mention the same issue → add -0.5 to score (penalty)

**3. Pass threshold:** weighted "Yes" votes >= 60% of total weight

**4. Find top issues** — issues mentioned by multiple judges get priority

**Format the output:**

```
🎭 Code Jury Results
============================================================

{For each judge:}
{emoji} {assigned_name} ({personality_title}) (weight: {vote_weight}x)
  ✅ {likes}
  ❌ {dislikes}
  📊 {score}/10 | {verdict}

============================================================
📊 Summary: {weighted_yes} ✅ Yes | {weighted_no} ❌ No (weighted)
🎯 Weighted Score: {avg}/10
⚠️ Common issues (mentioned by 3+ judges):
  • {most common issue}

{🎉 PASSED or 😔 FAILED message}

💡 Top improvement tips:
  • {most common issue} (mentioned by X judges)
  • {second most common issue} (mentioned by Y judges)
```

## Judge Types & Models

| Personality | Weight | Model | Focus |
|-------------|--------|-------|-------|
| Strict Critic | 1.5x | sonnet | Architecture, errors, security |
| Supportive Mentor | 1.0x | haiku | Potential, best practices |
| Detail-Oriented | 1.2x | haiku | Style, docs, tests, DRY |
| Creative Engineer | 1.0x | haiku | Creativity, performance |
| Security Expert | 1.8x | sonnet | Vulnerabilities, validation |
| Performance Optimizer | 1.3x | sonnet | Algorithms, memory, CPU |
| Testing Expert | 1.4x | sonnet | Unit tests, edge cases |
| Architecture Guru | 1.6x | sonnet | SOLID, patterns, modularity |
| UX Advocate | 1.1x | haiku | API design, UX |
| Maintenance Focus | 1.2x | haiku | Readability, tech debt |

## Quality Modes

The user can specify a quality mode:

| Mode | Models | Cost | Use when |
|------|--------|------|----------|
| **Economy** 💰 | 4× Haiku | ~$0.01 | Quick checks, drafts |
| **Standard** ⚖️ | 2× Sonnet + 2× Haiku | ~$0.03 | Default, balanced |
| **Premium** 🏆 | 4× Sonnet | ~$0.05 | Final reviews, important changes |

If no mode specified, use **Standard**.

To override: filter judges by model after selection:
- Economy: force all to haiku
- Premium: force all to sonnet
- Standard: keep original model assignments

## Language Support

Names are localized via `scripts/judge_profiles/<lang>.json`:
- Each file has `name_pool` with 20-30 names + gender
- Each file has `personalities` with localized titles

## Files

- `select_judges.py` — selects 4 random judges with names
- `.qwen/agents/jury-judge.md` — Qwen sub-agent
- `.claude/agents/jury-judge-haiku.md` — Claude lightweight judge
- `.claude/agents/jury-judge-sonnet.md` — Claude expert judge
- `scripts/judge_profiles/*.json` — name pools per language
- `judges.json` — 10 personality types with model + weight
