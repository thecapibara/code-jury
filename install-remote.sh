#!/bin/bash
# Remote installer for Vote Skill
# Usage: curl -fsSL <url>/install-remote.sh | bash -s -- [options]
#
# Options:
#   --qwen       Install for Qwen Code only
#   --claude     Install for Claude Code only
#   --all        Install for both (default)
#   --global     Install globally (~/.qwen, ~/.claude)
#   --help       Show help

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

# GitHub raw URL — override with VOTE_SKILL_URL env var if forked
BASE_URL="${VOTE_SKILL_URL:-https://raw.githubusercontent.com/thecapibara/vote-skill/main}"

echo -e "${BLUE}🎭 Vote Skill Installer${NC}"
echo -e "${BLUE}=====================${NC}"
echo ""

INSTALL_QWEN=false
INSTALL_CLAUDE=false
GLOBAL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --qwen|-q)  INSTALL_QWEN=true; shift ;;
        --claude|-c)  INSTALL_CLAUDE=true; shift ;;
        --global|-g)  GLOBAL=true; shift ;;
        --all|-a)  INSTALL_QWEN=true; INSTALL_CLAUDE=true; shift ;;
        --help|-h)
            echo -e "${CYAN}Usage: curl -fsSL <url>/install-remote.sh | bash -s -- [options]${NC}"
            echo ""
            echo "  --qwen, -q     Install for Qwen Code only"
            echo "  --claude, -c   Install for Claude Code only"
            echo "  --all, -a      Install for both (default)"
            echo "  --global, -g   Install globally"
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

# ─── Files to download ───
PROFILES=(ukrainian english arabic russian polish spanish german french italian)
AGENTS_QWEN=(jury-judge.md)
AGENTS_CLAUDE=(jury-judge-haiku.md jury-judge-sonnet.md)

download_file() {
    local url="$1" dest="$2" desc="$3"
    if curl -fsSL "$url" -o "$dest" 2>/dev/null; then
        echo -e "   ✅ $desc"
        return 0
    else
        echo -e "   ${RED}❌ Failed: $desc${NC}"
        return 1
    fi
}

download_shared() {
    local target_dir="$1"
    mkdir -p "$target_dir/scripts/judge_profiles" "$target_dir/sessions" "$target_dir/branches"

    # select_judges.py + judges.json from repo root
    download_file "$BASE_URL/select_judges.py" "$target_dir/scripts/select_judges.py" "select_judges.py"
    download_file "$BASE_URL/judges.json" "$target_dir/scripts/judges.json" "judges.json"

    # Language profiles
    for p in "${PROFILES[@]}"; do
        download_file "$BASE_URL/.claude/skills/vote/scripts/judge_profiles/${p}.json" \
            "$target_dir/scripts/judge_profiles/${p}.json" "${p}.json"
    done

    cat > "$target_dir/sessions/.gitignore" << 'EOF'
*.json
EOF
    cat > "$target_dir/branches/.gitignore" << 'EOF'
*.json
EOF
}

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

    download_shared "$TARGET_DIR"
    download_file "$BASE_URL/.qwen/skills/vote/SKILL.md" "$TARGET_DIR/SKILL.md" "SKILL.md"

    # Download Qwen agent
    mkdir -p "$AGENTS_DIR"
    for agent in "${AGENTS_QWEN[@]}"; do
        download_file "$BASE_URL/.qwen/agents/$agent" "$AGENTS_DIR/$agent" "$agent"
    done

    update_gitignore ".qwen/skills/vote"

    echo ""
    echo -e "   ${GREEN}✅ Qwen Code skill installed${NC}"
    echo ""
}

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

    download_shared "$TARGET_DIR"

    if [ "$GLOBAL" = false ]; then
        mkdir -p "$PROJECT_DIR/.claude/commands"
        download_file "$BASE_URL/.claude/commands/vote.md" "$PROJECT_DIR/.claude/commands/vote.md" "vote.md"
    fi

    # Download Claude agents
    mkdir -p "$AGENTS_DIR"
    for agent in "${AGENTS_CLAUDE[@]}"; do
        download_file "$BASE_URL/.claude/agents/$agent" "$AGENTS_DIR/$agent" "$agent"
    done

    update_gitignore ".claude/skills/vote"

    echo ""
    echo -e "   ${GREEN}✅ Claude Code skill installed${NC}"
    echo ""
}

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
