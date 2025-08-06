"""
Enhanced Code Generation and Execution Engine

Production-grade builder that generates complete applications with
actual file content, templates, and sophisticated build processes.
"""

import json
import os
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from loguru import logger
from rich.console import Console
from rich.progress import Progress, TaskID
from rich.table import Table

from .enhanced_asm import EnhancedBuildPlan
from .templates import TemplateEngine
from .ai_providers import AIProviderManager
from .prompt_engineering import AdvancedPromptEngine, PromptType


@dataclass
class BuildResult:
    """Result of a build operation."""
    success: bool
    generated_files: List[str]
    executed_commands: List[str]
    errors: List[str]
    warnings: List[str]
    build_time: float
    metadata: Dict[str, Any]


class EnhancedCodeGenerationEngine:
    """Enhanced code generation engine with template support."""
    
    def __init__(self, working_directory: Optional[str] = None, dry_run: bool = False):
        self.working_directory = Path(working_directory) if working_directory else Path.cwd()
        self.dry_run = dry_run
        self.console = Console()
        
        # Initialize components
        self.template_engine = TemplateEngine()
        self.ai_manager = AIProviderManager()
        self.prompt_engine = AdvancedPromptEngine()
        
        # Ensure working directory exists
        self.working_directory.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Enhanced code generation engine initialized in: {self.working_directory}")
        if dry_run:
            logger.info("DRY RUN MODE: No actual changes will be made")
    
    def execute_enhanced_build_plan(self, build_plan: EnhancedBuildPlan) -> BuildResult:
        """
        Execute an enhanced build plan with template generation.
        
        Args:
            build_plan: EnhancedBuildPlan object
            
        Returns:
            BuildResult with detailed execution information
        """
        import time
        start_time = time.time()
        
        result = BuildResult(
            success=False,
            generated_files=[],
            executed_commands=[],
            errors=[],
            warnings=[],
            build_time=0.0,
            metadata={}
        )
        
        try:
            logger.info(f"Executing enhanced build plan for: {build_plan.project_name}")
            
            # Create project directory
            project_dir = self.working_directory / build_plan.project_name
            if not self.dry_run:
                project_dir.mkdir(parents=True, exist_ok=True)
            
            # Step 1: Generate project structure using templates
            template_files = self._generate_from_templates(build_plan, project_dir)
            result.generated_files.extend(template_files)
            
            # Step 2: Generate additional files using AI
            ai_files = self._generate_ai_files(build_plan, project_dir)
            result.generated_files.extend(ai_files)
            
            # Step 3: Execute build instructions
            executed_commands = self._execute_build_instructions(build_plan, project_dir)
            result.executed_commands.extend(executed_commands)
            
            # Step 4: Validate the generated project
            validation_result = self._validate_generated_project(build_plan, project_dir)
            result.warnings.extend(validation_result.get('warnings', []))
            
            result.success = True
            result.build_time = time.time() - start_time
            result.metadata = {
                'project_directory': str(project_dir),
                'template_used': self._detect_primary_template(build_plan),
                'ai_provider': build_plan.provider_used,
                'confidence_score': build_plan.confidence_score
            }
            
            logger.info(f"Enhanced build completed successfully in {result.build_time:.2f}s")
            self._display_build_summary(result, build_plan)
            
        except Exception as e:
            result.errors.append(str(e))
            result.build_time = time.time() - start_time
            logger.error(f"Enhanced build failed: {e}")
        
        return result
    
    def _generate_from_templates(self, build_plan: EnhancedBuildPlan, project_dir: Path) -> List[str]:
        """Generate project files using templates."""
        generated_files = []
        
        # Detect primary framework
        primary_framework = self._detect_primary_framework(build_plan.technology_stack)
        
        if primary_framework:
            logger.info(f"Using template for framework: {primary_framework}")
            
            # Get template
            template = self.template_engine.get_template(
                primary_framework, 
                build_plan.project_name,
                description=build_plan.description,
                **build_plan.environment_variables
            )
            
            if template:
                if not self.dry_run:
                    template_files = self.template_engine.generate_project_files(template, project_dir)
                    generated_files.extend(template_files)
                else:
                    logger.info(f"[DRY RUN] Would generate template files for {primary_framework}")
                    # Simulate file generation for dry run
                    structure = template.get_project_structure()
                    for file_template in structure.files:
                        generated_files.append(str(project_dir / file_template.path))
            else:
                logger.warning(f"No template found for framework: {primary_framework}")
        else:
            logger.warning("No primary framework detected, skipping template generation")
        
        return generated_files
    
    def _generate_ai_files(self, build_plan: EnhancedBuildPlan, project_dir: Path) -> List[str]:
        """Generate additional files using AI."""
        generated_files = []
        
        # Check if AI is available
        if not self.ai_manager.get_available_providers():
            logger.info("No AI providers available, skipping AI file generation")
            return generated_files
        
        # Generate custom files based on build plan
        custom_files = self._identify_custom_files(build_plan)
        
        for file_info in custom_files:
            try:
                file_path = project_dir / file_info['path']
                
                # Generate content using AI
                prompt = self.prompt_engine.generate_code_prompt(
                    file_path=file_info['path'],
                    file_type=file_info['type'],
                    framework=self._detect_primary_framework(build_plan.technology_stack) or 'generic',
                    requirements=file_info['requirements'],
                    context=file_info.get('context', '')
                )
                
                if not self.dry_run:
                    response = self.ai_manager.generate_with_fallback(prompt)
                    
                    # Ensure parent directory exists
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Write generated content
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(response.content)
                    
                    generated_files.append(str(file_path))
                    logger.debug(f"Generated AI file: {file_path}")
                else:
                    logger.info(f"[DRY RUN] Would generate AI file: {file_path}")
                    generated_files.append(str(file_path))
                    
            except Exception as e:
                logger.warning(f"Failed to generate AI file {file_info['path']}: {e}")
        
        return generated_files
    
    def _execute_build_instructions(self, build_plan: EnhancedBuildPlan, project_dir: Path) -> List[str]:
        """Execute build instructions in the correct order."""
        executed_commands = []
        
        # Sort instructions by order
        sorted_instructions = sorted(build_plan.build_instructions, key=lambda x: x.order)
        
        with Progress() as progress:
            task = progress.add_task(
                f"Executing build instructions...", 
                total=len(sorted_instructions)
            )
            
            for instruction in sorted_instructions:
                try:
                    command = self._execute_single_instruction(instruction, project_dir)
                    if command:
                        executed_commands.append(command)
                    progress.update(task, advance=1)
                    
                except Exception as e:
                    logger.error(f"Failed to execute instruction {instruction}: {e}")
                    # Continue with other instructions
        
        # Execute post-build commands
        for command in build_plan.post_build_commands:
            try:
                self._run_command(command, project_dir)
                executed_commands.append(command)
            except Exception as e:
                logger.warning(f"Post-build command failed: {command} - {e}")
        
        return executed_commands
    
    def _execute_single_instruction(self, instruction, project_dir: Path) -> Optional[str]:
        """Execute a single build instruction."""
        if instruction.type == 'directory':
            return self._create_directory(instruction.target, project_dir)
        elif instruction.type == 'file':
            return self._create_file(instruction.target, instruction.content or '', project_dir)
        elif instruction.type == 'dependency':
            return self._install_dependency(instruction.target, project_dir)
        elif instruction.type == 'command':
            return self._run_command(instruction.target, project_dir)
        else:
            logger.warning(f"Unknown instruction type: {instruction.type}")
            return None
    
    def _create_directory(self, dir_path: str, project_dir: Path) -> Optional[str]:
        """Create a directory."""
        try:
            full_path = project_dir / dir_path
            
            if self.dry_run:
                logger.info(f"[DRY RUN] Would create directory: {full_path}")
                return f"mkdir {dir_path}"
                
            full_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {full_path}")
            return f"mkdir {dir_path}"
            
        except Exception as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")
            return None
    
    def _create_file(self, file_path: str, content: str, project_dir: Path) -> Optional[str]:
        """Create a file with content."""
        try:
            full_path = project_dir / file_path
            
            if self.dry_run:
                logger.info(f"[DRY RUN] Would create file: {full_path}")
                return f"create {file_path}"
            
            # Ensure parent directory exists
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file content
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            logger.debug(f"Created file: {full_path}")
            return f"create {file_path}"
            
        except Exception as e:
            logger.error(f"Failed to create file {file_path}: {e}")
            return None
    
    def _install_dependency(self, dependency: str, project_dir: Path) -> Optional[str]:
        """Install a dependency."""
        try:
            # Detect package manager
            if (project_dir / 'package.json').exists():
                command = f"npm install {dependency}"
            elif (project_dir / 'requirements.txt').exists() or (project_dir / 'pyproject.toml').exists():
                command = f"pip install {dependency}"
            else:
                logger.warning(f"No package manager detected for dependency: {dependency}")
                return None
            
            if self.dry_run:
                logger.info(f"[DRY RUN] Would run: {command}")
                return command
                
            return self._run_command(command, project_dir)
            
        except Exception as e:
            logger.error(f"Failed to install dependency {dependency}: {e}")
            return None
    
    def _run_command(self, command: str, project_dir: Path) -> Optional[str]:
        """Run a shell command."""
        try:
            if self.dry_run:
                logger.info(f"[DRY RUN] Would run command: {command}")
                return command
            
            logger.debug(f"Running command: {command}")
            
            result = subprocess.run(
                command,
                shell=True,
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                if result.stdout:
                    logger.debug(f"Command output: {result.stdout}")
                return command
            else:
                logger.error(f"Command failed with code {result.returncode}: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {command}")
            return None
        except Exception as e:
            logger.error(f"Failed to run command {command}: {e}")
            return None

    def _detect_primary_framework(self, technology_stack: List[str]) -> Optional[str]:
        """Detect the primary framework from technology stack."""
        tech_lower = [tech.lower() for tech in technology_stack]

        # Priority order for framework detection
        framework_patterns = [
            ('nextjs', ['next.js', 'nextjs', 'next']),
            ('react', ['react']),
            ('django', ['django']),
            ('fastapi', ['fastapi']),
            ('python', ['python'])
        ]

        for framework, patterns in framework_patterns:
            if any(pattern in tech_lower for pattern in patterns):
                return framework

        return None

    def _detect_primary_template(self, build_plan: EnhancedBuildPlan) -> str:
        """Detect which template was primarily used."""
        primary_framework = self._detect_primary_framework(build_plan.technology_stack)
        return primary_framework or 'generic'

    def _identify_custom_files(self, build_plan: EnhancedBuildPlan) -> List[Dict[str, str]]:
        """Identify custom files that need AI generation."""
        custom_files = []

        # Look for specific file requirements in the build plan
        if hasattr(build_plan, 'ai_analysis') and build_plan.ai_analysis:
            analysis = build_plan.ai_analysis

            # Check for database models
            if 'database' in str(analysis).lower():
                custom_files.append({
                    'path': 'src/models/index.ts',
                    'type': 'typescript',
                    'requirements': 'Database models and schemas',
                    'context': str(analysis)
                })

            # Check for API routes
            if 'api' in str(analysis).lower():
                custom_files.append({
                    'path': 'src/api/routes.ts',
                    'type': 'typescript',
                    'requirements': 'API routes and handlers',
                    'context': str(analysis)
                })

        return custom_files

    def _validate_generated_project(self, build_plan: EnhancedBuildPlan, project_dir: Path) -> Dict[str, Any]:
        """Validate the generated project."""
        validation_result = {
            'is_valid': True,
            'warnings': [],
            'suggestions': []
        }

        # Check for essential files
        essential_files = []
        primary_framework = self._detect_primary_framework(build_plan.technology_stack)

        if primary_framework == 'nextjs':
            essential_files = ['package.json', 'next.config.js', 'src/app/layout.tsx']
        elif primary_framework == 'react':
            essential_files = ['package.json', 'src/App.tsx']
        elif primary_framework == 'python':
            essential_files = ['requirements.txt', 'main.py']

        for file_path in essential_files:
            if not (project_dir / file_path).exists() and not self.dry_run:
                validation_result['warnings'].append(f"Missing essential file: {file_path}")

        # Check package.json validity for Node.js projects
        if (project_dir / 'package.json').exists() and not self.dry_run:
            try:
                with open(project_dir / 'package.json', 'r') as f:
                    json.load(f)
            except json.JSONDecodeError:
                validation_result['warnings'].append("Invalid package.json format")

        return validation_result

    def _display_build_summary(self, result: BuildResult, build_plan: EnhancedBuildPlan):
        """Display a summary of the build results."""
        table = Table(title=f"Build Summary: {build_plan.project_name}")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Status", "✅ Success" if result.success else "❌ Failed")
        table.add_row("Build Time", f"{result.build_time:.2f}s")
        table.add_row("Files Generated", str(len(result.generated_files)))
        table.add_row("Commands Executed", str(len(result.executed_commands)))
        table.add_row("Template Used", result.metadata.get('template_used', 'None'))
        table.add_row("AI Provider", result.metadata.get('ai_provider', 'None'))
        table.add_row("Confidence Score", f"{build_plan.confidence_score:.2f}")

        if result.warnings:
            table.add_row("Warnings", str(len(result.warnings)))

        if result.errors:
            table.add_row("Errors", str(len(result.errors)))

        self.console.print(table)

        # Show next steps
        if result.success:
            self.console.print("\n🎉 [bold green]Build completed successfully![/bold green]")
            self.console.print(f"📁 Project created in: {result.metadata.get('project_directory')}")

            # Framework-specific next steps
            primary_framework = self._detect_primary_framework(build_plan.technology_stack)
            if primary_framework == 'nextjs':
                self.console.print("\n📋 [bold]Next Steps:[/bold]")
                self.console.print("1. Navigate to project directory")
                self.console.print("2. Install dependencies: [cyan]npm install[/cyan]")
                self.console.print("3. Start development server: [cyan]npm run dev[/cyan]")
                self.console.print("4. Open http://localhost:3000 in your browser")
            elif primary_framework == 'python':
                self.console.print("\n📋 [bold]Next Steps:[/bold]")
                self.console.print("1. Navigate to project directory")
                self.console.print("2. Create virtual environment: [cyan]python -m venv venv[/cyan]")
                self.console.print("3. Activate virtual environment")
                self.console.print("4. Install dependencies: [cyan]pip install -r requirements.txt[/cyan]")

        # Show warnings if any
        if result.warnings:
            self.console.print("\n⚠️ [yellow]Warnings:[/yellow]")
            for warning in result.warnings:
                self.console.print(f"  • {warning}")

        # Show errors if any
        if result.errors:
            self.console.print("\n❌ [red]Errors:[/red]")
            for error in result.errors:
                self.console.print(f"  • {error}")
