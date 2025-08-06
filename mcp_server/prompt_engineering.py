"""
Advanced Prompt Engineering System

Sophisticated prompt templates with chain-of-thought reasoning,
role-based prompts, and context-aware generation.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json

from .enhanced_ingestion import EnhancedDocumentChunk, ContentType


class PromptType(Enum):
    """Types of prompts for different tasks."""
    ARCHITECTURE_ANALYSIS = "architecture_analysis"
    TECHNOLOGY_EXTRACTION = "technology_extraction"
    DEPENDENCY_ANALYSIS = "dependency_analysis"
    BUILD_PLAN_GENERATION = "build_plan_generation"
    CODE_GENERATION = "code_generation"
    VALIDATION = "validation"


@dataclass
class PromptTemplate:
    """Template for generating prompts."""
    name: str
    system_prompt: str
    user_prompt_template: str
    examples: List[Dict[str, str]]
    validation_schema: Optional[Dict[str, Any]] = None


class AdvancedPromptEngine:
    """Advanced prompt engineering with chain-of-thought reasoning."""
    
    def __init__(self):
        self.templates = self._initialize_templates()
    
    def _initialize_templates(self) -> Dict[PromptType, PromptTemplate]:
        """Initialize prompt templates."""
        return {
            PromptType.ARCHITECTURE_ANALYSIS: PromptTemplate(
                name="Architecture Analysis",
                system_prompt="""You are an expert software architect with deep knowledge of modern development practices, frameworks, and architectural patterns. Your task is to analyze documentation and extract comprehensive architectural information.

You must think step-by-step and provide detailed reasoning for your analysis. Use chain-of-thought reasoning to break down complex requirements into actionable components.

Key principles:
1. Identify the core technology stack and frameworks
2. Understand the application's purpose and scope
3. Extract dependencies and their relationships
4. Identify architectural patterns and best practices
5. Consider scalability, security, and maintainability requirements""",
                
                user_prompt_template="""Analyze the following documentation and provide a comprehensive architectural analysis:

DOCUMENTATION:
{content}

Please analyze this step-by-step:

1. **Project Overview Analysis**:
   - What type of application is being described?
   - What is the main purpose and scope?
   - Who are the target users?

2. **Technology Stack Identification**:
   - What programming languages are mentioned?
   - What frameworks and libraries are specified?
   - What databases and storage solutions are used?
   - What deployment and infrastructure tools are mentioned?

3. **Architectural Patterns**:
   - What architectural patterns are evident (MVC, microservices, etc.)?
   - How is the application structured?
   - What are the main components and their relationships?

4. **Dependencies and Requirements**:
   - What external dependencies are required?
   - What are the version requirements?
   - Are there any compatibility constraints?

5. **Build and Deployment Process**:
   - What build tools are mentioned?
   - What are the deployment requirements?
   - Are there any environment-specific configurations?

Provide your analysis in the following JSON format:
{{
  "project_overview": {{
    "name": "string",
    "type": "string",
    "description": "string",
    "scope": "string"
  }},
  "technology_stack": {{
    "languages": ["array of languages"],
    "frameworks": ["array of frameworks"],
    "databases": ["array of databases"],
    "tools": ["array of tools"]
  }},
  "architecture": {{
    "patterns": ["array of patterns"],
    "components": ["array of components"],
    "structure": "string description"
  }},
  "dependencies": {{
    "runtime": ["array of runtime dependencies"],
    "development": ["array of dev dependencies"],
    "system": ["array of system requirements"]
  }},
  "build_process": {{
    "tools": ["array of build tools"],
    "steps": ["array of build steps"],
    "environments": ["array of target environments"]
  }}
}}""",
                
                examples=[
                    {
                        "input": "Build a React application with TypeScript and Tailwind CSS",
                        "output": json.dumps({
                            "project_overview": {
                                "name": "react-app",
                                "type": "web_application",
                                "description": "Modern React application with TypeScript",
                                "scope": "frontend_application"
                            },
                            "technology_stack": {
                                "languages": ["TypeScript", "JavaScript"],
                                "frameworks": ["React"],
                                "databases": [],
                                "tools": ["Tailwind CSS"]
                            }
                        })
                    }
                ]
            ),
            
            PromptType.BUILD_PLAN_GENERATION: PromptTemplate(
                name="Build Plan Generation",
                system_prompt="""You are an expert DevOps engineer and build automation specialist. Your task is to create comprehensive, executable build plans that can transform architectural requirements into working applications.

You must create detailed, step-by-step build instructions that include:
1. Directory structure creation
2. File generation with actual content
3. Dependency installation
4. Configuration setup
5. Build and deployment commands

Think through each step carefully and ensure the build plan is complete and executable.""",
                
                user_prompt_template="""Based on the following architectural analysis, create a comprehensive build plan:

ARCHITECTURAL ANALYSIS:
{architecture_analysis}

EXTRACTED CONTENT CHUNKS:
{content_chunks}

Create a detailed build plan with the following considerations:

1. **Project Structure**:
   - What directories need to be created?
   - What files need to be generated?
   - How should the project be organized?

2. **Dependencies**:
   - What packages need to be installed?
   - In what order should they be installed?
   - Are there any version constraints?

3. **Configuration**:
   - What configuration files are needed?
   - What environment variables should be set?
   - What build configurations are required?

4. **Build Process**:
   - What commands need to be executed?
   - In what order should they run?
   - What are the expected outputs?

5. **File Content**:
   - What should be the content of key files?
   - What templates should be used?
   - What customizations are needed?

Provide your build plan in this JSON format:
{{
  "project_name": "string",
  "description": "string",
  "technology_stack": ["array"],
  "directory_structure": {{
    "directories": ["array of directory paths"],
    "files": [
      {{
        "path": "string",
        "type": "string",
        "content": "string",
        "template": "string"
      }}
    ]
  }},
  "dependencies": {{
    "package_manager": "string",
    "packages": [
      {{
        "name": "string",
        "version": "string",
        "type": "runtime|development"
      }}
    ]
  }},
  "build_instructions": [
    {{
      "step": "number",
      "type": "directory|file|command|dependency",
      "action": "string",
      "target": "string",
      "content": "string (optional)",
      "description": "string"
    }}
  ],
  "environment_variables": {{
    "key": "value"
  }},
  "post_build_commands": ["array of commands"],
  "validation_steps": ["array of validation commands"]
}}""",
                
                examples=[]
            ),
            
            PromptType.CODE_GENERATION: PromptTemplate(
                name="Code Generation",
                system_prompt="""You are an expert software developer with mastery of multiple programming languages and frameworks. Your task is to generate high-quality, production-ready code based on specifications.

Generate code that follows best practices:
1. Clean, readable, and well-documented
2. Follows language and framework conventions
3. Includes proper error handling
4. Is secure and performant
5. Includes appropriate comments and documentation""",
                
                user_prompt_template="""Generate code for the following specification:

FILE PATH: {file_path}
FILE TYPE: {file_type}
FRAMEWORK: {framework}
REQUIREMENTS: {requirements}

CONTEXT:
{context}

Please generate complete, production-ready code that:
1. Follows best practices for {framework}
2. Includes proper imports and dependencies
3. Has appropriate error handling
4. Is well-documented with comments
5. Follows the project's architectural patterns

Return only the code content, no additional explanation.""",
                
                examples=[]
            )
        }
    
    def generate_prompt(self, prompt_type: PromptType, **kwargs) -> str:
        """Generate a prompt based on type and parameters."""
        template = self.templates.get(prompt_type)
        if not template:
            raise ValueError(f"Unknown prompt type: {prompt_type}")
        
        # Format the user prompt with provided parameters
        user_prompt = template.user_prompt_template.format(**kwargs)
        
        # Combine system and user prompts
        full_prompt = f"{template.system_prompt}\n\n{user_prompt}"
        
        return full_prompt
    
    def generate_architecture_analysis_prompt(self, chunks: List[EnhancedDocumentChunk]) -> str:
        """Generate prompt for architecture analysis."""
        # Prepare content from chunks
        content_parts = []
        
        for chunk in chunks:
            content_type = chunk.content_type.value if hasattr(chunk, 'content_type') else chunk.chunk_type
            content_parts.append(f"[{content_type.upper()}]\n{chunk.content}\n")
        
        content = "\n".join(content_parts)
        
        return self.generate_prompt(
            PromptType.ARCHITECTURE_ANALYSIS,
            content=content
        )
    
    def generate_build_plan_prompt(self, architecture_analysis: Dict[str, Any], 
                                 chunks: List[EnhancedDocumentChunk]) -> str:
        """Generate prompt for build plan creation."""
        # Format architecture analysis
        arch_analysis = json.dumps(architecture_analysis, indent=2)
        
        # Format content chunks
        chunk_summaries = []
        for chunk in chunks:
            chunk_info = {
                'type': chunk.content_type.value if hasattr(chunk, 'content_type') else chunk.chunk_type,
                'content_preview': chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                'entities': getattr(chunk, 'extracted_entities', {}),
                'hierarchy': getattr(chunk, 'section_hierarchy', [])
            }
            chunk_summaries.append(chunk_info)
        
        content_chunks = json.dumps(chunk_summaries, indent=2)
        
        return self.generate_prompt(
            PromptType.BUILD_PLAN_GENERATION,
            architecture_analysis=arch_analysis,
            content_chunks=content_chunks
        )
    
    def generate_code_prompt(self, file_path: str, file_type: str, framework: str, 
                           requirements: str, context: str = "") -> str:
        """Generate prompt for code generation."""
        return self.generate_prompt(
            PromptType.CODE_GENERATION,
            file_path=file_path,
            file_type=file_type,
            framework=framework,
            requirements=requirements,
            context=context
        )
    
    def validate_response_format(self, response: str, prompt_type: PromptType) -> bool:
        """Validate that response matches expected format."""
        template = self.templates.get(prompt_type)
        if not template or not template.validation_schema:
            return True
        
        try:
            if prompt_type in [PromptType.ARCHITECTURE_ANALYSIS, PromptType.BUILD_PLAN_GENERATION]:
                # Expect JSON response
                json.loads(response)
                return True
        except json.JSONDecodeError:
            return False
        
        return True
