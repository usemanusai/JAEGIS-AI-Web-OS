"""
Enhanced Architectural Synthesis Module

Advanced AI-powered architectural synthesis with multi-provider support,
sophisticated prompt engineering, and comprehensive validation.
"""

import json
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

from loguru import logger
from dotenv import load_dotenv

from .enhanced_ingestion import EnhancedDocumentChunk
from .ai_providers import AIProviderManager, AIProvider, AIResponse
from .prompt_engineering import AdvancedPromptEngine, PromptType
from .asm import UnifiedBuildPlan, BuildInstruction

load_dotenv()


@dataclass
class EnhancedBuildPlan(UnifiedBuildPlan):
    """Enhanced build plan with additional metadata."""
    ai_analysis: Dict[str, Any]
    confidence_score: float
    provider_used: str
    generation_metadata: Dict[str, Any]
    validation_results: Dict[str, Any]


class EnhancedArchitecturalSynthesisModule:
    """Enhanced ASM with sophisticated AI integration."""
    
    def __init__(self, preferred_provider: Optional[AIProvider] = None):
        self.ai_manager = AIProviderManager()
        self.prompt_engine = AdvancedPromptEngine()
        self.preferred_provider = preferred_provider
        
        # Get available providers
        self.available_providers = self.ai_manager.get_available_providers()
        logger.info(f"Available AI providers: {[p.value for p in self.available_providers]}")
        
        if not self.available_providers:
            logger.warning("No AI providers available. Falling back to rule-based processing.")
    
    def synthesize_architecture_enhanced(
        self, 
        base_chunks: List[EnhancedDocumentChunk], 
        overlay_chunks: Optional[List[EnhancedDocumentChunk]] = None,
        output_path: Optional[str] = None
    ) -> EnhancedBuildPlan:
        """
        Enhanced architectural synthesis with AI-powered analysis.
        
        Args:
            base_chunks: Primary architecture document chunks
            overlay_chunks: Optional strategic overlay chunks
            output_path: Optional path to save the build plan
            
        Returns:
            EnhancedBuildPlan object
        """
        logger.info("Starting enhanced architectural synthesis...")
        
        # Combine and analyze chunks
        all_chunks = base_chunks + (overlay_chunks or [])
        
        # Step 1: AI-powered architectural analysis
        ai_analysis = self._perform_ai_analysis(all_chunks)
        
        # Step 2: Generate comprehensive build plan
        build_plan_data = self._generate_build_plan(ai_analysis, all_chunks)
        
        # Step 3: Validate and enhance the plan
        validation_results = self._validate_build_plan(build_plan_data)
        
        # Step 4: Create enhanced build plan
        enhanced_plan = self._create_enhanced_build_plan(
            build_plan_data, ai_analysis, validation_results, all_chunks
        )
        
        # Step 5: Save build plan if output path specified
        if output_path:
            self._save_enhanced_build_plan(enhanced_plan, output_path)
            
        logger.info(f"Enhanced architectural synthesis complete. Generated {len(enhanced_plan.build_instructions)} instructions.")
        return enhanced_plan
    
    def _perform_ai_analysis(self, chunks: List[EnhancedDocumentChunk]) -> Dict[str, Any]:
        """Perform AI-powered architectural analysis."""
        if not self.available_providers:
            logger.warning("No AI providers available. Using rule-based analysis.")
            return self._fallback_analysis(chunks)
        
        try:
            # Generate analysis prompt
            prompt = self.prompt_engine.generate_architecture_analysis_prompt(chunks)
            
            # Get AI response with fallback
            response = self.ai_manager.generate_with_fallback(
                prompt=prompt,
                preferred_provider=self.preferred_provider,
                temperature=0.1,
                max_tokens=4000
            )
            
            # Validate and parse response
            if self.prompt_engine.validate_response_format(response.content, PromptType.ARCHITECTURE_ANALYSIS):
                try:
                    analysis = json.loads(response.content)
                    analysis['_ai_metadata'] = {
                        'provider': response.provider.value,
                        'model': response.model,
                        'tokens_used': response.tokens_used,
                        'confidence': response.confidence_score
                    }
                    return analysis
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse AI analysis response: {e}")
                    return self._fallback_analysis(chunks)
            else:
                logger.warning("AI response format validation failed. Using fallback.")
                return self._fallback_analysis(chunks)
                
        except Exception as e:
            logger.error(f"AI analysis failed: {e}. Using fallback.")
            return self._fallback_analysis(chunks)
    
    def _generate_build_plan(self, ai_analysis: Dict[str, Any], 
                           chunks: List[EnhancedDocumentChunk]) -> Dict[str, Any]:
        """Generate comprehensive build plan using AI."""
        if not self.available_providers:
            return self._fallback_build_plan(ai_analysis, chunks)
        
        try:
            # Generate build plan prompt
            prompt = self.prompt_engine.generate_build_plan_prompt(ai_analysis, chunks)
            
            # Get AI response
            response = self.ai_manager.generate_with_fallback(
                prompt=prompt,
                preferred_provider=self.preferred_provider,
                temperature=0.1,
                max_tokens=6000
            )
            
            # Validate and parse response
            if self.prompt_engine.validate_response_format(response.content, PromptType.BUILD_PLAN_GENERATION):
                try:
                    build_plan = json.loads(response.content)
                    build_plan['_ai_metadata'] = {
                        'provider': response.provider.value,
                        'model': response.model,
                        'tokens_used': response.tokens_used,
                        'confidence': response.confidence_score
                    }
                    return build_plan
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse build plan response: {e}")
                    return self._fallback_build_plan(ai_analysis, chunks)
            else:
                logger.warning("Build plan response format validation failed. Using fallback.")
                return self._fallback_build_plan(ai_analysis, chunks)
                
        except Exception as e:
            logger.error(f"AI build plan generation failed: {e}. Using fallback.")
            return self._fallback_build_plan(ai_analysis, chunks)
    
    def _validate_build_plan(self, build_plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the generated build plan."""
        validation_results = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'suggestions': []
        }
        
        # Check required fields
        required_fields = ['project_name', 'technology_stack', 'build_instructions']
        for field in required_fields:
            if field not in build_plan_data:
                validation_results['errors'].append(f"Missing required field: {field}")
                validation_results['is_valid'] = False
        
        # Validate build instructions
        if 'build_instructions' in build_plan_data:
            instructions = build_plan_data['build_instructions']
            if not isinstance(instructions, list):
                validation_results['errors'].append("build_instructions must be a list")
                validation_results['is_valid'] = False
            else:
                for i, instruction in enumerate(instructions):
                    if not isinstance(instruction, dict):
                        validation_results['errors'].append(f"Instruction {i} must be a dictionary")
                        continue
                    
                    required_instruction_fields = ['type', 'action', 'target']
                    for field in required_instruction_fields:
                        if field not in instruction:
                            validation_results['warnings'].append(
                                f"Instruction {i} missing field: {field}"
                            )
        
        # Validate technology stack
        if 'technology_stack' in build_plan_data:
            tech_stack = build_plan_data['technology_stack']
            if not isinstance(tech_stack, list):
                validation_results['warnings'].append("technology_stack should be a list")
        
        # Check for common issues
        if 'dependencies' in build_plan_data:
            deps = build_plan_data['dependencies']
            if isinstance(deps, dict) and 'packages' in deps:
                packages = deps['packages']
                if len(packages) == 0:
                    validation_results['warnings'].append("No dependencies specified")
        
        return validation_results
    
    def _create_enhanced_build_plan(self, build_plan_data: Dict[str, Any], 
                                  ai_analysis: Dict[str, Any],
                                  validation_results: Dict[str, Any],
                                  chunks: List[EnhancedDocumentChunk]) -> EnhancedBuildPlan:
        """Create enhanced build plan object."""
        
        # Convert build instructions to BuildInstruction objects
        instructions = []
        if 'build_instructions' in build_plan_data:
            for i, inst_data in enumerate(build_plan_data['build_instructions']):
                instructions.append(BuildInstruction(
                    type=inst_data.get('type', 'command'),
                    action=inst_data.get('action', 'run'),
                    target=inst_data.get('target', ''),
                    content=inst_data.get('content'),
                    dependencies=inst_data.get('dependencies'),
                    order=inst_data.get('step', i)
                ))
        
        # Calculate overall confidence score
        ai_confidence = ai_analysis.get('_ai_metadata', {}).get('confidence', 0.5)
        validation_confidence = 1.0 if validation_results['is_valid'] else 0.3
        overall_confidence = (ai_confidence + validation_confidence) / 2
        
        # Extract provider information
        provider_used = ai_analysis.get('_ai_metadata', {}).get('provider', 'fallback')
        
        return EnhancedBuildPlan(
            project_name=build_plan_data.get('project_name', 'generated-project'),
            description=build_plan_data.get('description', 'AI-generated application'),
            technology_stack=build_plan_data.get('technology_stack', []),
            directory_structure=build_plan_data.get('directory_structure', {}),
            dependencies=build_plan_data.get('dependencies', {}).get('packages', []) if isinstance(build_plan_data.get('dependencies'), dict) else build_plan_data.get('dependencies', []),
            build_instructions=instructions,
            environment_variables=build_plan_data.get('environment_variables', {}),
            post_build_commands=build_plan_data.get('post_build_commands', []),
            metadata={
                'generated_at': str(Path.cwd()),
                'source_files': [chunk.source_file for chunk in chunks],
                'total_chunks': len(chunks),
                'chunk_types': list(set(chunk.chunk_type for chunk in chunks))
            },
            ai_analysis=ai_analysis,
            confidence_score=overall_confidence,
            provider_used=provider_used,
            generation_metadata=build_plan_data.get('_ai_metadata', {}),
            validation_results=validation_results
        )
    
    def _fallback_analysis(self, chunks: List[EnhancedDocumentChunk]) -> Dict[str, Any]:
        """Fallback rule-based analysis when AI is not available."""
        logger.info("Using rule-based fallback analysis")
        
        # Extract information using rule-based methods
        technologies = set()
        dependencies = set()
        commands = []
        
        for chunk in chunks:
            # Extract technologies
            if hasattr(chunk, 'extracted_entities'):
                entities = chunk.extracted_entities
                technologies.update(entities.get('technologies', []))
                dependencies.update(entities.get('dependencies', []))
                commands.extend(entities.get('commands', []))
        
        return {
            'project_overview': {
                'name': 'generated-project',
                'type': 'application',
                'description': 'Generated from documentation',
                'scope': 'unknown'
            },
            'technology_stack': {
                'languages': list(technologies),
                'frameworks': [],
                'databases': [],
                'tools': []
            },
            'dependencies': {
                'runtime': list(dependencies),
                'development': [],
                'system': []
            },
            '_ai_metadata': {
                'provider': 'rule_based_fallback',
                'confidence': 0.6
            }
        }
    
    def _fallback_build_plan(self, ai_analysis: Dict[str, Any], 
                           chunks: List[EnhancedDocumentChunk]) -> Dict[str, Any]:
        """Fallback build plan generation."""
        logger.info("Using rule-based fallback build plan generation")
        
        tech_stack = ai_analysis.get('technology_stack', {})
        dependencies = ai_analysis.get('dependencies', {})
        
        return {
            'project_name': ai_analysis.get('project_overview', {}).get('name', 'generated-project'),
            'description': ai_analysis.get('project_overview', {}).get('description', 'Generated application'),
            'technology_stack': tech_stack.get('languages', []) + tech_stack.get('frameworks', []),
            'dependencies': dependencies.get('runtime', []),
            'build_instructions': [
                {
                    'step': 1,
                    'type': 'directory',
                    'action': 'create',
                    'target': 'src',
                    'description': 'Create source directory'
                }
            ],
            'environment_variables': {},
            'post_build_commands': [],
            '_ai_metadata': {
                'provider': 'rule_based_fallback',
                'confidence': 0.5
            }
        }
    
    def _save_enhanced_build_plan(self, build_plan: EnhancedBuildPlan, output_path: str):
        """Save enhanced build plan to file."""
        output_file = Path(output_path) / 'EnhancedBuildPlan.json'
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dict for JSON serialization
        plan_dict = asdict(build_plan)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(plan_dict, f, indent=2, default=str)
            
        logger.info(f"Enhanced build plan saved to: {output_file}")
