"""
Template System for Code Generation

Provides templates for various frameworks and project types.
"""

from .base_template import BaseTemplate, TemplateEngine
from .nextjs_template import NextJSTemplate
from .react_template import ReactTemplate
from .python_template import PythonTemplate
from .django_template import DjangoTemplate
from .fastapi_template import FastAPITemplate

__all__ = [
    'BaseTemplate',
    'TemplateEngine', 
    'NextJSTemplate',
    'ReactTemplate',
    'PythonTemplate',
    'DjangoTemplate',
    'FastAPITemplate'
]
