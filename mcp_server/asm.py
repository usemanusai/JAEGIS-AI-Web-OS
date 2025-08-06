"""
Architectural Synthesis Module (ASM)

Uses AI/LLM integration to analyze and synthesize architectural requirements
from processed documents and generate comprehensive build plans.
"""

import json
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

import openai
from loguru import logger
from dotenv import load_dotenv

from .ingestion import DocumentChunk

load_dotenv()


@dataclass
class BuildInstruction:
    """Represents a single build instruction."""
    type: str  # 'file', 'directory', 'command', 'dependency'
    action: str  # 'create', 'install', 'run'
    target: str  # file path, command, package name
    content: Optional[str] = None  # file content if applicable
    dependencies: List[str] = None  # prerequisite instructions
    order: int = 0  # execution order


@dataclass
class UnifiedBuildPlan:
    """Complete build plan for an application."""
    project_name: str
    description: str
    technology_stack: List[str]
    directory_structure: Dict[str, Any]
    dependencies: List[str]
    build_instructions: List[BuildInstruction]
    environment_variables: Dict[str, str]
    post_build_commands: List[str]
    metadata: Dict[str, Any]


class ArchitecturalSynthesisModule:
    """Main architectural synthesis engine."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            logger.warning("No OpenAI API key found. AI synthesis will be limited.")
        else:
            openai.api_key = self.api_key
            
        self.client = openai.OpenAI(api_key=self.api_key) if self.api_key else None
    
    def synthesize_architecture(
        self, 
        base_chunks: List[DocumentChunk], 
        overlay_chunks: Optional[List[DocumentChunk]] = None,
        output_path: Optional[str] = None
    ) -> UnifiedBuildPlan:
        """
        Synthesize architectural requirements from document chunks.
        
        Args:
            base_chunks: Primary architecture document chunks
            overlay_chunks: Optional strategic overlay chunks
            output_path: Optional path to save the build plan
            
        Returns:
            UnifiedBuildPlan object
        """
        logger.info("Starting architectural synthesis...")
        
        # Combine and analyze chunks
        all_chunks = base_chunks + (overlay_chunks or [])
        
        # Extract key information
        project_info = self._extract_project_info(all_chunks)
        tech_stack = self._extract_technology_stack(all_chunks)
        dependencies = self._extract_dependencies(all_chunks)
        file_structure = self._extract_file_structure(all_chunks)
        build_steps = self._extract_build_steps(all_chunks)
        
        # Use AI to enhance and validate the plan
        if self.client:
            enhanced_plan = self._ai_enhance_plan(all_chunks, {
                'project_info': project_info,
                'tech_stack': tech_stack,
                'dependencies': dependencies,
                'file_structure': file_structure,
                'build_steps': build_steps
            })
        else:
            enhanced_plan = self._create_basic_plan(
                project_info, tech_stack, dependencies, file_structure, build_steps
            )
        
        # Create unified build plan
        build_plan = UnifiedBuildPlan(
            project_name=enhanced_plan.get('project_name', 'generated-project'),
            description=enhanced_plan.get('description', 'AI-generated application'),
            technology_stack=enhanced_plan.get('technology_stack', tech_stack),
            directory_structure=enhanced_plan.get('directory_structure', file_structure),
            dependencies=enhanced_plan.get('dependencies', dependencies),
            build_instructions=self._create_build_instructions(enhanced_plan),
            environment_variables=enhanced_plan.get('environment_variables', {}),
            post_build_commands=enhanced_plan.get('post_build_commands', []),
            metadata={
                'generated_at': str(Path.cwd()),
                'source_files': [chunk.source_file for chunk in all_chunks],
                'total_chunks': len(all_chunks)
            }
        )
        
        # Save build plan if output path specified
        if output_path:
            self._save_build_plan(build_plan, output_path)
            
        logger.info(f"Architectural synthesis complete. Generated {len(build_plan.build_instructions)} instructions.")
        return build_plan
    
    def _extract_project_info(self, chunks: List[DocumentChunk]) -> Dict[str, str]:
        """Extract basic project information from chunks."""
        project_info = {
            'name': 'unknown-project',
            'description': 'Generated project',
            'version': '1.0.0'
        }
        
        for chunk in chunks:
            content = chunk.content.lower()
            
            # Look for project name patterns
            if 'project' in content or 'application' in content:
                lines = chunk.content.split('\n')
                for line in lines:
                    if any(keyword in line.lower() for keyword in ['project', 'app', 'application']):
                        # Extract potential project name
                        words = line.split()
                        for i, word in enumerate(words):
                            if word.lower() in ['project', 'app', 'application'] and i + 1 < len(words):
                                project_info['name'] = words[i + 1].strip(':-').lower()
                                break
                                
        return project_info
    
    def _extract_technology_stack(self, chunks: List[DocumentChunk]) -> List[str]:
        """Extract technology stack from chunks."""
        technologies = set()
        
        tech_patterns = {
            'next.js': ['next.js', 'nextjs', 'next'],
            'react': ['react'],
            'typescript': ['typescript', 'ts'],
            'tailwind': ['tailwind', 'tailwindcss'],
            'prisma': ['prisma'],
            'sqlite': ['sqlite'],
            'node.js': ['node.js', 'nodejs', 'node'],
            'python': ['python'],
            'express': ['express'],
            'fastapi': ['fastapi'],
            'django': ['django'],
            'flask': ['flask']
        }
        
        for chunk in chunks:
            content = chunk.content.lower()
            for tech, patterns in tech_patterns.items():
                if any(pattern in content for pattern in patterns):
                    technologies.add(tech)
                    
        return list(technologies)
    
    def _extract_dependencies(self, chunks: List[DocumentChunk]) -> List[str]:
        """Extract dependencies from chunks."""
        dependencies = set()
        
        for chunk in chunks:
            if chunk.chunk_type == 'command':
                content = chunk.content
                
                # Extract npm/yarn dependencies
                if 'npm install' in content or 'yarn add' in content:
                    lines = content.split('\n')
                    for line in lines:
                        if 'npm install' in line or 'yarn add' in line:
                            parts = line.split()
                            for part in parts[2:]:  # Skip 'npm install' or 'yarn add'
                                if not part.startswith('-'):
                                    dependencies.add(part)
                                    
                # Extract pip dependencies
                if 'pip install' in content:
                    lines = content.split('\n')
                    for line in lines:
                        if 'pip install' in line:
                            parts = line.split()
                            for part in parts[2:]:  # Skip 'pip install'
                                if not part.startswith('-'):
                                    dependencies.add(part)
                                    
        return list(dependencies)
    
    def _extract_file_structure(self, chunks: List[DocumentChunk]) -> Dict[str, Any]:
        """Extract file and directory structure from chunks."""
        structure = {}
        
        for chunk in chunks:
            if chunk.chunk_type in ['code', 'config']:
                content = chunk.content
                
                # Look for file path indicators
                lines = content.split('\n')
                for line in lines:
                    if line.strip().startswith('//') and ('/' in line or '\\' in line):
                        # Extract file path from comment
                        path = line.strip().replace('//', '').strip()
                        if '.' in path:  # Likely a file
                            self._add_to_structure(structure, path, 'file')
                    elif line.strip().endswith('/') or line.strip().endswith('\\'):
                        # Directory path
                        path = line.strip().rstrip('/\\')
                        self._add_to_structure(structure, path, 'directory')
                        
        return structure
    
    def _add_to_structure(self, structure: Dict[str, Any], path: str, item_type: str):
        """Add a path to the directory structure."""
        parts = path.split('/' if '/' in path else '\\')
        current = structure
        
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
            
        if parts:
            current[parts[-1]] = item_type
    
    def _extract_build_steps(self, chunks: List[DocumentChunk]) -> List[str]:
        """Extract build steps and commands from chunks."""
        build_steps = []

        for chunk in chunks:
            if chunk.chunk_type == 'command':
                lines = chunk.content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#') and not line.startswith('//'):
                        build_steps.append(line)

        return build_steps

    def _ai_enhance_plan(self, chunks: List[DocumentChunk], extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Use AI to enhance and validate the extracted build plan."""
        if not self.client:
            return self._create_basic_plan(**extracted_data)

        # Prepare context for AI
        context = self._prepare_ai_context(chunks, extracted_data)

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert software architect. Analyze the provided documentation and create a comprehensive build plan. Return a JSON object with the following structure:
{
  "project_name": "string",
  "description": "string",
  "technology_stack": ["array of technologies"],
  "directory_structure": {"nested object representing file/folder structure"},
  "dependencies": ["array of package dependencies"],
  "environment_variables": {"key": "value pairs"},
  "post_build_commands": ["array of commands to run after build"],
  "build_sequence": ["ordered array of build steps"]
}"""
                    },
                    {
                        "role": "user",
                        "content": f"Analyze this documentation and create a build plan:\n\n{context}"
                    }
                ],
                temperature=0.1,
                max_tokens=4000
            )

            ai_response = response.choices[0].message.content

            # Parse AI response
            try:
                enhanced_plan = json.loads(ai_response)
                logger.info("AI enhancement successful")
                return enhanced_plan
            except json.JSONDecodeError:
                logger.warning("AI response was not valid JSON, falling back to basic plan")
                return self._create_basic_plan(**extracted_data)

        except Exception as e:
            logger.error(f"AI enhancement failed: {e}")
            return self._create_basic_plan(**extracted_data)

    def _prepare_ai_context(self, chunks: List[DocumentChunk], extracted_data: Dict[str, Any]) -> str:
        """Prepare context string for AI analysis."""
        context_parts = []

        # Add extracted data summary
        context_parts.append("EXTRACTED DATA SUMMARY:")
        context_parts.append(f"Project Info: {extracted_data.get('project_info', {})}")
        context_parts.append(f"Technology Stack: {extracted_data.get('tech_stack', [])}")
        context_parts.append(f"Dependencies: {extracted_data.get('dependencies', [])}")
        context_parts.append("")

        # Add key chunks (limit to avoid token limits)
        context_parts.append("KEY DOCUMENTATION SECTIONS:")

        # Prioritize code and command chunks
        priority_chunks = [c for c in chunks if c.chunk_type in ['code', 'command', 'config']]
        text_chunks = [c for c in chunks if c.chunk_type == 'text']

        # Take top priority chunks and some text chunks
        selected_chunks = priority_chunks[:10] + text_chunks[:5]

        for chunk in selected_chunks:
            context_parts.append(f"--- {chunk.chunk_type.upper()} CHUNK ---")
            context_parts.append(chunk.content[:1000])  # Limit chunk size
            context_parts.append("")

        return "\n".join(context_parts)

    def _create_basic_plan(self, project_info: Dict, tech_stack: List, dependencies: List,
                          file_structure: Dict, build_steps: List) -> Dict[str, Any]:
        """Create a basic build plan without AI enhancement."""
        return {
            'project_name': project_info.get('name', 'generated-project'),
            'description': project_info.get('description', 'Generated application'),
            'technology_stack': tech_stack,
            'directory_structure': file_structure,
            'dependencies': dependencies,
            'environment_variables': {},
            'post_build_commands': [],
            'build_sequence': build_steps
        }

    def _create_build_instructions(self, plan: Dict[str, Any]) -> List[BuildInstruction]:
        """Convert plan data into structured build instructions."""
        instructions = []
        order = 0

        # 1. Create directories
        for dir_path in self._extract_directories(plan.get('directory_structure', {})):
            instructions.append(BuildInstruction(
                type='directory',
                action='create',
                target=dir_path,
                order=order
            ))
            order += 1

        # 2. Install dependencies
        for dep in plan.get('dependencies', []):
            instructions.append(BuildInstruction(
                type='dependency',
                action='install',
                target=dep,
                order=order
            ))
            order += 1

        # 3. Execute build sequence
        for command in plan.get('build_sequence', []):
            instructions.append(BuildInstruction(
                type='command',
                action='run',
                target=command,
                order=order
            ))
            order += 1

        return instructions

    def _extract_directories(self, structure: Dict[str, Any], prefix: str = '') -> List[str]:
        """Extract directory paths from nested structure."""
        directories = []

        for key, value in structure.items():
            current_path = f"{prefix}/{key}" if prefix else key

            if isinstance(value, dict):
                directories.append(current_path)
                directories.extend(self._extract_directories(value, current_path))

        return directories

    def _save_build_plan(self, build_plan: UnifiedBuildPlan, output_path: str):
        """Save the build plan to a JSON file."""
        output_file = Path(output_path) / 'UnifiedBuildPlan.json'
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict for JSON serialization
        plan_dict = asdict(build_plan)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(plan_dict, f, indent=2, default=str)

        logger.info(f"Build plan saved to: {output_file}")
