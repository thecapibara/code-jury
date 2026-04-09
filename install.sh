#!/bin/bash
# Vote Skill Installer for Qwen Code & Claude Code
# One script to rule them all!
#
# Usage:
#   bash install.sh                    # Both, project-local
#   bash install.sh --qwen             # Qwen only
#   bash install.sh --claude           # Claude only
#   bash install.sh --all --global     # Both, globally

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
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
            echo -e "${CYAN}Usage: bash install.sh [options]${NC}"
            echo ""
            echo "Options:"
            echo "  --qwen, -q       Install for Qwen Code only"
            echo "  --claude, -c     Install for Claude Code only"
            echo "  --all, -a        Install for both (default)"
            echo "  --global, -g     Install globally (~/.qwen, ~/.claude)"
            echo "                   (default: project-local .qwen, .claude)"
            echo "  --help, -h       Show this help"
            echo ""
            echo -e "${CYAN}Examples:${NC}"
            echo "  bash install.sh              # Both, project-local"
            echo "  bash install.sh --qwen       # Qwen only"
            echo "  bash install.sh --claude     # Claude only"
            echo "  bash install.sh --claude -g  # Claude, globally"
            echo "  bash install.sh -a -g        # Both, globally"
            exit 0
            ;;
        *)
            echo -e "${RED}⚠️  Unknown option: $1${NC}"
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

# Shared scripts and profiles
SHARED_SCRIPTS="$SCRIPT_DIR/.claude/skills/vote/scripts"
SHARED_PROFILES="$SCRIPT_DIR/.claude/skills/vote/scripts/judge_profiles"
QWEN_SKILL_MD="$SCRIPT_DIR/.qwen/skills/vote/SKILL.md"
CLAUDE_COMMAND="$SCRIPT_DIR/.claude/commands/vote.md"

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

    # Copy SKILL.md
    if [ -f "$QWEN_SKILL_MD" ]; then
        cp "$QWEN_SKILL_MD" "$TARGET_DIR/SKILL.md"
    fi

    # Copy scripts
    if [ -d "$SHARED_SCRIPTS" ]; then
        cp "$SHARED_SCRIPTS/"*.py "$TARGET_DIR/scripts/"
        cp "$SHARED_PROFILES/"*.json "$TARGET_DIR/scripts/judge_profiles/"
    else
        echo -e "${RED}   ❌ Scripts not found at: $SHARED_SCRIPTS${NC}"
        return 1
    fi

    # Create gitignore files
    cat > "$TARGET_DIR/sessions/.gitignore" << 'EOF'
*.json
EOF
    cat > "$TARGET_DIR/branches/.gitignore" << 'EOF'
*.json
EOF

    # Update project .gitignore
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
        TARGET_DIR="$HOME/.claude/skills/vote"
    else
        TARGET_DIR="$PROJECT_DIR/.claude/skills/vote"
    fi

    echo -e "${CYAN}📦 Installing for Claude Code...${NC}"
    echo "   → $TARGET_DIR"

    mkdir -p "$TARGET_DIR/scripts/judge_profiles"
    mkdir -p "$TARGET_DIR/sessions"
    mkdir -p "$TARGET_DIR/branches"
    if [ "$GLOBAL" = false ]; then
        mkdir -p "$PROJECT_DIR/.claude/commands"
    fi

    # Copy scripts
    if [ -d "$SHARED_SCRIPTS" ]; then
        cp "$SHARED_SCRIPTS/"*.py "$TARGET_DIR/scripts/"
        cp "$SHARED_PROFILES/"*.json "$TARGET_DIR/scripts/judge_profiles/"
    else
        echo -e "${RED}   ❌ Scripts not found at: $SHARED_SCRIPTS${NC}"
        return 1
    fi

    # Copy command file
    if [ "$GLOBAL" = false ] && [ -f "$CLAUDE_COMMAND" ]; then
        cp "$CLAUDE_COMMAND" "$PROJECT_DIR/.claude/commands/vote.md"
    fi

    # Create gitignore files
    cat > "$TARGET_DIR/sessions/.gitignore" << 'EOF'
*.json
EOF
    cat > "$TARGET_DIR/branches/.gitignore" << 'EOF'
*.json
EOF

    # Update project .gitignore
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
