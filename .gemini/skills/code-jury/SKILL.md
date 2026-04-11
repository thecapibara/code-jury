---
name: code-jury
description: Evaluate code changes with 4 independent AI judges. Each judge has a unique personality, expertise, and weighted vote. Use PROACTIVELY when asked to review, evaluate, or vote on code changes.
---

# 🎭 Code Jury for Gemini

**4 independent AI judges evaluate code changes — like America's Got Talent!**

## How It Works

1. **Choose quality mode** (4 options for Gemini)
2. **Select 4 random judges** from 10 personality types
3. **Spawn 4 sub-agents** (Pro for expert, Flash/Flash-Lite for lightweight)
4. **Each judge evaluates independently**
5. **Aggregate results** with weighted voting + consensus detection

## Step 0: Choose quality mode

Ask the user to pick a review mode, or infer from context:

| Mode | Models | Use case |
|------|--------|----------|
| ⚡ **Lightning** | 4× Flash-Lite | Quick checks, smallest diff |
| 💨 **Flash** | 4× Flash | Fast but capable |
| ⚖️ **Balanced** | 2× Pro + 2× Flash | Default — optimal balance |
| 🔍 **Thorough** | 4× Pro | Important reviews, security |

**Inference:**
- If user said "quick check" or "fast" → default to Lightning
- If user said "deep" or "security" → default to Thorough
- If user said "flash" → use Flash mode (Gemini-only)
- Otherwise → default to Balanced

## Step 1: Get the code diff

**Fallback chain** — try each until one works:

1. **`git diff HEAD`** — unstaged changes
2. **`git diff`** — changes vs index
3. **No `.git` directory** → list recent files, ask user which to review
4. **User requests specific scope** → `git show HEAD`, `git diff main...feature`, etc.

## Step 2: Detect language & select judges

**Detect language** from conversation context (Ukrainian → uk, English → en, etc.)

Run the judge selector:

```bash
python3 .gemini/skills/code-jury/scripts/select_judges.py --platform gemini --lang <lang> --mode <mode>
```

This outputs 4 judge configs with:
- `assigned_name`, `assigned_gender`, localized titles/emojis
- `gemini_model_full` (gemini-3.1-pro or gemini-3.1-flash or gemini-3.1-flash-lite)
- `vote_weight`, `focus`, `review_guide`

## Step 3: Spawn 4 sub-agents in parallel

For each judge, use the appropriate sub-agent:
- `model` = "pro" → use `jury-judge-pro` sub-agent
- `model` = "flash" or "flash-lite" → use `jury-judge-flash` sub-agent

Spawn ALL 4 in parallel. Each gets:
- The judge's personality JSON (with `assigned_name`, `assigned_gender`, localized titles, `focus`)
- The code diff
- Their `review_guide` filename so they can read the detailed checklist

**Gender fields:**
- If `assigned_gender` = "male" → use `emoji_male` + `title_male`
- If `assigned_gender` = "female" → use `emoji_female` + `title_female`

## Step 4: Aggregate results

**Step 4a — Extract issues:**
Parse each judge's "❌ What I disliked" section. Extract the core issue.

**Step 4b — Detect consensus:**
- Group issues by similarity (same file/function/concept)
- 3+ judges → consensus issue (high priority)
- 2 judges → shared issue (medium priority)

**Step 4c — Calculate weighted score:**
- Weighted average: `sum(score_i × vote_weight_i) / sum(vote_weight_i)`
- Consensus penalty: For each issue mentioned by 3+ judges, subtract 0.3 (max -1.0)
- Round to 1 decimal place

**Pass threshold:** weighted "Yes" votes >= 60% of total weight

## Output Format

```
🎭 Code Jury Results
============================================================

{For each judge:}
## {emoji} {assigned_name} — {localized_title}

**Focus:** {focus areas}
**Weight:** {vote_weight}x

### Verdict: {✅ Yes / ❌ No} — Score: {X}/10

#### ✅ What I liked
- [Specific positive observation with line references]

#### ❌ What I disliked
- [Specific negative observation with line references]

#### 💡 Advice
- [Actionable improvement suggestion]

============================================================
📊 Summary: {weighted_yes} ✅ Yes | {weighted_no} ❌ No (weighted: Yes {pct}% / No {pct}%)
🎯 Weighted Score: {score}/10
🔥 Consensus Issues (3+ judges): {list or "none"}

{🎉 PASSED or 😔 FAILED}

💡 Top improvement tips:
  1. {most common issue}
  2. {second most common issue}
  3. {third most common issue}
```

## Judge Types

| Type | Model | Weight | Focus |
|------|-------|--------|-------|
| Strict Critic | Pro | **1.7x** | Architecture, errors, security |
| Supportive Mentor | Flash | 1.0x | Potential, best practices |
| Detail-Oriented | Flash | 1.2x | Style, docs, tests, DRY |
| Creative Engineer | Flash | 1.0x | Creativity, elegance |
| Security Expert | Pro | **2.0x** | Vulnerabilities, validation |
| Performance Optimizer | Pro | **1.5x** | Algorithms, memory, CPU |
| Testing Expert | Pro | **1.6x** | Unit tests, edge cases |
| Architecture Guru | Pro | **1.8x** | SOLID, patterns, modularity |
| UX Advocate | Flash | 1.1x | API design, error messages |
| Maintenance Focus | Flash | 1.2x | Readability, tech debt |
