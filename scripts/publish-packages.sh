#!/bin/bash

# JAEGIS AI Web OS - Package Publishing Script
# This script automates publishing to NPM and PyPI registries

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📦 JAEGIS AI Web OS - Package Publishing Script${NC}"
echo -e "${BLUE}===============================================${NC}"

# Check if we're in the right directory
if [ ! -f "package.json" ] || [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}❌ Error: Please run this script from the project root directory${NC}"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check required tools
echo -e "${BLUE}🔍 Checking required tools...${NC}"

if ! command_exists node; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    exit 1
fi

if ! command_exists npm; then
    echo -e "${RED}❌ NPM is not installed${NC}"
    exit 1
fi

if ! command_exists python; then
    echo -e "${RED}❌ Python is not installed${NC}"
    exit 1
fi

if ! command_exists pip; then
    echo -e "${RED}❌ pip is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All required tools are available${NC}"

# Get package version
PACKAGE_VERSION=$(node -p "require('./package.json').version")
echo -e "${BLUE}📋 Package Version: ${PACKAGE_VERSION}${NC}"

# Pre-publication tests
echo -e "${BLUE}🧪 Step 1: Running Pre-Publication Tests${NC}"

echo "Running NPM tests..."
if npm test; then
    echo -e "${GREEN}✅ NPM tests passed${NC}"
else
    echo -e "${RED}❌ NPM tests failed${NC}"
    exit 1
fi

echo "Running Python tests..."
if python -m pytest tests/ -v; then
    echo -e "${GREEN}✅ Python tests passed${NC}"
else
    echo -e "${YELLOW}⚠️  Python tests failed or pytest not available${NC}"
    echo "Continuing with publication..."
fi

# Lint checks
echo "Running lint checks..."
if npm run lint; then
    echo -e "${GREEN}✅ Lint checks passed${NC}"
else
    echo -e "${YELLOW}⚠️  Lint checks failed${NC}"
    echo "Continuing with publication..."
fi

# Security audit
echo "Running security audit..."
if npm audit --audit-level=moderate; then
    echo -e "${GREEN}✅ Security audit passed${NC}"
else
    echo -e "${YELLOW}⚠️  Security audit found issues${NC}"
    echo "Please review security issues before publishing"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Build packages
echo -e "${BLUE}🔨 Step 2: Building Packages${NC}"

echo "Building Python package..."
if command_exists python && python -c "import build" 2>/dev/null; then
    python -m build
    echo -e "${GREEN}✅ Python package built${NC}"
else
    echo "Installing build tools..."
    pip install build twine
    python -m build
    echo -e "${GREEN}✅ Python package built${NC}"
fi

echo "Preparing NPM package..."
if npm pack; then
    echo -e "${GREEN}✅ NPM package prepared${NC}"
else
    echo -e "${RED}❌ Failed to prepare NPM package${NC}"
    exit 1
fi

# Test local installation
echo -e "${BLUE}🧪 Step 3: Testing Local Installation${NC}"

echo "Testing NPM package installation..."
TARBALL="jaegis-ai-web-os-${PACKAGE_VERSION}.tgz"
if [ -f "$TARBALL" ]; then
    # Test installation in a temporary directory
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"
    
    if npm install "$OLDPWD/$TARBALL"; then
        echo -e "${GREEN}✅ NPM package installs correctly${NC}"
        
        # Test CLI
        if ./node_modules/.bin/jaegis-ai-web-os --help >/dev/null 2>&1; then
            echo -e "${GREEN}✅ CLI works correctly${NC}"
        else
            echo -e "${YELLOW}⚠️  CLI test failed${NC}"
        fi
    else
        echo -e "${RED}❌ NPM package installation failed${NC}"
        cd "$OLDPWD"
        exit 1
    fi
    
    cd "$OLDPWD"
    rm -rf "$TEMP_DIR"
else
    echo -e "${RED}❌ NPM tarball not found${NC}"
    exit 1
fi

echo "Testing Python package installation..."
WHEEL_FILE=$(find dist/ -name "*.whl" | head -1)
if [ -f "$WHEEL_FILE" ]; then
    # Create virtual environment for testing
    VENV_DIR=$(mktemp -d)
    python -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate" 2>/dev/null || source "$VENV_DIR/Scripts/activate"
    
    if pip install "$WHEEL_FILE"; then
        echo -e "${GREEN}✅ Python package installs correctly${NC}"
        
        # Test CLI
        if jaegis-ai-web-os --help >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Python CLI works correctly${NC}"
        else
            echo -e "${YELLOW}⚠️  Python CLI test failed${NC}"
        fi
    else
        echo -e "${RED}❌ Python package installation failed${NC}"
        deactivate
        rm -rf "$VENV_DIR"
        exit 1
    fi
    
    deactivate
    rm -rf "$VENV_DIR"
else
    echo -e "${RED}❌ Python wheel file not found${NC}"
    exit 1
fi

# Check authentication
echo -e "${BLUE}🔐 Step 4: Checking Authentication${NC}"

echo "Checking NPM authentication..."
if npm whoami >/dev/null 2>&1; then
    NPM_USER=$(npm whoami)
    echo -e "${GREEN}✅ Logged in to NPM as: ${NPM_USER}${NC}"
else
    echo -e "${YELLOW}⚠️  Not logged in to NPM${NC}"
    echo "Please run: npm login"
    read -p "Continue with NPM login now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        npm login
    else
        echo "Skipping NPM publication"
        SKIP_NPM=true
    fi
fi

echo "Checking PyPI authentication..."
if python -c "import keyring; keyring.get_password('https://upload.pypi.org/legacy/', '__token__')" 2>/dev/null; then
    echo -e "${GREEN}✅ PyPI credentials found${NC}"
elif [ -f "$HOME/.pypirc" ]; then
    echo -e "${GREEN}✅ PyPI configuration found${NC}"
else
    echo -e "${YELLOW}⚠️  PyPI credentials not found${NC}"
    echo "Please configure PyPI credentials:"
    echo "1. Create API token at: https://pypi.org/manage/account/token/"
    echo "2. Run: python -m twine upload --repository testpypi dist/* (for testing)"
    echo "3. Or configure ~/.pypirc with your credentials"
    read -p "Continue with PyPI publication? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping PyPI publication"
        SKIP_PYPI=true
    fi
fi

# Publish to NPM
if [ "$SKIP_NPM" != true ]; then
    echo -e "${BLUE}📤 Step 5: Publishing to NPM${NC}"
    
    # Check if package already exists
    if npm view jaegis-ai-web-os@$PACKAGE_VERSION >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Package version ${PACKAGE_VERSION} already exists on NPM${NC}"
        read -p "Continue anyway? This will fail. (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Skipping NPM publication"
            SKIP_NPM=true
        fi
    fi
    
    if [ "$SKIP_NPM" != true ]; then
        echo "Publishing to NPM..."
        if npm publish; then
            echo -e "${GREEN}✅ Successfully published to NPM!${NC}"
            echo -e "${GREEN}📦 Package available at: https://www.npmjs.com/package/jaegis-ai-web-os${NC}"
        else
            echo -e "${RED}❌ Failed to publish to NPM${NC}"
            exit 1
        fi
    fi
else
    echo -e "${YELLOW}⏭️  Skipping NPM publication${NC}"
fi

# Publish to PyPI
if [ "$SKIP_PYPI" != true ]; then
    echo -e "${BLUE}📤 Step 6: Publishing to PyPI${NC}"
    
    echo "Publishing to PyPI..."
    if python -m twine upload dist/*; then
        echo -e "${GREEN}✅ Successfully published to PyPI!${NC}"
        echo -e "${GREEN}📦 Package available at: https://pypi.org/project/jaegis-ai-web-os/${NC}"
    else
        echo -e "${RED}❌ Failed to publish to PyPI${NC}"
        echo "You may need to:"
        echo "1. Configure PyPI credentials"
        echo "2. Check if the version already exists"
        echo "3. Verify package metadata"
        exit 1
    fi
else
    echo -e "${YELLOW}⏭️  Skipping PyPI publication${NC}"
fi

# Cleanup
echo -e "${BLUE}🧹 Step 7: Cleanup${NC}"
echo "Cleaning up build artifacts..."
rm -f jaegis-ai-web-os-*.tgz

echo -e "${GREEN}🎉 Package publication completed successfully!${NC}"
echo -e "${BLUE}📋 Publication Summary:${NC}"
echo "Package Version: $PACKAGE_VERSION"

if [ "$SKIP_NPM" != true ]; then
    echo -e "${GREEN}✅ NPM: https://www.npmjs.com/package/jaegis-ai-web-os${NC}"
    echo "   Install with: npm install -g jaegis-ai-web-os"
    echo "   Use with: npx jaegis-ai-web-os interactive"
fi

if [ "$SKIP_PYPI" != true ]; then
    echo -e "${GREEN}✅ PyPI: https://pypi.org/project/jaegis-ai-web-os/${NC}"
    echo "   Install with: pip install jaegis-ai-web-os"
    echo "   Use with: jaegis-ai-web-os --help"
fi

echo ""
echo -e "${BLUE}🔄 Next Steps:${NC}"
echo "1. Run: ./scripts/verify-deployment.sh (to verify installations work)"
echo "2. Create GitHub release: https://github.com/usemanusai/JAEGIS-AI-Web-OS/releases/new"
echo "3. Announce the release to the community"
echo "4. Monitor for user feedback and issues"
