---
name: code-jury
description: Evaluate code changes with 4 independent AI judges (like America's Got Talent). Each judge has a unique personality and expertise. Use PROACTIVELY when asked to review, evaluate, or vote on code.
---

# 🎭 Code Jury

**4 independent AI judges evaluate code changes — like America's Got Talent!**

## How It Works

1. **Ask for quality mode** (interactive menu)
2. **Select 4 random judges** from 10 personality types
3. **Spawn 4 sub-agents** (haiku for lightweight, sonnet for heavyweight)
4. **Each judge evaluates independently**
5. **Aggregate results** with weighted voting + consensus detection

## Step-by-Step

### Step 0: Choose quality mode

Ask the user to pick a review mode:

**Mode options:**
- ⚡ **Lightning** — 4× Haiku (швидко, дешево, для дрібних змін)
- ⚖️ **Balanced** — 2× Sonnet + 2× Haiku (за замовчуванням, оптимальний баланс)
- 🔍 **Thorough** — 4× Sonnet (ретельно, для важливих ревью)

If user just said "quick check" or similar → default to Lightning.
If user said "thorough review" or "security check" → default to Thorough.
Otherwise → ask using the menu above, default to Balanced.

### Step 1: Get the code diff

**Fallback chain** — try each until one works:

1. **`git diff HEAD`** — unstaged changes in a project with commits
2. **`git diff`** — changes vs index (project with no commits yet)
3. **No `.git` directory** — project is not tracked by git:
   - List recently modified files: `ls -la --sort=time | head -20`
   - Ask user: *"This is not a git project. Which files should I review?"*
   - Use `git diff --no-index /dev/null <file>` or just read the files directly

Handle user requests:
- Unstaged: `git diff HEAD`
- Last commit: `git show HEAD`
- Branch: `git diff main...feature`
- Specific file: `git diff HEAD -- <file>`

### Step 2: Detect language & select judges

**Detect language from user's conversation context:**
- Ukrainian → `--lang uk`
- Russian → `--lang ru`
- Polish → `--lang pl`
- English → `--lang en`
- Spanish → `--lang es`
- German → `--lang de`
- French → `--lang fr`
- Italian → `--lang it`
- Arabic → `--lang ar`
- Default (if unsure) → `--lang en`

Run the judge selector with the **chosen mode** from Step 0:

```bash
python3 .claude/skills/vote/scripts/select_judges.py --lang <detected_lang> --mode <chosen_mode>
```

This outputs 4 judge configs with assigned names, localized titles, and `model` field (haiku or sonnet).

### Step 3: Spawn 4 sub-agents in parallel

For each judge, use the appropriate sub-agent based on `model` field:
- `model: haiku` → use `jury-judge-haiku` sub-agent
- `model: sonnet` → use `jury-judge-sonnet` sub-agent

Spawn ALL 4 in parallel. Each gets:
- The judge's personality JSON (with `assigned_name`, `assigned_gender`, localized `title_male`/`title_female`, `emoji_male`/`emoji_female`, `focus`)
- The code diff

**Important:** Use the **gender-appropriate** fields based on `assigned_gender`:
- If `assigned_gender` = "male" → use `emoji_male` + `title_male`
- If `assigned_gender` = "female" → use `emoji_female` + `title_female`

Example:
```
Use the jury-judge-sonnet sub-agent with this personality config:
{"name": "Architecture Guru", "assigned_name": "Василь", "assigned_gender": "male", "type": "architecture_guru", "emoji_male": "🏛️", "title_male": "Архітектор-гуру", "vote_weight": 1.8, ...}

Evaluate this code diff:
{diff here}
```

### Step 4: Aggregate results

**Step 4a — Extract issues from each judge:**
Parse each judge's "❌ What I disliked" section. Extract the core issue (the file/function/concept, not the full sentence).

**Step 4b — Detect consensus:**
- Group issues by similarity (same file, same function, same concept)
- Count how many judges mentioned each issue
- **3+ judges** → **consensus issue** (high priority)
- **2 judges** → **shared issue** (medium priority)

**Step 4c — Calculate weighted score:**
- Weighted average: `sum(score_i × vote_weight_i) / sum(vote_weight_i)`
- **Consensus penalty**: For each issue mentioned by 3+ judges, subtract `0.3` from the final score (max `-1.0`)
- Round to 1 decimal place

**Pass threshold:** weighted "Yes" votes >= 60% of total weight

**Format the output:**

```
🎭 Code Jury Results
============================================================

{For each judge — full output from sub-agent:}
## {emoji} {assigned_name} — {localized_title}

**Focus:** {comma-separated focus areas}
**Weight:** {vote_weight}x

### Verdict: {✅ Yes / ❌ No} — Score: {X}/10

#### ✅ What I liked
- [Specific positive observation with line references]
- [Another positive observation]

#### ❌ What I disliked
- [Specific negative observation with line references]
- [Another negative observation]

#### 💡 Advice
- [Actionable improvement suggestion]
- [Another actionable suggestion]

============================================================
📊 Summary: {weighted_yes} ✅ Yes | {weighted_no} ❌ No (зважені: Yes {pct}% / No {pct}%)
🎯 Weighted Score: {score}/10
🔥 Consensus Issues (3+ judges): {list or "none"}

{🎉 PASSED (поріг 60% зважених Yes) or 😔 FAILED message}

💡 Top improvement tips:
  1. {most common issue — mentioned by N/4 judges}
  2. {second most common issue — mentioned by N/4 judges}
  3. {third most common issue — mentioned by N/4 judges}
```

## Judge Types & Models

| Personality | Weight | Default Model | Focus |
|-------------|--------|---------------|-------|
| Strict Critic | **1.7x** | Sonnet | Architecture, errors, security |
| Supportive Mentor | 1.0x | Haiku | Potential, best practices |
| Detail-Oriented | 1.2x | Haiku | Style, docs, tests, DRY |
| Creative Engineer | 1.0x | Haiku | Creativity, performance |
| Security Expert | **2.0x** | Sonnet | Vulnerabilities, validation |
| Performance Optimizer | **1.5x** | Sonnet | Algorithms, memory, CPU |
| Testing Expert | **1.6x** | Sonnet | Unit tests, edge cases |
| Architecture Guru | **1.8x** | Sonnet | SOLID, patterns, modularity |
| UX Advocate | 1.1x | Haiku | API design, UX |
| Maintenance Focus | 1.2x | Haiku | Readability, tech debt |

## Files

- `.claude/agents/jury-judge-haiku.md` — lightweight sub-agent
- `.claude/agents/jury-judge-sonnet.md` — expert sub-agent
- `select_judges.py` — selects 4 random judges with localization
- `.claude/skills/vote/scripts/judge_profiles/` — localized names & personalities (9 languages)
- `judges.json` — source of truth for judge weights & default models
