#!/bin/bash
# Vote Skill Installer for Qwen Code & Claude Code
# Usage: bash install.sh [--qwen] [--claude] [--global]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

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
            echo "Usage: bash install.sh [options]"
            echo ""
            echo "Options:"
            echo "  --qwen, -q       Install for Qwen Code only"
            echo "  --claude, -c     Install for Claude Code only"
            echo "  --all, -a        Install for both (default)"
            echo "  --global, -g     Install globally (~/.qwen, ~/.claude)"
            echo "                   (default: project-local .qwen, .claude)"
            echo "  --help, -h       Show this help"
            echo ""
            echo "Examples:"
            echo "  bash install.sh              # Both, project-local"
            echo "  bash install.sh --qwen       # Qwen only"
            echo "  bash install.sh --claude     # Claude only"
            echo "  bash install.sh --claude --global  # Claude, globally"
            echo "  bash install.sh --all --global     # Both, globally"
            exit 0
            ;;
        *)
            echo -e "${YELLOW}⚠️  Unknown option: $1${NC}"
            echo "Use --help for usage info"
            exit 1
            ;;
    esac
done

# Default: install both if nothing specified
if [ "$INSTALL_QWEN" = false ] && [ "$INSTALL_CLAUDE" = false ]; then
    INSTALL_QWEN=true
    INSTALL_CLAUDE=true
fi

PROJECT_DIR="$(pwd)"
IS_GIT_REPO=false

if git -C "$PROJECT_DIR" rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    IS_GIT_REPO=true
fi

install_qwen() {
    if [ "$GLOBAL" = true ]; then
        TARGET_DIR="$HOME/.qwen/skills/vote"
    else
        TARGET_DIR="$PROJECT_DIR/.qwen/skills/vote"
    fi

    echo -e "${CYAN}📦 Installing for Qwen Code...${NC}"
    echo "   → $TARGET_DIR"

    mkdir -p "$TARGET_DIR/scripts/judge_profiles"
    mkdir -p "$TARGET_DIR/sessions"
    mkdir -p "$TARGET_DIR/branches"

    cp "$SCRIPT_DIR/SKILL.md" "$TARGET_DIR/SKILL.md" 2>/dev/null || true
    cp "$SCRIPT_DIR/scripts/"*.py "$TARGET_DIR/scripts/"
    cp "$SCRIPT_DIR/scripts/judge_profiles/"*.json "$TARGET_DIR/scripts/judge_profiles/"

    cat > "$TARGET_DIR/sessions/.gitignore" << 'EOF'
*.json
EOF
    cat > "$TARGET_DIR/branches/.gitignore" << 'EOF'
*.json
EOF

    if [ "$IS_GIT_REPO" = true ] && [ "$GLOBAL" = false ]; then
        GITIGNORE="$PROJECT_DIR/.gitignore"
        if [ -f "$GITIGNORE" ]; then
            if ! grep -q ".qwen/skills/vote/sessions/" "$GITIGNORE" 2>/dev/null; then
                echo "" >> "$GITIGNORE"
                echo "# Vote Skill sessions (sensitive)" >> "$GITIGNORE"
                echo ".qwen/skills/vote/sessions/" >> "$GITIGNORE"
                echo ".qwen/skills/vote/branches/" >> "$GITIGNORE"
            fi
        else
            echo "# Vote Skill sessions (sensitive)" > "$GITIGNORE"
            echo ".qwen/skills/vote/sessions/" >> "$GITIGNORE"
            echo ".qwen/skills/vote/branches/" >> "$GITIGNORE"
        fi
    fi

    echo -e "   ${GREEN}✅ Qwen Code skill installed${NC}"
    echo ""
}

install_claude() {
    if [ "$GLOBAL" = true ]; then
        # Claude doesn't have a standard global skills dir like Qwen
        # Use ~/.claude/skills/ as convention
        TARGET_DIR="$HOME/.claude/skills/vote"
    else
        TARGET_DIR="$PROJECT_DIR/.claude/skills/vote"
    fi

    echo -e "${CYAN}📦 Installing for Claude Code...${NC}"
    echo "   → $TARGET_DIR"

    mkdir -p "$TARGET_DIR/scripts/judge_profiles"
    mkdir -p "$TARGET_DIR/sessions"
    mkdir -p "$TARGET_DIR/branches"
    mkdir -p "$PROJECT_DIR/.claude/commands"

    cp "$SCRIPT_DIR/scripts/"*.py "$TARGET_DIR/scripts/"
    cp "$SCRIPT_DIR/scripts/judge_profiles/"*.json "$TARGET_DIR/scripts/judge_profiles/"
    cp "$SCRIPT_DIR/../commands/vote.md" "$PROJECT_DIR/.claude/commands/vote.md" 2>/dev/null || true

    cat > "$TARGET_DIR/sessions/.gitignore" << 'EOF'
*.json
EOF
    cat > "$TARGET_DIR/branches/.gitignore" << 'EOF'
*.json
EOF

    if [ "$IS_GIT_REPO" = true ] && [ "$GLOBAL" = false ]; then
        GITIGNORE="$PROJECT_DIR/.gitignore"
        if [ -f "$GITIGNORE" ]; then
            if ! grep -q ".claude/skills/vote/sessions/" "$GITIGNORE" 2>/dev/null; then
                echo "" >> "$GITIGNORE"
                echo "# Vote Skill sessions (sensitive)" >> "$GITIGNORE"
                echo ".claude/skills/vote/sessions/" >> "$GITIGNORE"
                echo ".claude/skills/vote/branches/" >> "$GITIGNORE"
            fi
        else
            echo "# Vote Skill sessions (sensitive)" > "$GITIGNORE"
            echo ".claude/skills/vote/sessions/" >> "$GITIGNORE"
            echo ".claude/skills/vote/branches/" >> "$GITIGNORE"
        fi
    fi

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
    echo "  Qwen Code:"
    echo "    Ask naturally: 'evaluate my changes'"
    echo "    Or: /skills vote"
    echo ""
fi
if [ "$INSTALL_CLAUDE" = true ]; then
    echo "  Claude Code:"
    echo "    /vote                    # Evaluate changes"
    echo "    /vote last commit         # Last commit"
    echo "    /vote branch feature-name # Branch changes"
    echo "    /vote history             # View history"
    echo ""
fi
echo "🌍 Languages: Ukrainian, English, Arabic, Russian, Polish,"
echo "   Spanish, German, French, Italian"
echo ""
echo "💡 4 judges from 10 personality types with weighted voting"
