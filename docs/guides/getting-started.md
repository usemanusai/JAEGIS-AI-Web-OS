# Getting Started with JAEGIS AI Web OS

## 🚀 Quick Start

JAEGIS AI Web OS transforms architectural documentation into complete, production-ready applications using AI-powered analysis and code generation.

### Prerequisites

- **Node.js** 16+ (for CLI wrapper)
- **Python** 3.8+ (for core processing)
- **AI Provider API Key** (OpenAI, Anthropic, or local model)

### Installation

#### Option 1: NPX (Recommended - No Installation Required)
```bash
# Interactive mode with guided setup
npx jaegis-ai-web-os interactive

# Direct build from document
npx jaegis-ai-web-os build --base ./architecture.docx --output ./my-app
```

#### Option 2: Global Installation
```bash
# Install globally via npm
npm install -g jaegis-ai-web-os

# Verify installation
jaegis-ai-web-os --version
```

#### Option 3: Local Development
```bash
# Clone repository
git clone https://github.com/usemanusai/JAEGIS-AI-Web-OS.git
cd JAEGIS-AI-Web-OS

# Install dependencies
npm install
pip install -r requirements.txt

# Run locally
node cli.js --help
```

## 🔧 Configuration

### Environment Variables
```bash
# AI Provider Configuration (choose one or more)
export OPENAI_API_KEY="your-openai-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Optional: Preferred provider
export MCP_PREFERRED_AI_PROVIDER="openai"  # or "anthropic", "auto"

# Optional: Processing configuration
export MCP_MAX_CHUNK_SIZE="4000"
export MCP_CACHE_ENABLED="true"
export MCP_LOG_LEVEL="INFO"
```

### Configuration File (Optional)
Create `mcp_server.yaml` in your project directory:

```yaml
# AI Provider Settings
ai:
  preferred_provider: "openai"
  request_timeout: 120
  max_retries: 3

# Document Processing
processing:
  max_chunk_size: 4000
  chunk_overlap_size: 200

# Caching
cache:
  enabled: true
  max_size_mb: 1024
  ttl_hours: 24

# Logging
logging:
  level: "INFO"
  file_enabled: true
```

## 📖 Basic Usage

### Interactive Mode (Recommended for Beginners)
```bash
# Launch interactive mode
jaegis-ai-web-os interactive

# Follow the guided prompts:
# 1. Enter project name
# 2. Select architecture documents
# 3. Configure AI provider
# 4. Choose framework preference
# 5. Review and confirm
# 6. Watch your project being built!
```

### Command Line Mode
```bash
# Basic build from architecture document
jaegis-ai-web-os build \
  --base ./docs/architecture.docx \
  --output ./my-project

# Enhanced build with specific AI provider
jaegis-ai-web-os build \
  --base ./specs/requirements.md \
  --output ./my-app \
  --ai-provider openai \
  --enhanced

# Dry run to preview what will be generated
jaegis-ai-web-os build \
  --base ./design.pdf \
  --output ./preview \
  --dry-run \
  --plan-only
```

## 📄 Supported Document Formats

### Primary Formats
- **Microsoft Word** (.docx) - Full structure preservation
- **PDF** (.pdf) - Text extraction with table detection
- **Markdown** (.md) - Native support with metadata
- **Plain Text** (.txt) - Automatic encoding detection

### Extended Formats
- **PowerPoint** (.pptx) - Slide content extraction
- **Excel** (.xlsx) - Data and table extraction
- **HTML** (.html) - Structure-aware processing

### Document Requirements
- **Size**: Up to 100MB per document
- **Pages**: Up to 500 pages (recommended: 50-100 pages)
- **Language**: English (primary), other languages supported
- **Structure**: Clear headings and sections improve results

## 🏗️ Framework Support

### Frontend Frameworks
- **Next.js 15**: Full-stack React with TypeScript and Tailwind CSS
- **React 18**: Modern React with Vite and TypeScript
- **Vue.js**: (Coming soon) Progressive framework
- **Angular**: (Coming soon) Enterprise applications

### Backend Frameworks
- **Python**: CLI applications with Click and modern tooling
- **Django**: Web applications with REST API support
- **FastAPI**: High-performance APIs with documentation
- **Node.js/Express**: (Coming soon) JavaScript backends

## 🎯 Your First Project

### Step 1: Prepare Your Architecture Document
Create a document with:
- **Project Overview**: What you're building
- **Technical Requirements**: Technologies, frameworks, features
- **Architecture**: System design, components, data flow
- **Dependencies**: External services, databases, APIs

### Step 2: Run JAEGIS AI Web OS
```bash
# Interactive mode (recommended for first time)
npx jaegis-ai-web-os interactive
```

### Step 3: Follow the Guided Process
1. **Project Information**: Name, description, output directory
2. **Document Selection**: Choose your architecture document(s)
3. **Configuration**: AI provider, framework preference
4. **Preview**: Review the generated build plan
5. **Generation**: Watch your project being created

### Step 4: Explore Your Generated Project
```bash
# Navigate to your project
cd ./output/your-project-name

# For Next.js projects
npm install
npm run dev

# For Python projects
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## 📊 Example Workflows

### Workflow 1: Web Application from Requirements
```bash
# Input: requirements.docx (web app specifications)
# Output: Complete Next.js application

jaegis-ai-web-os build \
  --base ./requirements.docx \
  --output ./web-app \
  --template-preference nextjs \
  --ai-provider openai
```

### Workflow 2: API Service from Design Document
```bash
# Input: api-design.md (API specifications)
# Output: FastAPI service with documentation

jaegis-ai-web-os build \
  --base ./api-design.md \
  --output ./api-service \
  --template-preference fastapi \
  --enhanced
```

### Workflow 3: CLI Tool from Specifications
```bash
# Input: cli-specs.pdf (command-line tool requirements)
# Output: Python CLI application

jaegis-ai-web-os build \
  --base ./cli-specs.pdf \
  --output ./cli-tool \
  --template-preference python \
  --ai-provider anthropic
```

## 🔍 Troubleshooting

### Common Issues

#### "No AI provider configured"
```bash
# Solution: Set API key
export OPENAI_API_KEY="your-api-key"
# or
export ANTHROPIC_API_KEY="your-api-key"
```

#### "Document processing failed"
```bash
# Check document format and size
jaegis-ai-web-os analyze ./your-document.docx

# Try with different format
# Convert to PDF or Markdown if needed
```

#### "Build validation failed"
```bash
# Run in dry-run mode to see issues
jaegis-ai-web-os build --base ./doc.docx --dry-run

# Check logs for details
tail -f logs/mcp_server.log
```

### Getting Help

#### Built-in Help
```bash
# General help
jaegis-ai-web-os --help

# Command-specific help
jaegis-ai-web-os build --help
jaegis-ai-web-os interactive --help
```

#### System Status
```bash
# Check system status and configuration
jaegis-ai-web-os status

# Clear cache if needed
jaegis-ai-web-os clear-cache
```

#### Debug Mode
```bash
# Enable verbose logging
jaegis-ai-web-os build --base ./doc.docx --verbose --debug
```

## 📚 Next Steps

### Learn More
- [Configuration Guide](./configuration.md) - Advanced configuration options
- [API Documentation](../api/python-api.md) - Python API reference
- [Examples](../examples/) - Comprehensive examples and tutorials
- [Architecture](../architecture/) - System design and components

### Advanced Features
- [Custom Templates](../examples/custom-templates.md) - Create your own templates
- [AI Provider Configuration](./ai-providers.md) - Multi-provider setup
- [Performance Optimization](./performance.md) - Optimize for large documents
- [Enterprise Deployment](./deployment.md) - Production deployment guide

### Community
- [GitHub Issues](https://github.com/usemanusai/JAEGIS-AI-Web-OS/issues) - Bug reports and feature requests
- [GitHub Discussions](https://github.com/usemanusai/JAEGIS-AI-Web-OS/discussions) - Community discussions
- [Contributing Guide](../../CONTRIBUTING.md) - How to contribute

## 🎉 Success!

You're now ready to transform your architectural documentation into production-ready applications with JAEGIS AI Web OS!

**Pro Tip**: Start with the interactive mode to get familiar with the system, then move to command-line mode for automation and CI/CD integration.
