#!/bin/bash

# JAEGIS AI Web OS - Universal Deployment Launcher
# Run this script from ANYWHERE - it will find your project automatically!

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${PURPLE}🔍 JAEGIS AI Web OS - Universal Deployment Launcher${NC}"
echo -e "${PURPLE}===================================================${NC}"

# Function to find project directory
find_project_directory() {
    local current_dir="$(pwd)"
    local search_dir="$current_dir"
    
    echo -e "${BLUE}🔍 Searching for JAEGIS AI Web OS project...${NC}"
    echo -e "${BLUE}Starting search from: ${current_dir}${NC}"
    
    # Search in current directory and parent directories
    while [ "$search_dir" != "/" ]; do
        echo -e "${YELLOW}Checking: ${search_dir}${NC}"
        
        if [ -f "$search_dir/package.json" ] && [ -f "$search_dir/pyproject.toml" ] && [ -d "$search_dir/mcp_server" ]; then
            # Verify it's actually JAEGIS by checking package.json content
            if grep -q "jaegis-ai-web-os" "$search_dir/package.json" 2>/dev/null; then
                echo -e "${GREEN}✅ Found JAEGIS AI Web OS project at: ${search_dir}${NC}"
                PROJECT_DIR="$search_dir"
                return 0
            fi
        fi
        
        search_dir="$(dirname "$search_dir")"
    done
    
    # Search in common locations
    echo -e "${YELLOW}Searching in common locations...${NC}"
    
    local common_locations=(
        "$HOME/Desktop"
        "$HOME/Documents"
        "$HOME/Projects"
        "$HOME/Development"
        "$HOME/Code"
        "/c/Users/*/Desktop"
        "/c/Users/*/Documents"
        "/c/Users/*/Projects"
    )
    
    for location in "${common_locations[@]}"; do
        if [ -d "$location" ]; then
            echo -e "${YELLOW}Searching in: ${location}${NC}"
            local found_dirs=$(find "$location" -maxdepth 3 -name "package.json" -type f 2>/dev/null | while read -r pkg_file; do
                local dir=$(dirname "$pkg_file")
                if [ -f "$dir/pyproject.toml" ] && [ -d "$dir/mcp_server" ] && grep -q "jaegis-ai-web-os" "$pkg_file" 2>/dev/null; then
                    echo "$dir"
                fi
            done)
            
            if [ -n "$found_dirs" ]; then
                PROJECT_DIR=$(echo "$found_dirs" | head -1)
                echo -e "${GREEN}✅ Found JAEGIS AI Web OS project at: ${PROJECT_DIR}${NC}"
                return 0
            fi
        fi
    done
    
    return 1
}

# Try to find the project
if find_project_directory; then
    echo -e "${GREEN}✅ Project located successfully!${NC}"
    echo ""
    
    # Check if deployment script exists
    DEPLOY_SCRIPT="$PROJECT_DIR/scripts/deploy-all.sh"
    
    if [ ! -f "$DEPLOY_SCRIPT" ]; then
        echo -e "${RED}❌ Deployment script not found at: ${DEPLOY_SCRIPT}${NC}"
        echo -e "${YELLOW}Expected location: scripts/deploy-all.sh${NC}"
        exit 1
    fi
    
    # Make script executable
    chmod +x "$DEPLOY_SCRIPT"
    
    echo -e "${BLUE}🚀 Launching JAEGIS AI Web OS deployment...${NC}"
    echo -e "${BLUE}Project directory: ${PROJECT_DIR}${NC}"
    echo -e "${BLUE}Deployment script: ${DEPLOY_SCRIPT}${NC}"
    echo ""
    
    # Change to project directory and run deployment
    cd "$PROJECT_DIR"
    exec "$DEPLOY_SCRIPT"
    
else
    echo -e "${RED}❌ Could not find JAEGIS AI Web OS project directory${NC}"
    echo ""
    echo -e "${YELLOW}Please ensure you have the JAEGIS AI Web OS project with:${NC}"
    echo "  ✅ package.json (containing 'jaegis-ai-web-os')"
    echo "  ✅ pyproject.toml"
    echo "  ✅ mcp_server/ directory"
    echo "  ✅ scripts/deploy-all.sh"
    echo ""
    echo -e "${BLUE}💡 Alternative: Navigate to your project directory and run:${NC}"
    echo -e "${BLUE}   ./scripts/deploy-all.sh${NC}"
    exit 1
fi
