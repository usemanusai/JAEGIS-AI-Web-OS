"""
FastAPI Project Template

Generates FastAPI applications with modern setup.
"""

from typing import Dict, List
from .base_template import BaseTemplate, ProjectStructure, FileTemplate


class FastAPITemplate(BaseTemplate):
    """Template for FastAPI projects."""
    
    def get_framework_name(self) -> str:
        return "FastAPI"
    
    def get_dependencies(self) -> Dict[str, List[str]]:
        """Return FastAPI dependencies."""
        return {
            'runtime': [
                'fastapi>=0.100.0',
                'uvicorn>=0.23.0',
                'pydantic>=2.0.0',
                'python-dotenv>=1.0.0'
            ],
            'development': [
                'pytest>=7.0.0',
                'httpx>=0.24.0',
                'black>=23.0.0'
            ]
        }
    
    def get_project_structure(self) -> ProjectStructure:
        """Return FastAPI project structure."""
        # Basic FastAPI structure - can be expanded
        return ProjectStructure(
            directories=[
                "app",
                "app/api",
                "app/models",
                "tests"
            ],
            files=[
                FileTemplate(
                    path="main.py",
                    content="# FastAPI main.py placeholder"
                ),
                FileTemplate(
                    path="requirements.txt",
                    content="\n".join(self.get_dependencies()['runtime'])
                )
            ],
            dependencies=self.get_dependencies(),
            scripts={},
            environment_variables={}
        )
