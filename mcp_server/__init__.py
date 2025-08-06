"""
MCP Server - Universal AI-Powered Application Foundry

A hybrid architecture system consisting of a Python backend engine
for document processing, architectural synthesis, and code generation.
"""

__version__ = "1.0.0"
__author__ = "MCP Server Team"
__description__ = "Universal AI-powered application foundry"

from .ingestion import DocumentProcessor
from .asm import ArchitecturalSynthesisModule
from .builder import CodeGenerationEngine

__all__ = [
    "DocumentProcessor",
    "ArchitecturalSynthesisModule", 
    "CodeGenerationEngine"
]
