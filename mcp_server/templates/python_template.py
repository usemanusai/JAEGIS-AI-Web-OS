"""
Python Project Template

Generates Python applications with modern tooling and structure.
"""

from typing import Dict, List
from .base_template import BaseTemplate, ProjectStructure, FileTemplate, create_requirements_txt_content, create_gitignore_content, create_readme_content


class PythonTemplate(BaseTemplate):
    """Template for Python projects."""
    
    def get_framework_name(self) -> str:
        return "Python"
    
    def get_dependencies(self) -> Dict[str, List[str]]:
        """Return Python dependencies."""
        return {
            'runtime': [
                'click>=8.0.0',
                'loguru>=0.7.0',
                'python-dotenv>=1.0.0'
            ],
            'development': [
                'pytest>=7.0.0',
                'black>=23.0.0',
                'flake8>=6.0.0',
                'mypy>=1.0.0'
            ]
        }
    
    def get_project_structure(self) -> ProjectStructure:
        """Return Python project structure."""
        
        # Dependencies
        deps = self.get_dependencies()
        
        # Files
        files = [
            # Requirements.txt
            FileTemplate(
                path="requirements.txt",
                content=create_requirements_txt_content(deps['runtime']),
                is_template=False
            ),
            
            # Dev requirements
            FileTemplate(
                path="requirements-dev.txt",
                content=create_requirements_txt_content(deps['development']),
                is_template=False
            ),
            
            # Main module
            FileTemplate(
                path="main.py",
                content=self._get_main_content()
            ),
            
            # Package init
            FileTemplate(
                path=f"{self.project_name.replace('-', '_')}/__init__.py",
                content=self._get_package_init_content()
            ),
            
            # CLI module
            FileTemplate(
                path=f"{self.project_name.replace('-', '_')}/cli.py",
                content=self._get_cli_content()
            ),
            
            # Config module
            FileTemplate(
                path=f"{self.project_name.replace('-', '_')}/config.py",
                content=self._get_config_content()
            ),
            
            # Utils module
            FileTemplate(
                path=f"{self.project_name.replace('-', '_')}/utils.py",
                content=self._get_utils_content()
            ),
            
            # Tests
            FileTemplate(
                path="tests/__init__.py",
                content=""
            ),
            
            FileTemplate(
                path="tests/test_main.py",
                content=self._get_test_content()
            ),
            
            # Setup.py
            FileTemplate(
                path="setup.py",
                content=self._get_setup_content()
            ),
            
            # Environment file
            FileTemplate(
                path=".env.example",
                content=self._get_env_example_content()
            ),
            
            # Gitignore
            FileTemplate(
                path=".gitignore",
                content=create_gitignore_content([
                    "# Python",
                    "__pycache__/",
                    "*.py[cod]",
                    "*$py.class",
                    "*.so",
                    ".Python",
                    "build/",
                    "develop-eggs/",
                    "dist/",
                    "downloads/",
                    "eggs/",
                    ".eggs/",
                    "lib/",
                    "lib64/",
                    "parts/",
                    "sdist/",
                    "var/",
                    "wheels/",
                    "*.egg-info/",
                    ".installed.cfg",
                    "*.egg",
                    "",
                    "# Virtual environments",
                    "venv/",
                    "env/",
                    "ENV/",
                    "",
                    "# Environment variables",
                    ".env",
                    ".env.local",
                    "",
                    "# IDE",
                    ".vscode/",
                    ".idea/",
                    "*.swp",
                    "*.swo",
                    "",
                    "# Testing",
                    ".pytest_cache/",
                    ".coverage",
                    "htmlcov/"
                ]),
                is_template=False
            ),
            
            # README
            FileTemplate(
                path="README.md",
                content=create_readme_content(
                    self.project_name,
                    f"A Python application built with modern tooling.",
                    [
                        "Create virtual environment: `python -m venv venv`",
                        "Activate virtual environment: `source venv/bin/activate` (Linux/Mac) or `venv\\Scripts\\activate` (Windows)",
                        "Install dependencies: `pip install -r requirements.txt`",
                        "Run the application: `python main.py`"
                    ]
                ),
                is_template=False
            )
        ]
        
        return ProjectStructure(
            directories=[
                self.project_name.replace('-', '_'),
                "tests",
                "docs"
            ],
            files=files,
            dependencies=deps,
            scripts={},
            environment_variables={}
        )
    
    def _get_main_content(self) -> str:
        return '''"""
{{ project_name }} - Main Entry Point

Generated by MCP Server - Universal AI-Powered Application Foundry
"""

import os
from dotenv import load_dotenv
from loguru import logger

from {{ project_name.replace('-', '_') }}.cli import main

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Configure logging
    logger.add("logs/{{ project_name }}.log", rotation="1 day", retention="7 days")
    
    # Run the main CLI
    main()
'''
    
    def _get_package_init_content(self) -> str:
        return '''"""
{{ project_name }} Package

A Python application generated by MCP Server.
"""

__version__ = "0.1.0"
__author__ = "Generated by MCP Server"
__description__ = "{{ project_name }} - A Python application"

from .cli import main
from .config import Config
from .utils import setup_logging

__all__ = ["main", "Config", "setup_logging"]
'''
    
    def _get_cli_content(self) -> str:
        return '''"""
Command Line Interface for {{ project_name }}
"""

import click
from loguru import logger

from .config import Config
from .utils import setup_logging


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.pass_context
def main(ctx, verbose, config):
    """{{ project_name }} - A Python application."""
    
    # Ensure context object exists
    ctx.ensure_object(dict)
    
    # Setup logging
    setup_logging(verbose)
    
    # Load configuration
    ctx.obj['config'] = Config(config_file=config)
    
    logger.info(f"Starting {{ project_name }}")


@main.command()
@click.pass_context
def hello(ctx):
    """Say hello."""
    config = ctx.obj['config']
    click.echo(f"Hello from {{ project_name }}!")
    logger.info("Hello command executed")


@main.command()
@click.option('--name', '-n', default='World', help='Name to greet')
@click.pass_context
def greet(ctx, name):
    """Greet someone."""
    config = ctx.obj['config']
    message = f"Hello, {name}!"
    click.echo(message)
    logger.info(f"Greeted: {name}")


if __name__ == '__main__':
    main()
'''
    
    def _get_config_content(self) -> str:
        return '''"""
Configuration management for {{ project_name }}
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

from loguru import logger


class Config:
    """Configuration manager."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file
        self.config_data = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file and environment."""
        
        # Load from file if specified
        if self.config_file and Path(self.config_file).exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config_data = json.load(f)
                logger.info(f"Loaded configuration from {self.config_file}")
            except Exception as e:
                logger.error(f"Failed to load config file {self.config_file}: {e}")
        
        # Override with environment variables
        self._load_from_env()
    
    def _load_from_env(self):
        """Load configuration from environment variables."""
        env_prefix = "{{ project_name.upper().replace('-', '_') }}_"
        
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                config_key = key[len(env_prefix):].lower()
                self.config_data[config_key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config_data.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value."""
        self.config_data[key] = value
    
    def save(self, file_path: Optional[str] = None):
        """Save configuration to file."""
        target_file = file_path or self.config_file
        
        if not target_file:
            raise ValueError("No config file specified")
        
        try:
            with open(target_file, 'w') as f:
                json.dump(self.config_data, f, indent=2)
            logger.info(f"Configuration saved to {target_file}")
        except Exception as e:
            logger.error(f"Failed to save config to {target_file}: {e}")
            raise
'''
    
    def _get_utils_content(self) -> str:
        return '''"""
Utility functions for {{ project_name }}
"""

import sys
from pathlib import Path
from loguru import logger


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    
    # Remove default logger
    logger.remove()
    
    # Add console logger
    log_level = "DEBUG" if verbose else "INFO"
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # Add file logger
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logger.add(
        log_dir / "{{ project_name }}.log",
        level="DEBUG",
        rotation="1 day",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    )


def ensure_directory(path: Path):
    """Ensure directory exists."""
    path.mkdir(parents=True, exist_ok=True)


def read_file(file_path: Path) -> str:
    """Read file content safely."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to read file {file_path}: {e}")
        raise


def write_file(file_path: Path, content: str):
    """Write file content safely."""
    try:
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.debug(f"Written file: {file_path}")
    except Exception as e:
        logger.error(f"Failed to write file {file_path}: {e}")
        raise
'''
    
    def _get_test_content(self) -> str:
        return '''"""
Tests for {{ project_name }}
"""

import pytest
from click.testing import CliRunner

from {{ project_name.replace('-', '_') }}.cli import main


def test_hello_command():
    """Test the hello command."""
    runner = CliRunner()
    result = runner.invoke(main, ['hello'])
    
    assert result.exit_code == 0
    assert "Hello from {{ project_name }}!" in result.output


def test_greet_command():
    """Test the greet command."""
    runner = CliRunner()
    result = runner.invoke(main, ['greet', '--name', 'Test'])
    
    assert result.exit_code == 0
    assert "Hello, Test!" in result.output


def test_greet_command_default():
    """Test the greet command with default name."""
    runner = CliRunner()
    result = runner.invoke(main, ['greet'])
    
    assert result.exit_code == 0
    assert "Hello, World!" in result.output
'''
    
    def _get_setup_content(self) -> str:
        return '''"""
Setup script for {{ project_name }}
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="{{ project_name }}",
    version="0.1.0",
    author="Generated by MCP Server",
    description="A Python application generated by MCP Server",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "{{ project_name }}={{ project_name.replace('-', '_') }}.cli:main",
        ],
    },
)
'''
    
    def _get_env_example_content(self) -> str:
        return '''# Environment variables for {{ project_name }}

# Application settings
{{ project_name.upper().replace('-', '_') }}_DEBUG=false
{{ project_name.upper().replace('-', '_') }}_LOG_LEVEL=INFO

# Database (if needed)
# {{ project_name.upper().replace('-', '_') }}_DATABASE_URL=sqlite:///{{ project_name }}.db

# API Keys (if needed)
# {{ project_name.upper().replace('-', '_') }}_API_KEY=your-api-key-here

# Other settings
# {{ project_name.upper().replace('-', '_') }}_CUSTOM_SETTING=value
'''
