#!/bin/bash

# JAEGIS AI Web OS - Repository Configuration Script
# This script configures GitHub repository settings, branch protection, and security

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}⚙️ JAEGIS AI Web OS - Repository Configuration${NC}"
echo -e "${BLUE}=============================================${NC}"

# Configuration
REPO_OWNER="usemanusai"
REPO_NAME="JAEGIS-AI-Web-OS"
REPO_FULL="$REPO_OWNER/$REPO_NAME"

# Check if GitHub CLI is available
if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ GitHub CLI (gh) is required but not installed${NC}"
    echo "Please install GitHub CLI: https://cli.github.com/"
    echo ""
    echo -e "${YELLOW}Alternative: Configure manually at https://github.com/$REPO_FULL/settings${NC}"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo -e "${RED}❌ Not authenticated with GitHub CLI${NC}"
    echo "Please run: gh auth login"
    exit 1
fi

echo -e "${GREEN}✅ GitHub CLI is available and authenticated${NC}"

echo -e "${BLUE}📋 Step 1: Basic Repository Configuration${NC}"

# Set repository description
echo "Setting repository description..."
if gh repo edit $REPO_FULL --description "Universal AI-powered application foundry that transforms architectural documentation into complete, production-ready applications"; then
    echo -e "${GREEN}✅ Repository description set${NC}"
else
    echo -e "${RED}❌ Failed to set repository description${NC}"
fi

# Set repository website
echo "Setting repository website..."
if gh repo edit $REPO_FULL --homepage "https://github.com/$REPO_FULL"; then
    echo -e "${GREEN}✅ Repository website set${NC}"
else
    echo -e "${RED}❌ Failed to set repository website${NC}"
fi

# Add topics
echo "Adding repository topics..."
TOPICS="ai,artificial-intelligence,code-generation,documentation,automation,nextjs,react,python,django,fastapi,enterprise,ai-powered,application-generator,cli-tool,developer-tools,openai,anthropic,gpt-4,claude"

if gh repo edit $REPO_FULL --add-topic $TOPICS; then
    echo -e "${GREEN}✅ Repository topics added${NC}"
else
    echo -e "${RED}❌ Failed to add repository topics${NC}"
fi

echo -e "${BLUE}🔧 Step 2: Repository Features Configuration${NC}"

# Enable repository features
echo "Enabling repository features..."

if gh repo edit $REPO_FULL --enable-issues; then
    echo -e "${GREEN}✅ Issues enabled${NC}"
else
    echo -e "${YELLOW}⚠️  Failed to enable issues${NC}"
fi

if gh repo edit $REPO_FULL --enable-projects; then
    echo -e "${GREEN}✅ Projects enabled${NC}"
else
    echo -e "${YELLOW}⚠️  Failed to enable projects${NC}"
fi

if gh repo edit $REPO_FULL --enable-wiki; then
    echo -e "${GREEN}✅ Wiki enabled${NC}"
else
    echo -e "${YELLOW}⚠️  Failed to enable wiki${NC}"
fi

# Note: Discussions might need to be enabled manually
echo -e "${YELLOW}📝 Note: Enable Discussions manually at https://github.com/$REPO_FULL/settings${NC}"

echo -e "${BLUE}🛡️ Step 3: Branch Protection Configuration${NC}"

# Configure branch protection for main branch
echo "Setting up branch protection for 'main' branch..."

# Create branch protection rule
PROTECTION_CONFIG='{
  "required_status_checks": {
    "strict": true,
    "contexts": ["CI/CD Pipeline"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}'

# Use GitHub API to set branch protection (gh CLI doesn't have full support)
if curl -s -X PUT \
  -H "Authorization: token $(gh auth token)" \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/repos/$REPO_FULL/branches/main/protection" \
  -d "$PROTECTION_CONFIG" > /dev/null; then
    echo -e "${GREEN}✅ Branch protection configured for 'main'${NC}"
else
    echo -e "${YELLOW}⚠️  Failed to configure branch protection automatically${NC}"
    echo -e "${YELLOW}📝 Please configure manually at: https://github.com/$REPO_FULL/settings/branches${NC}"
    echo "Recommended settings:"
    echo "  - Require pull request reviews before merging"
    echo "  - Require status checks to pass before merging"
    echo "  - Require branches to be up to date before merging"
    echo "  - Include administrators"
    echo "  - Do not allow force pushes"
    echo "  - Do not allow deletions"
fi

echo -e "${BLUE}🔒 Step 4: Security Configuration${NC}"

# Enable security features using GitHub API
echo "Configuring security features..."

# Enable vulnerability alerts
if curl -s -X PUT \
  -H "Authorization: token $(gh auth token)" \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/repos/$REPO_FULL/vulnerability-alerts" > /dev/null; then
    echo -e "${GREEN}✅ Vulnerability alerts enabled${NC}"
else
    echo -e "${YELLOW}⚠️  Failed to enable vulnerability alerts${NC}"
fi

# Enable automated security fixes
if curl -s -X PUT \
  -H "Authorization: token $(gh auth token)" \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/repos/$REPO_FULL/automated-security-fixes" > /dev/null; then
    echo -e "${GREEN}✅ Automated security fixes enabled${NC}"
else
    echo -e "${YELLOW}⚠️  Failed to enable automated security fixes${NC}"
fi

echo -e "${BLUE}🔑 Step 5: Repository Secrets Configuration${NC}"

echo -e "${YELLOW}📝 Manual configuration required for repository secrets:${NC}"
echo "Go to: https://github.com/$REPO_FULL/settings/secrets/actions"
echo ""
echo "Add the following secrets for package publishing:"
echo "1. NPM_TOKEN - Your NPM authentication token"
echo "   - Get from: https://www.npmjs.com/settings/tokens"
echo "   - Type: Automation token"
echo ""
echo "2. PYPI_TOKEN - Your PyPI API token"
echo "   - Get from: https://pypi.org/manage/account/token/"
echo "   - Scope: Entire account or specific project"
echo ""
echo "Optional secrets for enhanced features:"
echo "3. DOCKER_USERNAME - Docker Hub username"
echo "4. DOCKER_PASSWORD - Docker Hub password or token"
echo "5. CODECOV_TOKEN - Codecov token for coverage reporting"

echo -e "${BLUE}📊 Step 6: Repository Insights Configuration${NC}"

# Configure repository insights
echo "Configuring repository insights..."

# Enable dependency graph (usually enabled by default)
echo -e "${GREEN}✅ Dependency graph should be enabled by default${NC}"

# Note about additional configurations
echo -e "${YELLOW}📝 Additional manual configurations recommended:${NC}"
echo "1. Go to: https://github.com/$REPO_FULL/settings/security_analysis"
echo "2. Enable: Dependency graph (if not already enabled)"
echo "3. Enable: Dependabot alerts"
echo "4. Enable: Dependabot security updates"
echo "5. Consider enabling: Code scanning alerts"

echo -e "${BLUE}🏷️ Step 7: Labels Configuration${NC}"

# Create custom labels for the project
echo "Creating custom labels..."

LABELS=(
    "ai-enhancement:🤖:0052cc:Improvements to AI functionality"
    "template:📄:fef2c0:Template system related"
    "documentation:📚:0075ca:Documentation improvements"
    "security:🔒:d73a4a:Security related issues"
    "performance:⚡:fbca04:Performance improvements"
    "enterprise:🏢:5319e7:Enterprise features"
    "cli:💻:1d76db:Command line interface"
    "python:🐍:3776ab:Python backend related"
    "nodejs:💚:68a063:Node.js related"
    "needs-triage:🔍:ffffff:Needs initial review"
)

for label in "${LABELS[@]}"; do
    IFS=':' read -r name emoji color description <<< "$label"
    
    if gh label create "$name" --description "$description" --color "$color" --repo "$REPO_FULL" 2>/dev/null; then
        echo -e "${GREEN}✅ Created label: $name $emoji${NC}"
    else
        echo -e "${YELLOW}⚠️  Label '$name' might already exist${NC}"
    fi
done

echo -e "${BLUE}📋 Step 8: Issue Templates Verification${NC}"

# Verify issue templates are in place
TEMPLATES=(
    ".github/ISSUE_TEMPLATE/bug_report.md"
    ".github/ISSUE_TEMPLATE/feature_request.md"
    ".github/ISSUE_TEMPLATE/security_report.md"
)

for template in "${TEMPLATES[@]}"; do
    if [ -f "$template" ]; then
        echo -e "${GREEN}✅ $template exists${NC}"
    else
        echo -e "${RED}❌ Missing: $template${NC}"
    fi
done

# Check PR template
if [ -f ".github/PULL_REQUEST_TEMPLATE.md" ]; then
    echo -e "${GREEN}✅ Pull request template exists${NC}"
else
    echo -e "${RED}❌ Missing: .github/PULL_REQUEST_TEMPLATE.md${NC}"
fi

echo -e "${BLUE}🎯 Step 9: GitHub Actions Verification${NC}"

# Check if workflows exist
WORKFLOWS=(
    ".github/workflows/ci.yml"
    ".github/workflows/security-audit.yml"
    ".github/workflows/dependency-update.yml"
    ".github/workflows/repository-intelligence.yml"
)

for workflow in "${WORKFLOWS[@]}"; do
    if [ -f "$workflow" ]; then
        echo -e "${GREEN}✅ $workflow exists${NC}"
    else
        echo -e "${RED}❌ Missing: $workflow${NC}"
    fi
done

echo -e "${BLUE}📈 Step 10: Repository Analytics Setup${NC}"

echo -e "${YELLOW}📝 Manual setup recommended for analytics:${NC}"
echo "1. Go to: https://github.com/$REPO_FULL/pulse"
echo "2. Monitor: Contributors, commits, code frequency"
echo "3. Set up: GitHub Insights for traffic analytics"
echo "4. Consider: Third-party analytics tools"

echo -e "${GREEN}🎉 Repository Configuration Completed!${NC}"
echo -e "${BLUE}📋 Configuration Summary:${NC}"
echo "✅ Repository description and topics set"
echo "✅ Repository features enabled (Issues, Projects, Wiki)"
echo "✅ Branch protection configured"
echo "✅ Security features enabled"
echo "✅ Custom labels created"
echo "✅ Templates and workflows verified"

echo -e "\n${BLUE}🔄 Next Steps:${NC}"
echo "1. Add repository secrets manually (NPM_TOKEN, PYPI_TOKEN)"
echo "2. Enable Discussions if desired"
echo "3. Configure additional security settings"
echo "4. Set up team permissions if working with collaborators"
echo "5. Run: ./scripts/publish-packages.sh (to publish packages)"

echo -e "\n${GREEN}Repository URL: https://github.com/$REPO_FULL${NC}"
echo -e "${GREEN}Settings URL: https://github.com/$REPO_FULL/settings${NC}"
