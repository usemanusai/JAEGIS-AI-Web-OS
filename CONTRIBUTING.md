# Contributing to JAEGIS AI Web OS

Thank you for your interest in contributing to JAEGIS AI Web OS! This document provides guidelines and information for contributors.

## 🤝 Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please read and follow our [Code of Conduct](./CODE_OF_CONDUCT.md).

## 🚀 Getting Started

### Prerequisites

- **Node.js** 16+ and npm 7+
- **Python** 3.8+ with pip
- **Git** for version control
- **AI Provider API Key** (OpenAI or Anthropic) for testing

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/JAEGIS-AI-Web-OS.git
   cd JAEGIS-AI-Web-OS
   ```

2. **Install Dependencies**
   ```bash
   # Node.js dependencies
   npm install
   
   # Python dependencies
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. **Set Up Environment**
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Add your API keys
   export OPENAI_API_KEY="your-openai-key"
   export ANTHROPIC_API_KEY="your-anthropic-key"
   ```

4. **Install Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

5. **Verify Setup**
   ```bash
   # Run tests
   npm test
   python -m pytest
   
   # Test CLI
   node cli.js --help
   ```

## 📋 How to Contribute

### Types of Contributions

We welcome various types of contributions:

- 🐛 **Bug Reports**: Help us identify and fix issues
- ✨ **Feature Requests**: Suggest new features or improvements
- 📝 **Documentation**: Improve docs, examples, and tutorials
- 🔧 **Code Contributions**: Bug fixes, features, and optimizations
- 🧪 **Testing**: Add tests and improve test coverage
- 🎨 **Templates**: Create new project templates
- 🔍 **Code Review**: Review pull requests from other contributors

### Reporting Issues

Before creating an issue, please:

1. **Search existing issues** to avoid duplicates
2. **Use the appropriate template** (bug report, feature request, etc.)
3. **Provide detailed information** including:
   - Steps to reproduce (for bugs)
   - Expected vs actual behavior
   - Environment details (OS, Node.js/Python versions)
   - Sample documents (if applicable)

### Submitting Pull Requests

1. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-description
   ```

2. **Make Your Changes**
   - Follow our coding standards (see below)
   - Add tests for new functionality
   - Update documentation as needed
   - Ensure all tests pass

3. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "feat: add new template engine feature"
   ```
   
   Use [Conventional Commits](https://conventionalcommits.org/) format:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation changes
   - `test:` for test additions/changes
   - `refactor:` for code refactoring
   - `perf:` for performance improvements
   - `chore:` for maintenance tasks

4. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   
   Then create a pull request using our PR template.

## 🎯 Development Guidelines

### Code Style

#### Python Code
- **Formatter**: Black with 100-character line length
- **Linter**: Flake8 with project configuration
- **Type Hints**: Required for all public functions
- **Docstrings**: Google-style docstrings for all modules, classes, and functions

```python
def process_document(file_path: str, chunk_size: int = 4000) -> List[DocumentChunk]:
    """Process a document into semantic chunks.
    
    Args:
        file_path: Path to the document file
        chunk_size: Maximum size of each chunk in characters
        
    Returns:
        List of processed document chunks
        
    Raises:
        FileNotFoundError: If the document file doesn't exist
        ProcessingError: If document processing fails
    """
    pass
```

#### JavaScript Code
- **Formatter**: Prettier with default configuration
- **Linter**: ESLint with recommended rules
- **Style**: Modern ES6+ syntax with async/await

```javascript
/**
 * Execute Python CLI with provided arguments
 * @param {string[]} args - Command line arguments
 * @returns {Promise<void>}
 */
async function executePythonCLI(args) {
    // Implementation
}
```

### Testing Guidelines

#### Python Tests
- **Framework**: pytest with coverage reporting
- **Structure**: Mirror the source code structure in `tests/`
- **Naming**: `test_*.py` files with `test_*` functions
- **Coverage**: Aim for 85%+ test coverage

```python
import pytest
from mcp_server.enhanced_ingestion import EnhancedDocumentProcessor

class TestEnhancedDocumentProcessor:
    def test_process_markdown_file(self):
        processor = EnhancedDocumentProcessor()
        chunks = processor.process_file_enhanced("test.md")
        assert len(chunks) > 0
        assert chunks[0].content is not None
```

#### JavaScript Tests
- **Framework**: Mocha with Chai assertions
- **Structure**: Tests in `test/` directory
- **Naming**: `test-*.js` files

```javascript
const { expect } = require('chai');
const { MCPServerCLI } = require('../cli.js');

describe('CLI Wrapper', () => {
    it('should display help message', async () => {
        // Test implementation
    });
});
```

### Documentation Standards

- **README**: Keep the main README concise and focused
- **API Docs**: Document all public APIs with examples
- **Code Comments**: Explain complex logic and business rules
- **Examples**: Provide working examples for all features
- **Architecture**: Document design decisions and trade-offs

### Performance Guidelines

- **Memory Efficiency**: Handle large documents without excessive memory usage
- **Processing Speed**: Optimize for sub-30 second processing of typical documents
- **Caching**: Implement intelligent caching for repeated operations
- **Error Handling**: Graceful degradation and recovery mechanisms

## 🏗️ Architecture Overview

### Core Components

1. **Document Processing** (`enhanced_ingestion.py`)
   - Multi-format document parsing
   - Semantic chunking and content extraction
   - Entity recognition and metadata extraction

2. **AI Integration** (`enhanced_asm.py`, `ai_providers.py`)
   - Multi-provider AI client management
   - Advanced prompt engineering
   - Response validation and error handling

3. **Template System** (`templates/`)
   - Framework-specific project templates
   - Jinja2-based template rendering
   - Extensible template engine

4. **Code Generation** (`enhanced_builder.py`)
   - Project structure generation
   - File content creation and validation
   - Build process execution

5. **CLI Interface** (`enhanced_cli.py`, `cli.js`)
   - Interactive and command-line modes
   - Rich terminal UI with progress tracking
   - Cross-platform compatibility

### Adding New Features

#### New Document Format Support
1. Add parser in `enhanced_ingestion.py`
2. Update format detection logic
3. Add tests with sample documents
4. Update documentation

#### New AI Provider
1. Implement provider in `ai_providers.py`
2. Add configuration options
3. Update provider selection logic
4. Add integration tests

#### New Project Template
1. Create template class in `templates/`
2. Implement required methods
3. Add template files and structure
4. Register in template engine
5. Add examples and documentation

## 🧪 Testing

### Running Tests

```bash
# Run all tests
npm test
python -m pytest

# Run specific test suites
npm run test:cli
npm run test:integration
python -m pytest tests/unit/
python -m pytest tests/integration/

# Run with coverage
npm run test:coverage
python -m pytest --cov=mcp_server --cov-report=html
```

### Test Categories

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete workflows
- **Performance Tests**: Benchmark processing speed and memory usage

### Adding Tests

1. **Create test files** following naming conventions
2. **Mock external dependencies** (AI providers, file system)
3. **Use fixtures** for test data and setup
4. **Test edge cases** and error conditions
5. **Verify performance** for large inputs

## 📚 Documentation

### Documentation Structure

```
docs/
├── guides/           # User guides and tutorials
├── api/             # API reference documentation
├── architecture/    # System design and architecture
├── examples/        # Code examples and samples
└── development/     # Development and contribution guides
```

### Writing Documentation

- **Clear and Concise**: Use simple language and short sentences
- **Examples**: Include working code examples
- **Screenshots**: Add visual aids for UI features
- **Links**: Cross-reference related documentation
- **Updates**: Keep documentation in sync with code changes

## 🔒 Security

### Security Guidelines

- **Input Validation**: Validate all user inputs and file contents
- **API Keys**: Never commit API keys or sensitive data
- **Dependencies**: Keep dependencies updated and scan for vulnerabilities
- **Error Messages**: Don't expose sensitive information in error messages

### Reporting Security Issues

Please report security vulnerabilities to [security@usemanusai.com](mailto:security@usemanusai.com) instead of creating public issues.

## 📦 Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

1. **Update version numbers** in `package.json` and `pyproject.toml`
2. **Update CHANGELOG.md** with release notes
3. **Run full test suite** and ensure all tests pass
4. **Update documentation** for new features
5. **Create release PR** and get approval
6. **Tag release** and push to GitHub
7. **Publish to NPM and PyPI** via GitHub Actions

## 🎉 Recognition

Contributors are recognized in:
- **README.md**: Major contributors listed
- **CHANGELOG.md**: Contributors credited for each release
- **GitHub**: Contributor graphs and statistics
- **Releases**: Special thanks in release notes

## 📞 Getting Help

- **GitHub Discussions**: For questions and community support
- **GitHub Issues**: For bug reports and feature requests
- **Email**: [team@usemanusai.com](mailto:team@usemanusai.com) for direct contact
- **Documentation**: Check the docs/ directory for detailed guides

## 📄 License

By contributing to JAEGIS AI Web OS, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to JAEGIS AI Web OS! Your contributions help make this project better for everyone. 🚀
