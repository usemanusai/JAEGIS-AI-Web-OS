"""
Django Project Template

Generates Django applications with modern setup.
"""

from typing import Dict, List
from .base_template import BaseTemplate, ProjectStructure, FileTemplate


class DjangoTemplate(BaseTemplate):
    """Template for Django projects."""
    
    def get_framework_name(self) -> str:
        return "Django"
    
    def get_dependencies(self) -> Dict[str, List[str]]:
        """Return Django dependencies."""
        return {
            'runtime': [
                'django>=4.2.0',
                'djangorestframework>=3.14.0',
                'python-dotenv>=1.0.0'
            ],
            'development': [
                'pytest-django>=4.5.0',
                'black>=23.0.0',
                'flake8>=6.0.0'
            ]
        }
    
    def get_project_structure(self) -> ProjectStructure:
        """Return Django project structure."""
        # Basic Django structure - can be expanded
        return ProjectStructure(
            directories=[
                self.project_name,
                f"{self.project_name}/apps",
                "static",
                "media",
                "templates"
            ],
            files=[
                FileTemplate(
                    path="manage.py",
                    content="# Django manage.py placeholder"
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
