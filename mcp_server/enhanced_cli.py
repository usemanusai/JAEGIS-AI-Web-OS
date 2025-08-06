"""
Enhanced CLI with Interactive Mode

Production-ready CLI with interactive workflows, progress persistence,
and rich user experience.
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

import click
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.tree import Tree
from loguru import logger

from .config_manager import ConfigManager
from .cache_manager import CacheManager, DocumentCache
from .error_handling import error_handler, handle_errors, ErrorCategory
from .enhanced_ingestion import EnhancedDocumentProcessor
from .enhanced_asm import EnhancedArchitecturalSynthesisModule
from .enhanced_builder import EnhancedCodeGenerationEngine


console = Console()


class InteractiveCLI:
    """Interactive CLI for guided project generation."""
    
    def __init__(self):
        self.config_manager = None
        self.cache_manager = None
        self.document_cache = None
        
    def initialize(self, config_file: Optional[str] = None, environment: str = "development"):
        """Initialize CLI components."""
        try:
            # Initialize configuration
            self.config_manager = ConfigManager(config_file, environment)
            
            # Initialize caching
            cache_dir = self.config_manager.get('cache_directory', '.mcp_cache')
            max_size_mb = self.config_manager.get('cache_max_size_mb', 1024)
            cache_ttl = self.config_manager.get('cache_ttl_hours', 24)
            
            self.cache_manager = CacheManager(cache_dir, max_size_mb, cache_ttl)
            self.document_cache = DocumentCache(self.cache_manager)
            
            # Setup logging
            self._setup_logging()
            
            console.print("✅ [green]MCP Server initialized successfully[/green]")
            
        except Exception as e:
            console.print(f"❌ [red]Initialization failed: {e}[/red]")
            raise
    
    def _setup_logging(self):
        """Setup enhanced logging."""
        log_level = self.config_manager.get('log_level', 'INFO')
        log_file_enabled = self.config_manager.get('log_file_enabled', True)
        log_file_path = self.config_manager.get('log_file_path', 'logs/mcp_server.log')
        
        # Remove default logger
        logger.remove()
        
        # Add console logger
        logger.add(
            sys.stderr,
            level=log_level,
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>"
        )
        
        # Add file logger if enabled
        if log_file_enabled:
            log_path = Path(log_file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.add(
                log_path,
                level="DEBUG",
                rotation=self.config_manager.get('log_rotation', '1 day'),
                retention=self.config_manager.get('log_retention', '30 days'),
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
            )
    
    def run_interactive_mode(self):
        """Run interactive project generation workflow."""
        console.print(Panel.fit(
            "[bold blue]🚀 MCP Server - Interactive Project Generator[/bold blue]\n"
            "Let's build your application step by step!",
            border_style="blue"
        ))
        
        try:
            # Step 1: Project Information
            project_info = self._gather_project_info()
            
            # Step 2: Document Selection
            documents = self._select_documents()
            
            # Step 3: Configuration Options
            build_options = self._configure_build_options()
            
            # Step 4: Preview and Confirmation
            if not self._preview_and_confirm(project_info, documents, build_options):
                console.print("❌ [yellow]Build cancelled by user[/yellow]")
                return
            
            # Step 5: Execute Build
            self._execute_interactive_build(project_info, documents, build_options)
            
        except KeyboardInterrupt:
            console.print("\n❌ [yellow]Build cancelled by user[/yellow]")
        except Exception as e:
            console.print(f"\n❌ [red]Interactive build failed: {e}[/red]")
            logger.error(f"Interactive build error: {e}")
    
    def _gather_project_info(self) -> Dict[str, str]:
        """Gather basic project information."""
        console.print("\n📋 [bold]Step 1: Project Information[/bold]")
        
        project_name = Prompt.ask(
            "Project name",
            default="my-project",
            show_default=True
        )
        
        description = Prompt.ask(
            "Project description",
            default="Generated by MCP Server",
            show_default=True
        )
        
        output_dir = Prompt.ask(
            "Output directory",
            default="./output",
            show_default=True
        )
        
        return {
            "name": project_name,
            "description": description,
            "output_directory": output_dir
        }
    
    def _select_documents(self) -> List[str]:
        """Select input documents."""
        console.print("\n📄 [bold]Step 2: Document Selection[/bold]")
        
        documents = []
        
        while True:
            doc_path = Prompt.ask(
                "Document path (or 'done' to finish)",
                default="done" if documents else None
            )
            
            if doc_path.lower() == 'done':
                break
            
            if not Path(doc_path).exists():
                console.print(f"❌ [red]File not found: {doc_path}[/red]")
                continue
            
            documents.append(doc_path)
            console.print(f"✅ Added: {doc_path}")
        
        if not documents:
            console.print("❌ [red]No documents selected[/red]")
            raise ValueError("At least one document is required")
        
        return documents
    
    def _configure_build_options(self) -> Dict[str, Any]:
        """Configure build options."""
        console.print("\n⚙️ [bold]Step 3: Build Configuration[/bold]")
        
        # AI Provider selection
        available_providers = ["openai", "anthropic", "local", "auto"]
        ai_provider = Prompt.ask(
            "AI Provider",
            choices=available_providers,
            default="auto",
            show_default=True
        )
        
        # Build mode
        dry_run = Confirm.ask("Dry run mode (preview only)?", default=False)
        
        # Template preference
        template_preference = Prompt.ask(
            "Preferred framework (or 'auto' for detection)",
            default="auto",
            show_default=True
        )
        
        # Advanced options
        advanced = Confirm.ask("Configure advanced options?", default=False)
        
        options = {
            "ai_provider": ai_provider,
            "dry_run": dry_run,
            "template_preference": template_preference,
            "use_cache": True,
            "parallel_processing": False
        }
        
        if advanced:
            options.update(self._configure_advanced_options())
        
        return options
    
    def _configure_advanced_options(self) -> Dict[str, Any]:
        """Configure advanced build options."""
        console.print("\n🔧 [bold]Advanced Configuration[/bold]")
        
        chunk_size = Prompt.ask(
            "Document chunk size",
            default=str(self.config_manager.get('max_chunk_size', 4000)),
            show_default=True
        )
        
        build_timeout = Prompt.ask(
            "Build timeout (seconds)",
            default=str(self.config_manager.get('build_timeout', 1800)),
            show_default=True
        )
        
        use_cache = Confirm.ask(
            "Use caching for faster processing?",
            default=True
        )
        
        return {
            "chunk_size": int(chunk_size),
            "build_timeout": int(build_timeout),
            "use_cache": use_cache
        }
    
    def _preview_and_confirm(self, project_info: Dict, documents: List[str], 
                           options: Dict[str, Any]) -> bool:
        """Preview configuration and get confirmation."""
        console.print("\n👀 [bold]Step 4: Preview Configuration[/bold]")
        
        # Create preview table
        table = Table(title="Build Configuration Preview")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Project Name", project_info["name"])
        table.add_row("Description", project_info["description"])
        table.add_row("Output Directory", project_info["output_directory"])
        table.add_row("Documents", f"{len(documents)} files")
        table.add_row("AI Provider", options["ai_provider"])
        table.add_row("Dry Run", "Yes" if options["dry_run"] else "No")
        table.add_row("Template Preference", options["template_preference"])
        
        console.print(table)
        
        # Show document list
        if len(documents) <= 5:
            console.print("\n📄 [bold]Documents:[/bold]")
            for doc in documents:
                console.print(f"  • {doc}")
        else:
            console.print(f"\n📄 [bold]Documents:[/bold] {len(documents)} files (showing first 3)")
            for doc in documents[:3]:
                console.print(f"  • {doc}")
            console.print(f"  ... and {len(documents) - 3} more")
        
        return Confirm.ask("\n🚀 Proceed with build?", default=True)
    
    def _execute_interactive_build(self, project_info: Dict, documents: List[str], 
                                 options: Dict[str, Any]):
        """Execute the build with interactive feedback."""
        console.print("\n🔨 [bold]Step 5: Building Your Project[/bold]")
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                
                # Task 1: Document Processing
                task1 = progress.add_task("Processing documents...", total=None)
                
                processor = EnhancedDocumentProcessor(
                    max_chunk_size=options.get('chunk_size', 4000)
                )
                
                all_chunks = []
                for doc_path in documents:
                    chunks = processor.process_file_enhanced(doc_path)
                    all_chunks.extend(chunks)
                
                progress.update(task1, description=f"✅ Processed {len(all_chunks)} chunks")
                
                # Task 2: AI Analysis
                task2 = progress.add_task("Analyzing architecture...", total=None)
                
                asm = EnhancedArchitecturalSynthesisModule(
                    preferred_provider=options.get('ai_provider') if options.get('ai_provider') != 'auto' else None
                )
                
                build_plan = asm.synthesize_architecture_enhanced(
                    base_chunks=all_chunks,
                    output_path=project_info["output_directory"]
                )
                
                progress.update(task2, description="✅ Architecture analyzed")
                
                # Task 3: Code Generation
                task3 = progress.add_task("Generating code...", total=None)
                
                builder = EnhancedCodeGenerationEngine(
                    working_directory=project_info["output_directory"],
                    dry_run=options.get('dry_run', False)
                )
                
                result = builder.execute_enhanced_build_plan(build_plan)
                
                progress.update(task3, description="✅ Code generated")
            
            # Show results
            self._display_build_results(result, build_plan, project_info)
            
        except Exception as e:
            console.print(f"\n❌ [red]Build failed: {e}[/red]")
            logger.error(f"Interactive build execution failed: {e}")
            raise
    
    def _display_build_results(self, result, build_plan, project_info):
        """Display build results."""
        if result.success:
            console.print("\n🎉 [bold green]Build Completed Successfully![/bold green]")
            
            # Results table
            table = Table(title="Build Results")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="white")
            
            table.add_row("Project Name", build_plan.project_name)
            table.add_row("Files Generated", str(len(result.generated_files)))
            table.add_row("Commands Executed", str(len(result.executed_commands)))
            table.add_row("Build Time", f"{result.build_time:.2f}s")
            table.add_row("AI Provider", result.metadata.get('ai_provider', 'Unknown'))
            table.add_row("Confidence Score", f"{build_plan.confidence_score:.2f}")
            
            console.print(table)
            
            # Next steps
            console.print("\n📋 [bold]Next Steps:[/bold]")
            project_path = Path(project_info["output_directory"]) / build_plan.project_name
            console.print(f"1. Navigate to: [cyan]{project_path}[/cyan]")
            
            # Framework-specific instructions
            if 'nextjs' in build_plan.technology_stack or 'next.js' in build_plan.technology_stack:
                console.print("2. Install dependencies: [cyan]npm install[/cyan]")
                console.print("3. Start development: [cyan]npm run dev[/cyan]")
            elif 'python' in build_plan.technology_stack:
                console.print("2. Create virtual environment: [cyan]python -m venv venv[/cyan]")
                console.print("3. Install dependencies: [cyan]pip install -r requirements.txt[/cyan]")
            
        else:
            console.print("\n❌ [bold red]Build Failed![/bold red]")
            
            if result.errors:
                console.print("\n[red]Errors:[/red]")
                for error in result.errors:
                    console.print(f"  • {error}")
            
            if result.warnings:
                console.print("\n[yellow]Warnings:[/yellow]")
                for warning in result.warnings:
                    console.print(f"  • {warning}")
    
    def show_status(self):
        """Show system status and statistics."""
        console.print(Panel.fit(
            "[bold blue]📊 MCP Server Status[/bold blue]",
            border_style="blue"
        ))
        
        # Configuration summary
        config_summary = self.config_manager.get_summary()
        
        config_table = Table(title="Configuration")
        config_table.add_column("Setting", style="cyan")
        config_table.add_column("Value", style="white")
        
        for key, value in config_summary.items():
            config_table.add_row(key.replace('_', ' ').title(), str(value))
        
        console.print(config_table)
        
        # Cache statistics
        if self.cache_manager:
            cache_stats = self.cache_manager.get_stats()
            
            cache_table = Table(title="Cache Statistics")
            cache_table.add_column("Metric", style="cyan")
            cache_table.add_column("Value", style="white")
            
            cache_table.add_row("Total Entries", str(cache_stats["total_entries"]))
            cache_table.add_row("Total Size", f"{cache_stats['total_size_mb']:.2f} MB")
            cache_table.add_row("Usage", f"{cache_stats['usage_percent']:.1f}%")
            
            console.print(cache_table)
        
        # Error summary
        error_summary = error_handler.get_error_summary()
        
        if error_summary["total_errors"] > 0:
            error_table = Table(title="Error Summary")
            error_table.add_column("Category", style="cyan")
            error_table.add_column("Count", style="white")
            
            for category, count in error_summary.get("by_category", {}).items():
                error_table.add_row(category.title(), str(count))
            
            console.print(error_table)
    
    def clear_cache(self):
        """Clear the cache."""
        if self.cache_manager:
            if Confirm.ask("Clear all cached data?"):
                self.cache_manager.clear()
                console.print("✅ [green]Cache cleared[/green]")
        else:
            console.print("❌ [red]Cache not initialized[/red]")
