#!/bin/bash
# ============================================
# YouTube Extractor — Mac Setup Script
# ============================================
# Run this once on your Mac to:
#   1. Install Python dependencies (yt-dlp, youtube-transcript-api)
#   2. Create logs directory
#   3. Install launchd plist (runs extractor daily at 8:30 PM)
#
# Usage: bash setup_youtube_cron.sh
# To uninstall: bash setup_youtube_cron.sh --uninstall
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PLIST_NAME="com.aakash.youtube-extractor"
PLIST_SRC="$SCRIPT_DIR/$PLIST_NAME.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

if [ "$1" == "--uninstall" ]; then
    echo -e "${YELLOW}Uninstalling YouTube extractor scheduled job...${NC}"
    launchctl unload "$PLIST_DEST" 2>/dev/null || true
    rm -f "$PLIST_DEST"
    echo -e "${GREEN}Done. Launchd job removed.${NC}"
    echo "Note: Python packages (yt-dlp, youtube-transcript-api) were NOT removed."
    exit 0
fi

echo "============================================"
echo "  YouTube Extractor — Mac Setup"
echo "============================================"
echo ""

# Step 1: Check/install Python dependencies
echo -e "${YELLOW}Step 1: Checking Python dependencies...${NC}"

if python3 -c "import yt_dlp" 2>/dev/null; then
    echo "  ✓ yt-dlp already installed"
else
    echo "  Installing yt-dlp..."
    pip3 install yt-dlp
fi

if python3 -c "from youtube_transcript_api import YouTubeTranscriptApi" 2>/dev/null; then
    echo "  ✓ youtube-transcript-api already installed"
else
    echo "  Installing youtube-transcript-api..."
    pip3 install youtube-transcript-api
fi

# Also check yt-dlp CLI is available
if command -v yt-dlp &>/dev/null; then
    echo "  ✓ yt-dlp CLI available at: $(which yt-dlp)"
else
    echo -e "${RED}  ⚠ yt-dlp CLI not found in PATH. Trying brew install...${NC}"
    if command -v brew &>/dev/null; then
        brew install yt-dlp
    else
        echo -e "${RED}  ERROR: Neither yt-dlp nor brew found. Install yt-dlp manually: pip3 install yt-dlp${NC}"
        exit 1
    fi
fi

echo ""

# Step 2: Create directories
echo -e "${YELLOW}Step 2: Creating directories...${NC}"
mkdir -p "$PROJECT_DIR/queue"
mkdir -p "$PROJECT_DIR/queue/processed"
mkdir -p "$PROJECT_DIR/logs"
echo "  ✓ queue/ directory ready"
echo "  ✓ logs/ directory ready"
echo ""

# Step 3: Make extractor executable
echo -e "${YELLOW}Step 3: Making extractor executable...${NC}"
chmod +x "$SCRIPT_DIR/youtube_extractor.py"
echo "  ✓ youtube_extractor.py is executable"
echo ""

# Step 4: Install launchd plist
echo -e "${YELLOW}Step 4: Installing launchd job...${NC}"

if [ ! -f "$PLIST_SRC" ]; then
    echo -e "${RED}  ERROR: Plist file not found at $PLIST_SRC${NC}"
    exit 1
fi

# Unload existing if present
launchctl unload "$PLIST_DEST" 2>/dev/null || true

# Copy plist to LaunchAgents
mkdir -p "$HOME/Library/LaunchAgents"
cp "$PLIST_SRC" "$PLIST_DEST"

# Load the job
launchctl load "$PLIST_DEST"

echo "  ✓ Launchd job installed and loaded"
echo ""

# Step 5: Install `yt` CLI alias
echo -e "${YELLOW}Step 5: Installing 'yt' CLI shortcut...${NC}"
YT_SCRIPT="$SCRIPT_DIR/yt"
if [ -f "$YT_SCRIPT" ]; then
    chmod +x "$YT_SCRIPT"
    # Add to PATH via symlink
    if [ -d "/usr/local/bin" ] && [ -w "/usr/local/bin" ]; then
        ln -sf "$YT_SCRIPT" /usr/local/bin/yt
        echo "  ✓ 'yt' command installed to /usr/local/bin/yt"
    else
        # Fallback: add scripts dir to PATH in shell profile
        SHELL_RC="$HOME/.zshrc"
        [ -f "$HOME/.bashrc" ] && [ ! -f "$HOME/.zshrc" ] && SHELL_RC="$HOME/.bashrc"
        PATH_LINE="export PATH=\"$SCRIPT_DIR:\$PATH\""
        if ! grep -q "Aakash AI CoS/scripts" "$SHELL_RC" 2>/dev/null; then
            echo "" >> "$SHELL_RC"
            echo "# AI CoS YouTube extractor" >> "$SHELL_RC"
            echo "$PATH_LINE" >> "$SHELL_RC"
            echo "  ✓ Added scripts dir to PATH in $SHELL_RC"
            echo "  ⚠ Run 'source $SHELL_RC' or open a new terminal to use 'yt'"
        else
            echo "  ✓ Scripts dir already in PATH"
        fi
    fi
else
    echo -e "  ${RED}⚠ yt script not found at $YT_SCRIPT${NC}"
fi
echo ""

# Step 6: Verify
echo -e "${YELLOW}Step 6: Verifying...${NC}"
if launchctl list | grep -q "$PLIST_NAME"; then
    echo -e "  ${GREEN}✓ Job is running! Extractor will run daily at 8:30 PM.${NC}"
else
    echo -e "  ${RED}⚠ Job loaded but not showing in list. Try: launchctl list | grep youtube${NC}"
fi

echo ""
echo "============================================"
echo -e "${GREEN}  Setup complete!${NC}"
echo ""
echo "  Schedule: Daily at 8:30 PM"
echo "  Playlist: PLSAj-XU9ZUhPHrwSpZKxop1mDL8NgVPkD"
echo "  Filter:   Last 3 days of uploads"
echo "  Output:   $PROJECT_DIR/queue/"
echo "  Logs:     $PROJECT_DIR/logs/"
echo ""
echo "  The Cowork 'process-youtube-queue' task runs at 9 PM"
echo "  to analyze whatever the extractor produces."
echo ""
echo "  Quick commands:"
echo "    yt              → default playlist, last 3 days"
echo "    yt 7            → default playlist, last 7 days"
echo "    yt <URL>        → custom playlist"
echo "    yt <URL> 14     → custom playlist, last 14 days"
echo ""
echo "  To uninstall:"
echo "    bash $SCRIPT_DIR/setup_youtube_cron.sh --uninstall"
echo "============================================"
