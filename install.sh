#!/bin/bash
# Vote Skill Installer for Qwen Code & Claude Code
# Usage: bash install.sh [--qwen] [--claude] [--global] [--remote]
#
# Remote mode: bash install.sh --remote [other options]
#   Downloads files from GitHub instead of copying locally.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🎭 Vote Skill Installer${NC}"
echo -e "${BLUE}=====================${NC}"
echo ""

INSTALL_QWEN=false
INSTALL_CLAUDE=false
GLOBAL=false
REMOTE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --qwen|-q)     INSTALL_QWEN=true; shift ;;
        --claude|-c)   INSTALL_CLAUDE=true; shift ;;
        --global|-g)   GLOBAL=true; shift ;;
        --all|-a)      INSTALL_QWEN=true; INSTALL_CLAUDE=true; shift ;;
        --remote|-r)   REMOTE=true; shift ;;
        --help|-h)
            echo -e "${CYAN}Usage: bash install.sh [options]${NC}"
            echo ""
            echo "  --qwen, -q     Install for Qwen Code only"
            echo "  --claude, -c   Install for Claude Code only"
            echo "  --all, -a      Install for both (default)"
            echo "  --global, -g   Install globally (~/.qwen, ~/.claude)"
            echo "  --remote, -r   Download from GitHub (instead of copy)"
            exit 0
            ;;
        *) echo -e "${RED}⚠️  Unknown option: $1${NC}"; exit 1 ;;
    esac
done

if [ "$INSTALL_QWEN" = false ] && [ "$INSTALL_CLAUDE" = false ]; then
    INSTALL_QWEN=true
    INSTALL_CLAUDE=true
fi

PROJECT_DIR="$(pwd)"
IS_GIT_REPO=false
git -C "$PROJECT_DIR" rev-parse --is-inside-work-tree > /dev/null 2>&1 && IS_GIT_REPO=true

# ─── Remote config ───
BASE_URL="${VOTE_SKILL_URL:-https://raw.githubusercontent.com/thecapibara/vote-skill/main}"

# ─── Source paths (relative to this repo root) ───
SELECT_JUDGES="$SCRIPT_DIR/select_judges.py"
JUDGES_JSON="$SCRIPT_DIR/judges.json"
PROFILES_DIR="$SCRIPT_DIR/.claude/skills/vote/scripts/judge_profiles"
CLAUDE_CMD="$SCRIPT_DIR/.claude/commands/vote.md"
QWEN_SKILL="$SCRIPT_DIR/.qwen/skills/vote/SKILL.md"
QWEN_CMD="$SCRIPT_DIR/.qwen/commands/vote.md"
QWEN_AGENT="$SCRIPT_DIR/.qwen/agents/jury-judge.md"
CLAUDE_AGENTS_DIR="$SCRIPT_DIR/.claude/agents"

# ─── Language profiles ───
PROFILES=(ukrainian english arabic russian polish spanish german french italian)
AGENTS_QWEN=(jury-judge.md)
AGENTS_CLAUDE=(jury-judge-haiku.md jury-judge-sonnet.md)

# ─── Transport abstraction: cp or curl ───
fetch_file() {
    local url_or_src="$1" dest="$2" desc="$3"
    if [ "$REMOTE" = true ]; then
        if curl -fsSL "$url_or_src" -o "$dest" 2>/dev/null; then
            echo -e "   ✅ $desc"
            return 0
        else
            echo -e "   ${RED}❌ Failed to download: $desc${NC}"
            return 1
        fi
    else
        if [ -f "$url_or_src" ]; then
            cp "$url_or_src" "$dest"
            echo -e "   ✅ $desc"
            return 0
        else
            echo -e "   ${RED}❌ Not found: $desc ($url_or_src)${NC}"
            return 1
        fi
    fi
}

# ─── Helper: copy/download shared files into target dir ───
install_shared() {
    local target_dir="$1"
    mkdir -p "$target_dir/scripts/judge_profiles"
    mkdir -p "$target_dir/sessions"
    mkdir -p "$target_dir/branches"

    fetch_file "$SELECT_JUDGES" "$target_dir/scripts/select_judges.py" "select_judges.py"
    fetch_file "$JUDGES_JSON" "$target_dir/scripts/judges.json" "judges.json"

    # Language profiles
    for p in "${PROFILES[@]}"; do
        if [ "$REMOTE" = true ]; then
            fetch_file "$BASE_URL/.claude/skills/vote/scripts/judge_profiles/${p}.json" \
                "$target_dir/scripts/judge_profiles/${p}.json" "${p}.json"
        else
            fetch_file "$PROFILES_DIR/${p}.json" \
                "$target_dir/scripts/judge_profiles/${p}.json" "${p}.json"
        fi
    done

    cat > "$target_dir/sessions/.gitignore" << 'EOF'
*.json
EOF
    cat > "$target_dir/branches/.gitignore" << 'EOF'
*.json
EOF
}

# ─── Helper: update project .gitignore ───
update_gitignore() {
    local pattern="$1"
    if [ "$IS_GIT_REPO" = true ] && [ "$GLOBAL" = false ]; then
        GITIGNORE="$PROJECT_DIR/.gitignore"
        if [ -f "$GITIGNORE" ]; then
            grep -q "$pattern/sessions/" "$GITIGNORE" 2>/dev/null || {
                echo "" >> "$GITIGNORE"
                echo "# Vote Skill sessions (sensitive)" >> "$GITIGNORE"
                echo "$pattern/sessions/" >> "$GITIGNORE"
                echo "$pattern/branches/" >> "$GITIGNORE"
            }
        else
            echo "# Vote Skill sessions (sensitive)" > "$GITIGNORE"
            echo "$pattern/sessions/" >> "$GITIGNORE"
            echo "$pattern/branches/" >> "$GITIGNORE"
        fi
    fi
}

# ─── Qwen install ───
install_qwen() {
    if [ "$GLOBAL" = true ]; then
        TARGET_DIR="$HOME/.qwen/skills/vote"
        AGENTS_DIR="$HOME/.qwen/agents"
    else
        TARGET_DIR="$PROJECT_DIR/.qwen/skills/vote"
        AGENTS_DIR="$PROJECT_DIR/.qwen/agents"
    fi

    echo -e "${CYAN}📦 Installing for Qwen Code...${NC}"
    echo "   → $TARGET_DIR"
    echo ""

    install_shared "$TARGET_DIR"

    if [ "$REMOTE" = true ]; then
        fetch_file "$BASE_URL/.qwen/skills/vote/SKILL.md" "$TARGET_DIR/SKILL.md" "SKILL.md"
    elif [ -f "$QWEN_SKILL" ]; then
        fetch_file "$QWEN_SKILL" "$TARGET_DIR/SKILL.md" "SKILL.md"
    fi

    # Install Qwen command
    if [ "$GLOBAL" = false ]; then
        mkdir -p "$PROJECT_DIR/.qwen/commands"
        if [ "$REMOTE" = true ]; then
            fetch_file "$BASE_URL/.qwen/commands/vote.md" "$PROJECT_DIR/.qwen/commands/vote.md" "vote.md"
        elif [ -f "$QWEN_CMD" ]; then
            fetch_file "$QWEN_CMD" "$PROJECT_DIR/.qwen/commands/vote.md" "vote.md"
        fi
    fi

    # Install Qwen agent
    mkdir -p "$AGENTS_DIR"
    for agent in "${AGENTS_QWEN[@]}"; do
        if [ "$REMOTE" = true ]; then
            fetch_file "$BASE_URL/.qwen/agents/$agent" "$AGENTS_DIR/$agent" "$agent"
        elif [ -f "$QWEN_AGENT" ]; then
            fetch_file "$QWEN_AGENT" "$AGENTS_DIR/$agent" "$agent"
        fi
    done

    update_gitignore ".qwen/skills/vote"

    echo ""
    echo -e "   ${GREEN}✅ Qwen Code skill installed${NC}"
    echo ""
}

# ─── Claude install ───
install_claude() {
    if [ "$GLOBAL" = true ]; then
        TARGET_DIR="$HOME/.claude/skills/vote"
        AGENTS_DIR="$HOME/.claude/agents"
    else
        TARGET_DIR="$PROJECT_DIR/.claude/skills/vote"
        AGENTS_DIR="$PROJECT_DIR/.claude/agents"
    fi

    echo -e "${CYAN}📦 Installing for Claude Code...${NC}"
    echo "   → $TARGET_DIR"
    echo ""

    install_shared "$TARGET_DIR"

    # Install Claude command
    if [ "$GLOBAL" = false ]; then
        mkdir -p "$PROJECT_DIR/.claude/commands"
        if [ "$REMOTE" = true ]; then
            fetch_file "$BASE_URL/.claude/commands/vote.md" "$PROJECT_DIR/.claude/commands/vote.md" "vote.md"
        elif [ -f "$CLAUDE_CMD" ]; then
            fetch_file "$CLAUDE_CMD" "$PROJECT_DIR/.claude/commands/vote.md" "vote.md"
        fi
    fi

    # Install Claude agents
    mkdir -p "$AGENTS_DIR"
    if [ "$REMOTE" = true ]; then
        for agent in "${AGENTS_CLAUDE[@]}"; do
            fetch_file "$BASE_URL/.claude/agents/$agent" "$AGENTS_DIR/$agent" "$agent"
        done
    elif [ -d "$CLAUDE_AGENTS_DIR" ]; then
        for agent in "${AGENTS_CLAUDE[@]}"; do
            fetch_file "$CLAUDE_AGENTS_DIR/$agent" "$AGENTS_DIR/$agent" "$agent"
        done
    fi

    update_gitignore ".claude/skills/vote"

    echo ""
    echo -e "   ${GREEN}✅ Claude Code skill installed${NC}"
    echo ""
}

# ─── Execute ───
echo ""
[ "$INSTALL_QWEN" = true ] && install_qwen
[ "$INSTALL_CLAUDE" = true ] && install_claude

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Vote Skill installation complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "🚀 Usage:"
echo ""
[ "$INSTALL_QWEN" = true ] && echo "  ${CYAN}Qwen Code:${NC}  Ask: 'evaluate my changes'  or  /skills vote" && echo ""
[ "$INSTALL_CLAUDE" = true ] && echo -e "  ${CYAN}Claude Code:${NC}  /vote                    # Evaluate changes
  /vote --mode lightning     # Quick (4× Haiku)
  /vote --mode thorough      # Deep  (4× Sonnet)
  /vote history              # View history" && echo ""

echo "🌍 Languages: Ukrainian, English, Arabic, Russian, Polish, Spanish, German, French, Italian"
echo "💡 4 judges from 10 personality types with weighted voting"
echo ""
echo "👤 Idea: thecapibara | Implementation: Qwen Code + thecapibara"
