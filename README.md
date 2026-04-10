# Code Jury [Vote]

**4 independent AI judges evaluate your code — like America's Got Talent!**

Works with Qwen Code, Claude Code, and any other AI coding assistant that supports custom commands/skills.

## ✨ Features

- 🎭 **4 Dynamic Judges** — randomly selected from 10 personality types each time
- 🌍 **9 Languages** — Ukrainian, English, Arabic, Russian, Polish, Spanish, German, French, Italian
- ⚖️ **Weighted Voting** — experts in security, architecture, testing carry more weight
- 📊 **Score & Verdict** — 1-10 scale with ✅/❌ verdict per judge
- 🔄 **Branch Tracking** — tracks progress across multiple attempts on the same branch
- 💾 **Session Caching** — remembers previous votes for the same diff
- 📈 **Issue Persistence** — shows what got fixed, what's still broken, what's new

## 🚀 Quick Install

### One-line Installer (Recommended)

```bash
# Install for both Qwen & Claude
curl -fsSL https://raw.githubusercontent.com/thecapibara/vote-skill/main/install.sh | bash -s -- --remote

# Qwen Code only
curl -fsSL https://raw.githubusercontent.com/thecapibara/vote-skill/main/install.sh | bash -s -- --remote --qwen

# Claude Code only
curl -fsSL https://raw.githubusercontent.com/thecapibara/vote-skill/main/install.sh | bash -s -- --remote --claude

# Global installation
curl -fsSL https://raw.githubusercontent.com/thecapibara/vote-skill/main/install.sh | bash -s -- --remote --all --global
```

### Clone & Install (Offline)

```bash
git clone https://github.com/thecapibara/vote-skill.git
cd vote-skill

# Both (default)
bash install.sh

# Qwen only
bash install.sh --qwen

# Claude only
bash install.sh --claude

# Global
bash install.sh --all --global

# Remote (download from GitHub)
bash install.sh --remote
```

### Verify Installation

```bash
cd ~/.qwen/skills/vote  # or your project's .qwen/skills/vote
python3 scripts/select_judges.py --help
```

## 🎯 Usage

### Qwen Code

Use the slash command:

```
/vote                     # Evaluate unstaged changes
/vote --mode lightning    # Quick check (fast, cheap)
/vote --mode thorough     # Deep review (slow, thorough)
/vote last commit         # Last commit
/vote last 3 commits      # Last 3 commits
/vote branch feature-auth # Branch changes
```

Or just ask naturally:
- *"Evaluate my changes"*
- *"Check the last commit"*
- *"Vote on my feature branch"*

### Claude Code

Use the slash command:

```
/vote                     # Evaluate unstaged changes
/vote --mode lightning    # Quick check (fast, cheap)
/vote --mode thorough     # Deep review (slow, thorough)
/vote last commit         # Last commit
/vote last 3 commits      # Last 3 commits
/vote branch feature-auth # Branch changes
/vote file script.py      # Specific file
/vote history             # View history
```

Or directly run the selector script:
```bash
python3 .claude/skills/vote/scripts/select_judges.py --help
```

## 👥 The Judges

Each vote uses **4 judges** randomly selected from **10 personality types**:

| Personality | Emoji | Weight | Default Model | Expertise |
|-------------|-------|--------|---------------|-----------|
| Strict Critic | 👩‍⚖️ | **1.7x** | Sonnet | Architecture, errors, security |
| Supportive Mentor | 👨‍🏫 | 1.0x | Haiku | Potential, best practices, learning |
| Detail-Oriented Reviewer | 🔍 | 1.2x | Haiku | Style, docs, tests, DRY |
| Creative Engineer | 🎨 | 1.0x | Haiku | Creativity, performance, elegance |
| **Security Expert** | 🛡️ | **2.0x** | Sonnet | Vulnerabilities, validation, encryption |
| **Performance Optimizer** | ⚡ | **1.5x** | Sonnet | Algorithms, memory, CPU, scalability |
| **Testing Expert** | 🧪 | **1.6x** | Sonnet | Unit tests, integration, edge cases |
| **Architecture Guru** | 🏛️ | **1.8x** | Sonnet | SOLID, patterns, modularity |
| **User Advocate** | 👤 | **1.1x** | Haiku | API design, UX, error messages |
| **Maintenance Focused** | 🔧 | **1.2x** | Haiku | Readability, tech debt, legacy |

### Quality Modes

Each vote uses **4 judges**. Choose the review depth:

| Mode | Use case |
|------|----------|
| ⚡ **Lightning** | Quick checks, small changes (4× Haiku) |
| ⚖️ **Balanced** | Default, optimal balance (2× Sonnet + 2× Haiku) |
| 🔍 **Thorough** | Important reviews, security (4× Sonnet) |

Usage: `/vote --mode thorough` or `/vote --mode lightning`

### Weighted Voting Explained

- Judges with higher weight have more influence on the final verdict
- **Consensus detection**: Issues mentioned by 3+ judges get extra priority
- To pass: weighted "Yes" votes must exceed 60% of total weight
- Example: Security Expert (2.0x) saying ❌ hurts more than Mentor (1.0x) saying ❌

## 📊 Example Output

```
🎭 Vote Results
============================================================

👩‍⚖️ Оксана (Strict Critic) (weight: 1.7x)
  ✅ Good error handling, new functionality added
  ❌ Missing tests
  📊 6.5/10 | ❌ No

👨‍🏫 Тарас (Supportive Mentor) (weight: 1.0x)
  ✅ Clean architecture, good function names
  ❌ Needs more comments
  📊 8/10 | ✅ Yes

🔍 Ірина (Detail-Oriented Reviewer) (weight: 1.2x)
  ✅ Follows code style
  ❌ Magic numbers at line 45
  📊 7/10 | ✅ Yes

🎨 Богдан (Creative Engineer) (weight: 1.0x)
  ✅ Elegant caching solution
  ❌ Could optimize the loop
  📊 8/10 | ✅ Yes

============================================================
📊 Summary: 3.7 ✅ Yes | 1.5 ❌ No (weighted)
🎯 Average Score: 7.4/10

🎉 Great! Code passed the vote!

💡 Tips for improvement:
  • Add tests
  • Avoid magic numbers
  • Optimize the loop
```

## 🔄 Branch Tracking

When working on a feature branch, Vote skill tracks your progress:

1. First vote → ❌ Fails (finds: no tests, magic numbers)
2. Fix issues → Second vote → ✅ Shows what's fixed, what's still broken, what's new

```
📊 History on branch: feature-auth
============================================================

📋 Vote attempts:
  Attempt #1: 6.5/10 ❌
  Attempt #2: 7.5/10 ❌

📈 Trend: 6.5 → 7.5 (+1.0)

✅ Fixed issues:
  ✅ Added tests (was in attempt #1)

⚠️ Open issues:
  🔵 Deprecated function process()

============================================================
❌ Branch failing. Need to fix 1 issues.
```

## 🌍 Language Support

Judges names and personalities adapt to your language:

| Language | Flag | Example Names |
|----------|------|---------------|
| Ukrainian | 🇺🇦 | Оксана, Тарас, Ірина |
| English | 🇬🇧 | Alex, Maya, Chris |
| Arabic | 🇸🇦 | عمر, ليلى, حسن |
| Russian | 🇷🇺 | Алексей, Елена, Дмитрий |
| Polish | 🇵🇱 | Kasia, Tomek, Agnieszka |
| Spanish | 🇪🇸 | Carlos, Sofía, Miguel |
| German | 🇩🇪 | Hans, Greta, Fritz |
| French | 🇫🇷 | Pierre, Camille, Luc |
| Italian | 🇮🇹 | Marco, Giulia, Luca |

## 📁 Project Structure

```
.qwen/skills/vote/           # Qwen Code skill
├── SKILL.md                 # Skill description
├── scripts/
│   ├── select_judges.py     # Main entry point — judge selection
│   └── judge_profiles/      # 9 languages (names & personalities)
├── sessions/                # Vote cache (gitignored)
└── branches/                # Branch history (gitignored)

.claude/
├── commands/
│   └── vote.md              # /vote slash command for Claude
├── agents/
│   ├── jury-judge-haiku.md  # Lightweight sub-agent
│   └── jury-judge-sonnet.md # Expert sub-agent
└── skills/vote/             # Claude Code skill
    └── scripts/             # Same scripts as Qwen Code

judges.json                  # Source of truth for judge weights & models
install.sh                   # Installer (--remote for download from GitHub)
select_judges.py             # CLI: judge selection & localization
```

## ⚙️ Configuration

Key configuration files:

- `judges.json` — judge weights, models, and focus areas
- `select_judges.py` — `MODES` dict for quality mode behavior
- Language profiles in `.claude/skills/vote/scripts/judge_profiles/` — localized names & personalities

## 🔒 Privacy & Security

- Session data and branch history are **NOT committed to git**
- `.gitignore` files are included to protect sensitive information
- All data stays local — no external API calls (yet)

## 🛣️ Roadmap

- [ ] Real LLM API integration (Claude, GPT, Qwen)
- [ ] Custom judge personalities
- [ ] Vote report export (Markdown/PDF)
- [ ] Team sharing via git
- [ ] CI/CD integration
- [ ] Historical trends dashboard

## 🤝 Contributing

PRs welcome! Areas of interest:

- More language profiles
- New judge personality types
- LLM integration
- UI improvements

## 📝 License

MIT

## 👤 Authors

- 💡 **Idea**: [thecapibara](https://github.com/thecapibara)
- 🛠️ **Implementation**: Qwen Code + thecapibara
