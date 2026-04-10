# 🎭 Vote Skill for Qwen Code

**4 independent AI judges evaluate your code — like America's Got Talent!**

Each judge has a unique name, personality, and expertise focus. They evaluate your code in parallel and deliver verdicts with scores, likes, dislikes, and actionable feedback.

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
curl -fsSL https://raw.githubusercontent.com/thecapibara/vote-skill/main/install-remote.sh | bash

# Qwen Code only
curl -fsSL https://raw.githubusercontent.com/thecapibara/vote-skill/main/install-remote.sh | bash -s -- --qwen

# Claude Code only
curl -fsSL https://raw.githubusercontent.com/thecapibara/vote-skill/main/install-remote.sh | bash -s -- --claude

# Global installation
curl -fsSL https://raw.githubusercontent.com/thecapibara/vote-skill/main/install-remote.sh | bash -s -- --all --global
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
```

### Verify Installation

```bash
cd ~/.qwen/skills/vote  # or .qwen/skills/vote
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

Or directly run the script:
```bash
python3 .claude/skills/vote/scripts/vote.py [args]
```

## 👥 The Judges

Each vote uses **4 judges** randomly selected from **10 personality types**:

| Personality | Emoji | Weight | Expertise |
|-------------|-------|--------|-----------|
| Strict Critic | 👩‍⚖️ | **1.5x** | Architecture, errors, security |
| Supportive Mentor | 👨‍🏫 | 1.0x | Potential, best practices, learning |
| Detail-Oriented Reviewer | 🔍 | 1.2x | Style, docs, tests, DRY |
| Creative Engineer | 🎨 | 1.0x | Creativity, performance, elegance |
| **Security Expert** | 🛡️ | **1.8x** | Vulnerabilities, validation, encryption |
| **Performance Optimizer** | ⚡ | **1.3x** | Algorithms, memory, CPU, scalability |
| **Testing Expert** | 🧪 | **1.4x** | Unit tests, integration, edge cases |
| **Architecture Guru** | 🏛️ | **1.6x** | SOLID, patterns, modularity |
| **User Advocate** | 👤 | **1.1x** | API design, UX, error messages |
| **Maintenance Focused** | 🔧 | **1.2x** | Readability, tech debt, legacy |

### Quality Modes

Each vote uses **4 judges**. Choose the review depth:

| Mode | Judges | Use case |
|------|--------|----------|
| ⚡ **Lightning** | 4× Haiku | Quick checks, small changes |
| ⚖️ **Balanced** | 2× Sonnet + 2× Haiku | Default, optimal balance |
| 🔍 **Thorough** | 4× Sonnet | Important reviews, security |

Claude Code: `/vote --mode thorough` or `/vote --mode lightning`

### The Judges

Each vote uses **4 judges** randomly selected from **10 personality types**:

| Personality | Emoji | Weight | Expertise |
|-------------|-------|--------|-----------|
| Strict Critic | 👩‍️ | **1.7x** | Architecture, errors, security |
| Supportive Mentor | 👨‍ | 1.0x | Potential, best practices, learning |
| Detail-Oriented Reviewer | 🔍 | 1.2x | Style, docs, tests, DRY |
| Creative Engineer | 🎨 | 1.0x | Creativity, performance, elegance |
| **Security Expert** | 🛡️ | **2.0x** | Vulnerabilities, validation, encryption |
| **Performance Optimizer** | ⚡ | **1.5x** | Algorithms, memory, CPU, scalability |
| **Testing Expert** | 🧪 | **1.6x** | Unit tests, integration, edge cases |
| **Architecture Guru** | 🏛️ | **1.8x** | SOLID, patterns, modularity |
| **User Advocate** | 👤 | **1.1x** | API design, UX, error messages |
| **Maintenance Focused** | 🔧 | **1.2x** | Readability, tech debt, legacy |

### Weighted Voting Explained

- Judges with higher weight have more influence on the final verdict
- **Consensus detection**: Issues mentioned by 3+ judges get extra priority
- To pass: weighted "Yes" votes must exceed 60% of total weight
- Example: Security Expert (2.0x) saying ❌ hurts more than Mentor (1.0x) saying ❌

## 📊 Example Output

```
🎭 Vote Results
============================================================

👩‍⚖️ Оксана (Strict Critic) (weight: 1.5x)
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
├── install.sh               # Installer script
├── scripts/
│   ├── vote.py              # Main entry point
│   ├── judge_coordinator.py # Judge orchestration
│   ├── language_detector.py # Language detection
│   ├── branch_tracker.py    # Branch issue tracking
│   └── judge_profiles/      # 9 languages
├── sessions/                # Vote cache (gitignored)
└── branches/                # Branch history (gitignored)

.claude/
├── commands/
│   └── vote.md              # /vote slash command for Claude
└── skills/vote/             # Claude Code skill
    └── scripts/             # Same scripts as Qwen Code
```

## ⚙️ Configuration

Edit `SKILL.md` to modify behavior. Key settings in `judge_coordinator.py`:

- `JUDGES_COUNT = 4` — number of judges per vote
- `MAX_DIFF_LINES = 200` — diff optimization threshold
- `MAX_CONTEXT_LINES = 3` — context around changes

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
