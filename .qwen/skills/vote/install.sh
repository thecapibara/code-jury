#!/bin/bash
# Vote Skill Installer for Qwen Code
# Installs the Vote skill into ~/.qwen/skills/vote (personal) or .qwen/skills/vote (project)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎭 Vote Skill Installer${NC}"
echo -e "${BLUE}=====================${NC}"
echo ""

# Determine installation target
if [ "$1" == "--global" ] || [ "$1" == "-g" ]; then
    # Global installation
    TARGET_DIR="$HOME/.qwen/skills/vote"
    echo -e "${YELLOW}📂 Installing globally to: ~/.qwen/skills/vote${NC}"
else
    # Project installation (default)
    PROJECT_DIR="$(pwd)"
    
    # Check if we're in a git repo
    if git -C "$PROJECT_DIR" rev-parse --is-inside-work-tree > /dev/null 2>&1; then
        TARGET_DIR="$PROJECT_DIR/.qwen/skills/vote"
        echo -e "${YELLOW}📂 Installing to project: .qwen/skills/vote${NC}"
    else
        # Fallback to global
        TARGET_DIR="$HOME/.qwen/skills/vote"
        echo -e "${YELLOW}📂 Not in a git repo, installing globally: ~/.qwen/skills/vote${NC}"
    fi
fi

echo ""

# Create directories
echo "📁 Creating directories..."
mkdir -p "$TARGET_DIR/scripts/judge_profiles"
mkdir -p "$TARGET_DIR/sessions"
mkdir -p "$TARGET_DIR/branches"

# Copy files
echo "📋 Copying files..."
cp "$SCRIPT_DIR/SKILL.md" "$TARGET_DIR/SKILL.md" 2>/dev/null || true
cp "$SCRIPT_DIR/scripts/"*.py "$TARGET_DIR/scripts/"
cp "$SCRIPT_DIR/scripts/judge_profiles/"*.json "$TARGET_DIR/scripts/judge_profiles/"

# Create .gitignore files for sensitive data
cat > "$TARGET_DIR/sessions/.gitignore" << EOF
# Do not commit session data (contains sensitive info)
*.json
EOF

cat > "$TARGET_DIR/branches/.gitignore" << EOF
# Do not commit branch history (contains repo-specific data)
*.json
EOF

# Add to project .gitignore if not already there
if git -C "$PROJECT_DIR" rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    GITIGNORE="$PROJECT_DIR/.gitignore"
    if [ -f "$GITIGNORE" ]; then
        if ! grep -q ".qwen/skills/vote/sessions/" "$GITIGNORE" 2>/dev/null; then
            echo "" >> "$GITIGNORE"
            echo "# Vote Skill - sensitive data" >> "$GITIGNORE"
            echo ".qwen/skills/vote/sessions/" >> "$GITIGNORE"
            echo ".qwen/skills/vote/branches/" >> "$GITIGNORE"
            echo "✅ Added to .gitignore"
        fi
    else
        echo "# Vote Skill - sensitive data" > "$GITIGNORE"
        echo ".qwen/skills/vote/sessions/" >> "$GITIGNORE"
        echo ".qwen/skills/vote/branches/" >> "$GITIGNORE"
        echo "✅ Created .gitignore"
    fi
fi

echo ""
echo -e "${GREEN}✅ Vote Skill installed successfully!${NC}"
echo ""
echo "📍 Location: $TARGET_DIR"
echo ""
echo "🚀 Usage:"
echo "  Just ask Qwen Code to evaluate your code, or use:"
echo "    /skills vote          # Explicit invocation"
echo ""
echo "  Inside Qwen Code:"
echo "    Evaluate my changes   # AI will use Vote skill automatically"
echo "    Check the last commit # AI will run vote script"
echo ""
echo "📚 Supported languages: Ukrainian, English, Arabic, Russian, Polish,"
echo "   Spanish, German, French, Italian"
echo ""
echo "💡 Tip: Each vote uses 4 random judges from 10 personality types,"
echo "   with weighted voting for expertise areas."
