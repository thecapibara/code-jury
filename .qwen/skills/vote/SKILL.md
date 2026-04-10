---
name: vote
description: Evaluate code changes with 4 independent AI judges (like America's Got Talent). Each judge has a unique personality and expertise. Use PROACTIVELY when asked to review, evaluate, or vote on code changes, commits, or branches.
---

# 🎭 Code Jury

**4 independent AI judges evaluate code changes — like America's Got Talent!**

## How It Works

1. **Ask for quality mode** (interactive menu or parse `--mode` flag)
2. **Select 4 random judges** from 10 personality types with localized names
3. **Spawn 4 sub-agents** in parallel with personality + name
4. **Aggregate results** with weighted voting + consensus detection

## Step-by-Step

### Step 0: Choose quality mode

Check for `--mode` flag in user's request:
- `--mode lightning` — 4× Haiku (швидко, дешево, для дрібних змін)
- `--mode thorough` — 4× Sonnet (ретельно, для важливих ревью)
- No flag → **balanced** (2× Sonnet + 2× Haiku, default)

### Step 1: Get the code diff

**Fallback chain** — try each until one works:
1. `git diff HEAD` — unstaged changes with commits
2. `git diff` — changes vs index (no commits yet)
3. No `.git` → ask user which files to review

### Step 2: Detect language & select judges

Detect language from user's conversation context, then run:
```bash
python3 .qwen/skills/vote/scripts/select_judges.py --lang <code> --mode <mode>
```

### Step 3: Spawn 4 sub-agents

Use `.qwen/agents/jury-judge.md` for ALL 4 judges (model: inherit).
Pass each judge their personality JSON + code diff.

### Step 4: Aggregate results

**Consensus detection:**
- Extract issues from each judge's "❌ What I disliked"
- Issues mentioned by 3+ judges → consensus (high priority)
- Issues mentioned by 2 judges → shared (medium priority)

**Weighted score:**
- `sum(score_i × vote_weight_i) / sum(vote_weight_i)`
- Consensus penalty: `-0.3` per issue with 3+ mentions (max `-1.0`)

**Pass threshold:** weighted "Yes" >= 60% of total weight

## Judge Types

| Personality | Weight | Focus |
|-------------|--------|-------|
| Strict Critic | **1.7x** | Architecture, errors, security |
| Supportive Mentor | 1.0x | Potential, best practices |
| Detail-Oriented | 1.2x | Style, docs, tests, DRY |
| Creative Engineer | 1.0x | Creativity, performance |
| **Security Expert** | **2.0x** | Vulnerabilities, validation |
| **Performance Optimizer** | **1.5x** | Algorithms, memory, CPU |
| **Testing Expert** | **1.6x** | Unit tests, edge cases |
| **Architecture Guru** | **1.8x** | SOLID, patterns, modularity |
| UX Advocate | 1.1x | API design, UX |
| Maintenance Focus | 1.2x | Readability, tech debt |

## Files

- `scripts/select_judges.py` — selects 4 judges with localization
- `scripts/judge_profiles/*.json` — 9 language profiles
- `.qwen/agents/jury-judge.md` — sub-agent for each judge
- `judges.json` — source of truth for weights & models
