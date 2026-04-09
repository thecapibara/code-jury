#!/bin/bash
# Remote installer for Vote Skill
# Usage: curl -fsSL https://raw.githubusercontent.com/thecapibara/vote-skill/main/install.sh | bash -s -- [options]
#
# Options:
#   --qwen       Install for Qwen Code only
#   --claude     Install for Claude Code only
#   --all        Install for both (default)
#   --global     Install globally (~/.qwen, ~/.claude)
#   --help       Show help

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

# GitHub raw URL (change this to your actual repo)
BASE_URL="${VOTE_SKILL_URL:-https://raw.githubusercontent.com/thecapibara/vote-skill/main}"

echo -e "${BLUE}🎭 Vote Skill Installer${NC}"
echo -e "${BLUE}=====================${NC}"
echo ""

# Parse arguments
INSTALL_QWEN=false
INSTALL_CLAUDE=false
GLOBAL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --qwen|-q)
            INSTALL_QWEN=true
            shift
            ;;
        --claude|-c)
            INSTALL_CLAUDE=true
            shift
            ;;
        --global|-g)
            GLOBAL=true
            shift
            ;;
        --all|-a)
            INSTALL_QWEN=true
            INSTALL_CLAUDE=true
            shift
            ;;
        --help|-h)
            echo -e "${CYAN}Usage: curl -fsSL <url>/install.sh | bash -s -- [options]${NC}"
            echo ""
            echo "Options:"
            echo "  --qwen, -q       Install for Qwen Code only"
            echo "  --claude, -c     Install for Claude Code only"
            echo "  --all, -a        Install for both (default)"
            echo "  --global, -g     Install globally"
            echo "  --help, -h       Show this help"
            echo ""
            echo -e "${CYAN}Examples:${NC}"
            echo "  curl -fsSL <url>/install.sh | bash -s -- --claude"
            echo "  curl -fsSL <url>/install.sh | bash -s -- --qwen --global"
            echo "  curl -fsSL <url>/install.sh | bash -s -- --all"
            exit 0
            ;;
        *)
            echo -e "${RED}⚠️  Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Default: both
if [ "$INSTALL_QWEN" = false ] && [ "$INSTALL_CLAUDE" = false ]; then
    INSTALL_QWEN=true
    INSTALL_CLAUDE=true
fi

PROJECT_DIR="$(pwd)"
IS_GIT_REPO=false
if git -C "$PROJECT_DIR" rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    IS_GIT_REPO=true
fi

# Files to download
SCRIPTS=(
    "vote.py"
    "judge_coordinator.py"
    "language_detector.py"
    "branch_tracker.py"
)

PROFILES=(
    "ukrainian.json"
    "english.json"
    "arabic.json"
    "russian.json"
    "polish.json"
    "spanish.json"
    "german.json"
    "french.json"
    "italian.json"
)

download_file() {
    local url="$1"
    local dest="$2"
    local desc="$3"

    if curl -fsSL "$url" -o "$dest" 2>/dev/null; then
        echo -e "   ✅ $desc"
        return 0
    else
        echo -e "   ${RED}❌ Failed to download: $desc${NC}"
        return 1
    fi
}

download_scripts() {
    local target_dir="$1"

    mkdir -p "$target_dir/scripts/judge_profiles"
    mkdir -p "$target_dir/sessions"
    mkdir -p "$target_dir/branches"

    # Download main scripts
    for script in "${SCRIPTS[@]}"; do
        download_file "$BASE_URL/.claude/skills/vote/scripts/$script" "$target_dir/scripts/$script" "$script"
    done

    # Download profiles
    for profile in "${PROFILES[@]}"; do
        download_file "$BASE_URL/.claude/skills/vote/scripts/judge_profiles/$profile" "$target_dir/scripts/judge_profiles/$profile" "$profile"
    done

    # Create gitignore files
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
            if ! grep -q "$pattern" "$GITIGNORE" 2>/dev/null; then
                echo "" >> "$GITIGNORE"
                echo "# Vote Skill sessions (sensitive)" >> "$GITIGNORE"
                echo "$pattern/sessions/" >> "$GITIGNORE"
                echo "$pattern/branches/" >> "$GITIGNORE"
            fi
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
    else
        TARGET_DIR="$PROJECT_DIR/.qwen/skills/vote"
    fi

    echo -e "${CYAN}📦 Installing for Qwen Code...${NC}"
    echo "   → $TARGET_DIR"
    echo ""

    download_scripts "$TARGET_DIR"

    # Download SKILL.md
    download_file "$BASE_URL/.qwen/skills/vote/SKILL.md" "$TARGET_DIR/SKILL.md" "SKILL.md"

    update_gitignore ".qwen/skills/vote"

    echo ""
    echo -e "   ${GREEN}✅ Qwen Code skill installed${NC}"
    echo ""
}

install_claude() {
    if [ "$GLOBAL" = true ]; then
        TARGET_DIR="$HOME/.claude/skills/vote"
    else
        TARGET_DIR="$PROJECT_DIR/.claude/skills/vote"
    fi

    echo -e "${CYAN}📦 Installing for Claude Code...${NC}"
    echo "   → $TARGET_DIR"
    echo ""

    download_scripts "$TARGET_DIR"

    # Download command file
    if [ "$GLOBAL" = false ]; then
        mkdir -p "$PROJECT_DIR/.claude/commands"
        download_file "$BASE_URL/.claude/commands/vote.md" "$PROJECT_DIR/.claude/commands/vote.md" "vote.md (command)"
    fi

    update_gitignore ".claude/skills/vote"

    echo ""
    echo -e "   ${GREEN}✅ Claude Code skill installed${NC}"
    echo ""
}

# Execute installations
echo ""

if [ "$INSTALL_QWEN" = true ]; then
    install_qwen
fi

if [ "$INSTALL_CLAUDE" = true ]; then
    install_claude
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Vote Skill installation complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "🚀 Usage:"
echo ""
if [ "$INSTALL_QWEN" = true ]; then
    echo "  ${CYAN}Qwen Code:${NC}"
    echo "    Ask: 'evaluate my changes'"
    echo "    Or: /skills vote"
    echo ""
fi
if [ "$INSTALL_CLAUDE" = true ]; then
    echo "  ${CYAN}Claude Code:${NC}"
    echo "    /vote                    # Evaluate changes"
    echo "    /vote last commit         # Last commit"
    echo "    /vote branch feature      # Branch changes"
    echo "    /vote history             # View history"
    echo ""
fi
echo "🌍 Languages: Ukrainian, English, Arabic, Russian, Polish,"
echo "   Spanish, German, French, Italian"
echo ""
echo "💡 4 judges from 10 personality types with weighted voting"
echo ""
echo "👤 Idea: thecapibara | Implementation: Qwen Code + thecapibara"
