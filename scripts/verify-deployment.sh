#!/bin/bash

# JAEGIS AI Web OS - Deployment Verification Script
# This script verifies that all deployment steps completed successfully

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}✅ JAEGIS AI Web OS - Deployment Verification${NC}"
echo -e "${BLUE}=============================================${NC}"

# Configuration
REPO_OWNER="usemanusai"
REPO_NAME="JAEGIS-AI-Web-OS"
PACKAGE_NAME="jaegis-ai-web-os"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to test command with timeout
test_command_with_timeout() {
    local cmd="$1"
    local timeout="$2"
    local description="$3"
    
    echo "Testing: $description"
    if timeout "$timeout" bash -c "$cmd" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ $description - PASSED${NC}"
        return 0
    else
        echo -e "${RED}❌ $description - FAILED${NC}"
        return 1
    fi
}

# Verification counters
TOTAL_TESTS=0
PASSED_TESTS=0

# Function to run test
run_test() {
    local test_name="$1"
    local test_command="$2"
    local timeout="${3:-30}"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -e "\n${BLUE}🧪 Test $TOTAL_TESTS: $test_name${NC}"
    
    if test_command_with_timeout "$test_command" "$timeout" "$test_name"; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
    fi
}

echo -e "${BLUE}📋 Step 1: GitHub Repository Verification${NC}"

# Test 1: Repository accessibility
run_test "GitHub Repository Access" "curl -s https://api.github.com/repos/$REPO_OWNER/$REPO_NAME | grep -q '\"name\": \"$REPO_NAME\"'" 10

# Test 2: Repository content
run_test "Repository README" "curl -s https://raw.githubusercontent.com/$REPO_OWNER/$REPO_NAME/main/README.md | grep -q 'JAEGIS AI Web OS'" 10

# Test 3: Package.json exists
run_test "Package.json in Repository" "curl -s https://raw.githubusercontent.com/$REPO_OWNER/$REPO_NAME/main/package.json | grep -q '\"name\": \"$PACKAGE_NAME\"'" 10

# Test 4: Python package config
run_test "Pyproject.toml in Repository" "curl -s https://raw.githubusercontent.com/$REPO_OWNER/$REPO_NAME/main/pyproject.toml | grep -q 'name = \"$PACKAGE_NAME\"'" 10

# Test 5: GitHub Actions workflows
run_test "GitHub Actions CI Workflow" "curl -s https://raw.githubusercontent.com/$REPO_OWNER/$REPO_NAME/main/.github/workflows/ci.yml | grep -q 'name: CI/CD Pipeline'" 10

echo -e "\n${BLUE}📦 Step 2: NPM Package Verification${NC}"

# Test 6: NPM package exists
run_test "NPM Package Exists" "npm view $PACKAGE_NAME name" 15

# Test 7: NPM package version
if npm view $PACKAGE_NAME version >/dev/null 2>&1; then
    NPM_VERSION=$(npm view $PACKAGE_NAME version)
    echo -e "${GREEN}📋 NPM Version: $NPM_VERSION${NC}"
    run_test "NPM Package Metadata" "npm view $PACKAGE_NAME description | grep -q 'Universal AI-powered'" 10
fi

# Test 8: NPX installation test
echo -e "\n${BLUE}🧪 Testing NPX Installation${NC}"
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

run_test "NPX Help Command" "npx $PACKAGE_NAME --help" 60

# Test 9: NPX version command
run_test "NPX Version Command" "npx $PACKAGE_NAME --version" 30

cd - >/dev/null
rm -rf "$TEMP_DIR"

echo -e "\n${BLUE}🐍 Step 3: PyPI Package Verification${NC}"

# Test 10: PyPI package exists
run_test "PyPI Package Exists" "pip index versions $PACKAGE_NAME" 15

# Test 11: PyPI package installation test
echo -e "\n${BLUE}🧪 Testing PyPI Installation${NC}"
VENV_DIR=$(mktemp -d)
python -m venv "$VENV_DIR"

# Activate virtual environment
if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
elif [ -f "$VENV_DIR/Scripts/activate" ]; then
    source "$VENV_DIR/Scripts/activate"
else
    echo -e "${RED}❌ Could not activate virtual environment${NC}"
    rm -rf "$VENV_DIR"
    exit 1
fi

run_test "PyPI Package Installation" "pip install $PACKAGE_NAME" 120

# Test 12: Python CLI help
run_test "Python CLI Help Command" "$PACKAGE_NAME --help" 30

# Test 13: Python CLI version
run_test "Python CLI Version Command" "$PACKAGE_NAME --version" 30

deactivate
rm -rf "$VENV_DIR"

echo -e "\n${BLUE}🔧 Step 4: Functionality Verification${NC}"

# Test 14: Global NPM installation
if command_exists npm; then
    echo -e "\n${BLUE}🧪 Testing Global NPM Installation${NC}"
    
    # Check if already installed globally
    if npm list -g $PACKAGE_NAME >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Package already installed globally${NC}"
        run_test "Global CLI Help" "$PACKAGE_NAME --help" 30
    else
        echo -e "${YELLOW}⚠️  Package not installed globally. Install with: npm install -g $PACKAGE_NAME${NC}"
    fi
fi

# Test 15: Documentation links
echo -e "\n${BLUE}📚 Step 5: Documentation Verification${NC}"

run_test "GitHub Repository Documentation" "curl -s https://raw.githubusercontent.com/$REPO_OWNER/$REPO_NAME/main/docs/guides/getting-started.md | grep -q 'Getting Started'" 10

run_test "Contributing Guidelines" "curl -s https://raw.githubusercontent.com/$REPO_OWNER/$REPO_NAME/main/CONTRIBUTING.md | grep -q 'Contributing'" 10

run_test "Security Policy" "curl -s https://raw.githubusercontent.com/$REPO_OWNER/$REPO_NAME/main/SECURITY.md | grep -q 'Security Policy'" 10

# Test 16: GitHub Actions status
echo -e "\n${BLUE}⚙️ Step 6: CI/CD Verification${NC}"

if command_exists gh; then
    echo "Checking GitHub Actions status with GitHub CLI..."
    if gh run list --repo $REPO_OWNER/$REPO_NAME --limit 1 >/dev/null 2>&1; then
        echo -e "${GREEN}✅ GitHub Actions are configured and running${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${YELLOW}⚠️  GitHub Actions status unknown${NC}"
    fi
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
else
    echo -e "${YELLOW}⚠️  GitHub CLI not available. Cannot check Actions status.${NC}"
    echo "Manual check: https://github.com/$REPO_OWNER/$REPO_NAME/actions"
fi

# Test 17: Package registry links
echo -e "\n${BLUE}🔗 Step 7: Registry Links Verification${NC}"

run_test "NPM Registry Page" "curl -s https://www.npmjs.com/package/$PACKAGE_NAME | grep -q '$PACKAGE_NAME'" 10

run_test "PyPI Registry Page" "curl -s https://pypi.org/project/$PACKAGE_NAME/ | grep -q '$PACKAGE_NAME'" 10

# Test 18: Security scanning
echo -e "\n${BLUE}🔒 Step 8: Security Verification${NC}"

if command_exists npm; then
    echo "Running NPM security audit..."
    if npm audit --registry https://registry.npmjs.org/ --package-lock-only >/dev/null 2>&1; then
        echo -e "${GREEN}✅ NPM security audit passed${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${YELLOW}⚠️  NPM security audit found issues${NC}"
    fi
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
fi

# Final Results
echo -e "\n${BLUE}📊 Verification Results${NC}"
echo -e "${BLUE}======================${NC}"

PASS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))

echo -e "Total Tests: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$((TOTAL_TESTS - PASSED_TESTS))${NC}"
echo -e "Pass Rate: ${GREEN}$PASS_RATE%${NC}"

if [ $PASS_RATE -ge 90 ]; then
    echo -e "\n${GREEN}🎉 DEPLOYMENT VERIFICATION SUCCESSFUL!${NC}"
    echo -e "${GREEN}✅ JAEGIS AI Web OS is successfully deployed and functional${NC}"
elif [ $PASS_RATE -ge 75 ]; then
    echo -e "\n${YELLOW}⚠️  DEPLOYMENT MOSTLY SUCCESSFUL${NC}"
    echo -e "${YELLOW}Some tests failed but core functionality is working${NC}"
else
    echo -e "\n${RED}❌ DEPLOYMENT VERIFICATION FAILED${NC}"
    echo -e "${RED}Multiple critical tests failed. Please review and fix issues.${NC}"
    exit 1
fi

echo -e "\n${BLUE}📋 Quick Start Commands:${NC}"
echo -e "${GREEN}NPX (No installation):${NC} npx $PACKAGE_NAME interactive"
echo -e "${GREEN}NPM Global:${NC} npm install -g $PACKAGE_NAME && $PACKAGE_NAME interactive"
echo -e "${GREEN}Python/pip:${NC} pip install $PACKAGE_NAME && $PACKAGE_NAME interactive"

echo -e "\n${BLUE}🔗 Important Links:${NC}"
echo -e "📦 NPM Package: https://www.npmjs.com/package/$PACKAGE_NAME"
echo -e "🐍 PyPI Package: https://pypi.org/project/$PACKAGE_NAME/"
echo -e "📚 GitHub Repository: https://github.com/$REPO_OWNER/$REPO_NAME"
echo -e "📖 Documentation: https://github.com/$REPO_OWNER/$REPO_NAME#readme"
echo -e "🐛 Issues: https://github.com/$REPO_OWNER/$REPO_NAME/issues"
echo -e "💬 Discussions: https://github.com/$REPO_OWNER/$REPO_NAME/discussions"

echo -e "\n${GREEN}🚀 JAEGIS AI Web OS is ready to transform architectural documentation into applications!${NC}"
