---
description: Evaluate code changes with 4 independent AI judges. Usage: /vote [--mode lightning|balanced|thorough] [branch|commit|file|staged]
---

# 🎭 Code Jury

## Step 0: Choose quality mode

Parse the user's message for `--mode` flag:
- `--mode lightning` — 4× Haiku (cheap & fast, for quick checks)
- `--mode thorough` — 4× Sonnet (best quality, for important reviews)
- No flag → **balanced** (2× Sonnet + 2× Haiku, default)

If context suggests quick review → default to Lightning.
If context suggests deep review → default to Thorough.
Otherwise → use Balanced.

## Step 1: Get the code diff

**Fallback chain** — try each until one works:

1. **`git diff HEAD`** — unstaged changes in a project with commits
2. **`git diff`** — changes vs index (project with no commits yet)
3. **No `.git` directory** — project is not tracked by git:
   - List recently modified files: `ls -la --sort=time | head -20`
   - Ask user: *"This is not a git project. Which files should I review?"*
   - Read the files directly with `read_file`

Handle user requests:
- Unstaged: `git diff HEAD`
- Last commit: `git show HEAD`
- Last N commits: `git show HEAD~N..HEAD`
- Branch: `git diff main...feature`
- Specific file: `git diff HEAD -- <file>`
- Staged: `git diff --staged`

## Step 2: Detect language & select judges

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

Run the judge selector:

```bash
!{python3 .qwen/skills/vote/scripts/select_judges.py --lang <detected_lang> --mode <chosen_mode>}
```

This outputs 4 judge configs with assigned names, localized titles, and `model` field.

## Step 3: Spawn 4 sub-agents in parallel

Spawn ALL 4 `jury-judge` sub-agents in parallel. Each gets:
- The judge's personality JSON (with `assigned_name`, `assigned_gender`, localized `title_male`/`title_female`, `emoji_male`/`emoji_female`, `focus`)
- The code diff

**Important:** Pass gender-appropriate fields:
- If `assigned_gender` = "male" → use `emoji_male` + `title_male`
- If `assigned_gender` = "female" → use `emoji_female` + `title_female`

## Step 4: Aggregate results

**Step 4a — Extract issues:**
Parse each judge's "❌ What I disliked" section. Extract the core issue (file/function/concept).

**Step 4b — Detect consensus:**
- Group issues by similarity (same file, same function, same concept)
- Count how many judges mentioned each issue
- **3+ judges** → consensus issue (high priority)
- **2 judges** → shared issue (medium priority)

**Step 4c — Calculate weighted score:**
- Weighted average: `sum(score_i × vote_weight_i) / sum(vote_weight_i)`
- **Consensus penalty**: For each issue mentioned by 3+ judges, subtract `0.3` from final score (max `-1.0`)
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
