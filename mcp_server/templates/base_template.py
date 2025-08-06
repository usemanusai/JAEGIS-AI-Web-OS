"""
Base Template System

Provides the foundation for all project templates with common
functionality and structure.
"""

import os
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
from jinja2 import Environment, BaseLoader, Template
from loguru import logger


@dataclass
class FileTemplate:
    """Represents a file template."""
    path: str
    content: str
    is_template: bool = True
    executable: bool = False
    encoding: str = 'utf-8'


@dataclass
class ProjectStructure:
    """Represents the complete project structure."""
    directories: List[str]
    files: List[FileTemplate]
    dependencies: Dict[str, List[str]]
    scripts: Dict[str, str]
    environment_variables: Dict[str, str]


class BaseTemplate(ABC):
    """Base class for all project templates."""
    
    def __init__(self, project_name: str, **kwargs):
        self.project_name = project_name
        self.config = kwargs
        self.jinja_env = Environment(loader=BaseLoader())
        
    @abstractmethod
    def get_framework_name(self) -> str:
        """Return the framework name."""
        pass
    
    @abstractmethod
    def get_project_structure(self) -> ProjectStructure:
        """Return the project structure."""
        pass
    
    @abstractmethod
    def get_dependencies(self) -> Dict[str, List[str]]:
        """Return project dependencies."""
        pass
    
    def render_template(self, template_content: str, context: Dict[str, Any]) -> str:
        """Render a template with the given context."""
        template = self.jinja_env.from_string(template_content)
        return template.render(**context, project_name=self.project_name, **self.config)
    
    def get_template_context(self) -> Dict[str, Any]:
        """Get the template context for rendering."""
        return {
            'project_name': self.project_name,
            'framework': self.get_framework_name(),
            **self.config
        }
    
    def validate_config(self) -> bool:
        """Validate the template configuration."""
        return True


class TemplateEngine:
    """Manages and provides access to project templates."""
    
    def __init__(self):
        self.templates = {}
        self._register_templates()
    
    def _register_templates(self):
        """Register available templates."""
        # Import here to avoid circular imports
        from .nextjs_template import NextJSTemplate
        from .react_template import ReactTemplate
        from .python_template import PythonTemplate
        from .django_template import DjangoTemplate
        from .fastapi_template import FastAPITemplate
        
        self.templates = {
            'nextjs': NextJSTemplate,
            'next.js': NextJSTemplate,
            'react': ReactTemplate,
            'python': PythonTemplate,
            'django': DjangoTemplate,
            'fastapi': FastAPITemplate,
        }
    
    def get_template(self, framework: str, project_name: str, **kwargs) -> Optional[BaseTemplate]:
        """Get a template instance for the specified framework."""
        framework_key = framework.lower().replace('.', '').replace('-', '')
        
        # Try exact match first
        if framework_key in self.templates:
            template_class = self.templates[framework_key]
            return template_class(project_name, **kwargs)
        
        # Try partial matches
        for key, template_class in self.templates.items():
            if framework_key in key or key in framework_key:
                logger.info(f"Using template {key} for framework {framework}")
                return template_class(project_name, **kwargs)
        
        logger.warning(f"No template found for framework: {framework}")
        return None
    
    def get_available_templates(self) -> List[str]:
        """Get list of available template names."""
        return list(self.templates.keys())
    
    def detect_framework_from_dependencies(self, dependencies: List[str]) -> Optional[str]:
        """Detect framework from dependency list."""
        dep_lower = [dep.lower() for dep in dependencies]
        
        # Framework detection patterns
        if any('next' in dep for dep in dep_lower):
            return 'nextjs'
        elif any('react' in dep for dep in dep_lower):
            return 'react'
        elif any('django' in dep for dep in dep_lower):
            return 'django'
        elif any('fastapi' in dep for dep in dep_lower):
            return 'fastapi'
        elif any(dep in ['flask', 'requests', 'sqlalchemy'] for dep in dep_lower):
            return 'python'
        
        return None
    
    def generate_project_files(self, template: BaseTemplate, output_dir: Path) -> List[str]:
        """Generate all project files using the template."""
        generated_files = []
        
        try:
            structure = template.get_project_structure()
            context = template.get_template_context()
            
            # Create directories
            for directory in structure.directories:
                dir_path = output_dir / directory
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created directory: {dir_path}")
            
            # Generate files
            for file_template in structure.files:
                file_path = output_dir / file_template.path
                
                # Ensure parent directory exists
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Render content if it's a template
                if file_template.is_template:
                    content = template.render_template(file_template.content, context)
                else:
                    content = file_template.content
                
                # Write file
                with open(file_path, 'w', encoding=file_template.encoding) as f:
                    f.write(content)
                
                # Set executable if needed
                if file_template.executable:
                    os.chmod(file_path, 0o755)
                
                generated_files.append(str(file_path))
                logger.debug(f"Generated file: {file_path}")
            
            logger.info(f"Generated {len(generated_files)} files for {template.get_framework_name()} project")
            return generated_files
            
        except Exception as e:
            logger.error(f"Failed to generate project files: {e}")
            raise


def create_package_json_content(project_name: str, dependencies: Dict[str, str], 
                              dev_dependencies: Dict[str, str], scripts: Dict[str, str]) -> str:
    """Create package.json content."""
    package_json = {
        "name": project_name,
        "version": "0.1.0",
        "private": True,
        "scripts": scripts,
        "dependencies": dependencies,
        "devDependencies": dev_dependencies
    }
    return json.dumps(package_json, indent=2)


def create_requirements_txt_content(dependencies: List[str]) -> str:
    """Create requirements.txt content."""
    return '\n'.join(dependencies)


def create_dockerfile_content(base_image: str, port: int, commands: List[str]) -> str:
    """Create Dockerfile content."""
    dockerfile_lines = [
        f"FROM {base_image}",
        "",
        "WORKDIR /app",
        "",
        "COPY . .",
        ""
    ]
    
    dockerfile_lines.extend(commands)
    dockerfile_lines.extend([
        "",
        f"EXPOSE {port}",
        ""
    ])
    
    return '\n'.join(dockerfile_lines)


def create_gitignore_content(patterns: List[str]) -> str:
    """Create .gitignore content."""
    return '\n'.join(patterns)


def create_readme_content(project_name: str, description: str, 
                         setup_instructions: List[str]) -> str:
    """Create README.md content."""
    readme_lines = [
        f"# {project_name}",
        "",
        description,
        "",
        "## Setup",
        ""
    ]
    
    for i, instruction in enumerate(setup_instructions, 1):
        readme_lines.append(f"{i}. {instruction}")
    
    readme_lines.extend([
        "",
        "## Development",
        "",
        "Follow the setup instructions above to get started with development.",
        "",
        f"Generated by MCP Server - Universal AI-Powered Application Foundry"
    ])
    
    return '\n'.join(readme_lines)
