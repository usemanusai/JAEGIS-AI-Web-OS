"""
Code Generation and Execution Engine

Reads and executes UnifiedBuildPlan.json to create files, directories,
install dependencies, and run build commands.
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
from tqdm import tqdm

from .asm import UnifiedBuildPlan, BuildInstruction


class CodeGenerationEngine:
    """Main code generation and execution engine."""
    
    def __init__(self, working_directory: Optional[str] = None, dry_run: bool = False):
        self.working_directory = Path(working_directory) if working_directory else Path.cwd()
        self.dry_run = dry_run
        self.console = Console()
        
        # Ensure working directory exists
        self.working_directory.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Code generation engine initialized in: {self.working_directory}")
        if dry_run:
            logger.info("DRY RUN MODE: No actual changes will be made")
    
    def execute_build_plan(self, build_plan_path: str) -> bool:
        """
        Execute a complete build plan from JSON file.
        
        Args:
            build_plan_path: Path to UnifiedBuildPlan.json file
            
        Returns:
            bool: True if execution successful, False otherwise
        """
        try:
            # Load build plan
            build_plan = self._load_build_plan(build_plan_path)
            
            # Execute build plan
            return self._execute_plan(build_plan)
            
        except Exception as e:
            logger.error(f"Build plan execution failed: {e}")
            return False
    
    def execute_build_plan_object(self, build_plan: UnifiedBuildPlan) -> bool:
        """
        Execute a build plan object directly.
        
        Args:
            build_plan: UnifiedBuildPlan object
            
        Returns:
            bool: True if execution successful, False otherwise
        """
        try:
            return self._execute_plan(build_plan)
        except Exception as e:
            logger.error(f"Build plan execution failed: {e}")
            return False
    
    def _load_build_plan(self, build_plan_path: str) -> UnifiedBuildPlan:
        """Load build plan from JSON file."""
        plan_file = Path(build_plan_path)
        
        if not plan_file.exists():
            raise FileNotFoundError(f"Build plan not found: {plan_file}")
            
        with open(plan_file, 'r', encoding='utf-8') as f:
            plan_data = json.load(f)
            
        # Convert dict back to UnifiedBuildPlan object
        # Convert build_instructions back to BuildInstruction objects
        instructions = []
        for inst_data in plan_data.get('build_instructions', []):
            instructions.append(BuildInstruction(**inst_data))
        
        plan_data['build_instructions'] = instructions
        
        return UnifiedBuildPlan(**plan_data)
    
    def _execute_plan(self, build_plan: UnifiedBuildPlan) -> bool:
        """Execute the complete build plan."""
        logger.info(f"Executing build plan for: {build_plan.project_name}")
        
        # Sort instructions by order
        sorted_instructions = sorted(build_plan.build_instructions, key=lambda x: x.order)
        
        # Execute instructions with progress tracking
        with Progress() as progress:
            task = progress.add_task(
                f"Building {build_plan.project_name}...", 
                total=len(sorted_instructions)
            )
            
            for instruction in sorted_instructions:
                try:
                    success = self._execute_instruction(instruction)
                    if not success:
                        logger.error(f"Instruction failed: {instruction}")
                        return False
                        
                    progress.update(task, advance=1)
                    
                except Exception as e:
                    logger.error(f"Error executing instruction {instruction}: {e}")
                    return False
        
        # Execute post-build commands
        if build_plan.post_build_commands:
            logger.info("Executing post-build commands...")
            for command in build_plan.post_build_commands:
                if not self._run_command(command):
                    logger.warning(f"Post-build command failed: {command}")
        
        logger.info(f"Build plan execution completed for: {build_plan.project_name}")
        return True
    
    def _execute_instruction(self, instruction: BuildInstruction) -> bool:
        """Execute a single build instruction."""
        logger.debug(f"Executing: {instruction.type} {instruction.action} {instruction.target}")
        
        if instruction.type == 'directory':
            return self._create_directory(instruction.target)
        elif instruction.type == 'file':
            return self._create_file(instruction.target, instruction.content or '')
        elif instruction.type == 'dependency':
            return self._install_dependency(instruction.target)
        elif instruction.type == 'command':
            return self._run_command(instruction.target)
        else:
            logger.warning(f"Unknown instruction type: {instruction.type}")
            return True  # Don't fail on unknown types
    
    def _create_directory(self, dir_path: str) -> bool:
        """Create a directory."""
        try:
            full_path = self.working_directory / dir_path
            
            if self.dry_run:
                logger.info(f"[DRY RUN] Would create directory: {full_path}")
                return True
                
            full_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {full_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")
            return False
    
    def _create_file(self, file_path: str, content: str) -> bool:
        """Create a file with specified content."""
        try:
            full_path = self.working_directory / file_path
            
            if self.dry_run:
                logger.info(f"[DRY RUN] Would create file: {full_path}")
                return True
            
            # Ensure parent directory exists
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file content
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            logger.debug(f"Created file: {full_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create file {file_path}: {e}")
            return False
    
    def _install_dependency(self, dependency: str) -> bool:
        """Install a dependency using appropriate package manager."""
        try:
            # Detect package manager based on dependency format and project structure
            if self._has_package_json():
                return self._install_npm_dependency(dependency)
            elif self._has_requirements_txt() or self._has_pyproject_toml():
                return self._install_pip_dependency(dependency)
            else:
                logger.warning(f"No package manager detected for dependency: {dependency}")
                return True  # Don't fail if we can't detect package manager
                
        except Exception as e:
            logger.error(f"Failed to install dependency {dependency}: {e}")
            return False
    
    def _has_package_json(self) -> bool:
        """Check if package.json exists in working directory."""
        return (self.working_directory / 'package.json').exists()
    
    def _has_requirements_txt(self) -> bool:
        """Check if requirements.txt exists in working directory."""
        return (self.working_directory / 'requirements.txt').exists()
    
    def _has_pyproject_toml(self) -> bool:
        """Check if pyproject.toml exists in working directory."""
        return (self.working_directory / 'pyproject.toml').exists()
    
    def _install_npm_dependency(self, dependency: str) -> bool:
        """Install NPM dependency."""
        if self.dry_run:
            logger.info(f"[DRY RUN] Would install npm dependency: {dependency}")
            return True
            
        command = f"npm install {dependency}"
        return self._run_command(command)
    
    def _install_pip_dependency(self, dependency: str) -> bool:
        """Install pip dependency."""
        if self.dry_run:
            logger.info(f"[DRY RUN] Would install pip dependency: {dependency}")
            return True
            
        command = f"pip install {dependency}"
        return self._run_command(command)
    
    def _run_command(self, command: str) -> bool:
        """Run a shell command."""
        try:
            if self.dry_run:
                logger.info(f"[DRY RUN] Would run command: {command}")
                return True
            
            logger.debug(f"Running command: {command}")
            
            # Run command in working directory
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.working_directory,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                if result.stdout:
                    logger.debug(f"Command output: {result.stdout}")
                return True
            else:
                logger.error(f"Command failed with code {result.returncode}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {command}")
            return False
        except Exception as e:
            logger.error(f"Failed to run command {command}: {e}")
            return False
    
    def validate_build_plan(self, build_plan_path: str) -> bool:
        """Validate a build plan without executing it."""
        try:
            build_plan = self._load_build_plan(build_plan_path)
            
            # Basic validation
            if not build_plan.project_name:
                logger.error("Build plan missing project name")
                return False
                
            if not build_plan.build_instructions:
                logger.error("Build plan has no build instructions")
                return False
            
            # Validate instruction order
            orders = [inst.order for inst in build_plan.build_instructions]
            if len(orders) != len(set(orders)):
                logger.warning("Build plan has duplicate instruction orders")
            
            logger.info(f"Build plan validation passed: {len(build_plan.build_instructions)} instructions")
            return True
            
        except Exception as e:
            logger.error(f"Build plan validation failed: {e}")
            return False
