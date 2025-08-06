"""
MCP Server CLI Entry Point

Command-line interface for the MCP Server application foundry.
"""

import os
import sys
from pathlib import Path
from typing import Optional, List

import click
from loguru import logger
from rich.console import Console
from rich.table import Table

# Enhanced imports
from .enhanced_ingestion import EnhancedDocumentProcessor
from .enhanced_asm import EnhancedArchitecturalSynthesisModule
from .enhanced_builder import EnhancedCodeGenerationEngine
from .enhanced_cli import InteractiveCLI
from .config_manager import ConfigManager
from .cache_manager import CacheManager
from .error_handling import error_handler, handle_errors, ErrorCategory

# Legacy imports for backward compatibility
from .ingestion import DocumentProcessor
from .asm import ArchitecturalSynthesisModule
from .builder import CodeGenerationEngine


console = Console()


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.option('--environment', '-e', default='development', help='Environment (development, production)')
@click.pass_context
def cli(ctx, verbose: bool, debug: bool, config: Optional[str], environment: str):
    """MCP Server - Universal AI-Powered Application Foundry"""

    # Ensure context object exists
    ctx.ensure_object(dict)

    # Store configuration
    ctx.obj['config_file'] = config
    ctx.obj['environment'] = environment
    ctx.obj['verbose'] = verbose
    ctx.obj['debug'] = debug

    # Configure basic logging (will be enhanced by config manager)
    log_level = "DEBUG" if debug else "INFO" if verbose else "WARNING"
    logger.remove()
    logger.add(sys.stderr, level=log_level, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")


@cli.command()
@click.option('--base', '-b', required=True, type=click.Path(exists=True),
              help='Path to base architecture document')
@click.option('--overlay', '-o', type=click.Path(exists=True),
              help='Path to optional strategic overlay document')
@click.option('--output', '-out', type=click.Path(), default='./output',
              help='Output directory for generated project (default: ./output)')
@click.option('--plan-only', is_flag=True,
              help='Generate build plan only, do not execute')
@click.option('--dry-run', is_flag=True,
              help='Show what would be done without making changes')
@click.option('--api-key', type=str,
              help='OpenAI API key for AI enhancement (or set OPENAI_API_KEY env var)')
@click.option('--enhanced', is_flag=True, default=True,
              help='Use enhanced processing (default: true)')
@click.option('--legacy', is_flag=True,
              help='Use legacy processing mode')
@click.pass_context
def build(ctx, base: str, overlay: Optional[str], output: str, plan_only: bool,
          dry_run: bool, api_key: Optional[str], enhanced: bool, legacy: bool):
    """
    Build an application from architectural documentation.
    
    This command processes the base architecture document (and optional overlay)
    to generate a comprehensive build plan and execute it.
    """
    
    console.print(f"🚀 [bold blue]MCP Server - Application Foundry[/bold blue]")
    console.print(f"📄 Base document: {base}")
    
    if overlay:
        console.print(f"📄 Overlay document: {overlay}")
    
    console.print(f"📁 Output directory: {output}")
    
    if dry_run:
        console.print("🔍 [yellow]DRY RUN MODE - No changes will be made[/yellow]")
    
    try:
        # Set API key if provided
        if api_key:
            os.environ['OPENAI_API_KEY'] = api_key
        
        # Step 1: Document Ingestion
        console.print("\n📖 [bold]Step 1: Document Processing[/bold]")
        processor = DocumentProcessor()
        
        # Process base document
        base_chunks = processor.process_file(base)
        console.print(f"✅ Processed base document: {len(base_chunks)} chunks")
        
        # Process overlay document if provided
        overlay_chunks = None
        if overlay:
            overlay_chunks = processor.process_file(overlay)
            console.print(f"✅ Processed overlay document: {len(overlay_chunks)} chunks")
        
        # Step 2: Architectural Synthesis
        console.print("\n🧠 [bold]Step 2: Architectural Synthesis[/bold]")
        asm = ArchitecturalSynthesisModule(api_key=api_key)
        
        build_plan = asm.synthesize_architecture(
            base_chunks=base_chunks,
            overlay_chunks=overlay_chunks,
            output_path=output
        )
        
        console.print(f"✅ Generated build plan: {build_plan.project_name}")
        console.print(f"   - Technology stack: {', '.join(build_plan.technology_stack)}")
        console.print(f"   - Dependencies: {len(build_plan.dependencies)}")
        console.print(f"   - Build instructions: {len(build_plan.build_instructions)}")
        
        # Display build plan summary
        _display_build_plan_summary(build_plan)
        
        if plan_only:
            console.print(f"\n✅ [green]Build plan generated and saved to: {output}/UnifiedBuildPlan.json[/green]")
            return
        
        # Step 3: Code Generation and Execution
        console.print("\n🔨 [bold]Step 3: Code Generation & Execution[/bold]")
        
        # Create output directory
        output_path = Path(output)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize code generation engine
        builder = CodeGenerationEngine(
            working_directory=str(output_path / build_plan.project_name),
            dry_run=dry_run
        )
        
        # Execute build plan
        success = builder.execute_build_plan_object(build_plan)
        
        if success:
            console.print(f"\n🎉 [bold green]Build completed successfully![/bold green]")
            console.print(f"📁 Project created in: {output_path / build_plan.project_name}")
            
            # Show next steps
            _show_next_steps(build_plan, output_path / build_plan.project_name)
        else:
            console.print(f"\n❌ [bold red]Build failed![/bold red]")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Build process failed: {e}")
        console.print(f"\n❌ [bold red]Error: {e}[/bold red]")
        sys.exit(1)


@cli.command()
@click.argument('build_plan_path', type=click.Path(exists=True))
@click.option('--output', '-out', type=click.Path(), default='./output',
              help='Output directory for generated project (default: ./output)')
@click.option('--dry-run', is_flag=True,
              help='Show what would be done without making changes')
def execute(build_plan_path: str, output: str, dry_run: bool):
    """
    Execute an existing build plan from UnifiedBuildPlan.json file.
    """
    
    console.print(f"🔨 [bold blue]Executing Build Plan[/bold blue]")
    console.print(f"📄 Build plan: {build_plan_path}")
    console.print(f"📁 Output directory: {output}")
    
    if dry_run:
        console.print("🔍 [yellow]DRY RUN MODE - No changes will be made[/yellow]")
    
    try:
        # Create output directory
        output_path = Path(output)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize code generation engine
        builder = CodeGenerationEngine(
            working_directory=str(output_path),
            dry_run=dry_run
        )
        
        # Validate build plan first
        if not builder.validate_build_plan(build_plan_path):
            console.print("❌ [bold red]Build plan validation failed![/bold red]")
            sys.exit(1)
        
        # Execute build plan
        success = builder.execute_build_plan(build_plan_path)
        
        if success:
            console.print(f"\n🎉 [bold green]Build completed successfully![/bold green]")
            console.print(f"📁 Project created in: {output_path}")
        else:
            console.print(f"\n❌ [bold red]Build failed![/bold red]")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Build execution failed: {e}")
        console.print(f"\n❌ [bold red]Error: {e}[/bold red]")
        sys.exit(1)


@cli.command()
@click.argument('document_path', type=click.Path(exists=True))
@click.option('--output', '-out', type=click.Path(), default='./chunks.json',
              help='Output file for processed chunks (default: ./chunks.json)')
def analyze(document_path: str, output: str):
    """
    Analyze a document and show processing results.
    """
    
    console.print(f"🔍 [bold blue]Document Analysis[/bold blue]")
    console.print(f"📄 Document: {document_path}")
    
    try:
        processor = DocumentProcessor()
        chunks = processor.process_file(document_path)
        
        # Display analysis results
        _display_analysis_results(chunks)
        
        # Save chunks to file
        import json
        with open(output, 'w', encoding='utf-8') as f:
            chunk_data = [
                {
                    'content': chunk.content,
                    'metadata': chunk.metadata,
                    'chunk_index': chunk.chunk_index,
                    'source_file': chunk.source_file,
                    'chunk_type': chunk.chunk_type
                }
                for chunk in chunks
            ]
            json.dump(chunk_data, f, indent=2)
        
        console.print(f"\n✅ [green]Analysis complete. Results saved to: {output}[/green]")
        
    except Exception as e:
        logger.error(f"Document analysis failed: {e}")
        console.print(f"\n❌ [bold red]Error: {e}[/bold red]")
        sys.exit(1)


def _display_build_plan_summary(build_plan):
    """Display a summary table of the build plan."""
    table = Table(title="Build Plan Summary")
    table.add_column("Category", style="cyan")
    table.add_column("Details", style="white")
    
    table.add_row("Project Name", build_plan.project_name)
    table.add_row("Description", build_plan.description)
    table.add_row("Technologies", ", ".join(build_plan.technology_stack))
    table.add_row("Dependencies", str(len(build_plan.dependencies)))
    table.add_row("Build Steps", str(len(build_plan.build_instructions)))
    table.add_row("Environment Variables", str(len(build_plan.environment_variables)))
    
    console.print(table)


def _display_analysis_results(chunks):
    """Display document analysis results."""
    table = Table(title="Document Analysis Results")
    table.add_column("Chunk Type", style="cyan")
    table.add_column("Count", style="white")
    table.add_column("Avg Tokens", style="white")
    
    # Group chunks by type
    chunk_stats = {}
    for chunk in chunks:
        chunk_type = chunk.chunk_type
        if chunk_type not in chunk_stats:
            chunk_stats[chunk_type] = {'count': 0, 'total_tokens': 0}
        
        chunk_stats[chunk_type]['count'] += 1
        chunk_stats[chunk_type]['total_tokens'] += chunk.metadata.get('token_count', 0)
    
    # Add rows to table
    for chunk_type, stats in chunk_stats.items():
        avg_tokens = stats['total_tokens'] // stats['count'] if stats['count'] > 0 else 0
        table.add_row(chunk_type, str(stats['count']), str(avg_tokens))
    
    console.print(table)


def _show_next_steps(build_plan, project_path):
    """Show next steps after successful build."""
    console.print("\n📋 [bold]Next Steps:[/bold]")
    
    if 'next.js' in build_plan.technology_stack or 'react' in build_plan.technology_stack:
        console.print("1. Navigate to project directory:")
        console.print(f"   cd {project_path}")
        console.print("2. Install dependencies:")
        console.print("   npm install")
        console.print("3. Start development server:")
        console.print("   npm run dev")
    elif 'python' in build_plan.technology_stack:
        console.print("1. Navigate to project directory:")
        console.print(f"   cd {project_path}")
        console.print("2. Create virtual environment:")
        console.print("   python -m venv venv")
        console.print("3. Activate virtual environment and install dependencies:")
        console.print("   source venv/bin/activate  # On Windows: venv\\Scripts\\activate")
        console.print("   pip install -r requirements.txt")
    else:
        console.print("1. Navigate to project directory:")
        console.print(f"   cd {project_path}")
        console.print("2. Follow project-specific setup instructions")


@cli.command()
@click.pass_context
def interactive(ctx):
    """
    Interactive mode for guided project generation.

    This command provides a step-by-step guided workflow for creating
    applications from architectural documentation.
    """

    console.print(f"🚀 [bold blue]MCP Server - Interactive Mode[/bold blue]")

    try:
        # Initialize interactive CLI
        interactive_cli = InteractiveCLI()
        interactive_cli.initialize(
            config_file=ctx.obj.get('config_file'),
            environment=ctx.obj.get('environment', 'development')
        )

        # Run interactive workflow
        interactive_cli.run_interactive_mode()

    except Exception as e:
        logger.error(f"Interactive mode failed: {e}")
        console.print(f"\n❌ [bold red]Error: {e}[/bold red]")
        sys.exit(1)


@cli.command()
@click.pass_context
def status(ctx):
    """
    Show system status and statistics.
    """

    try:
        # Initialize interactive CLI for status display
        interactive_cli = InteractiveCLI()
        interactive_cli.initialize(
            config_file=ctx.obj.get('config_file'),
            environment=ctx.obj.get('environment', 'development')
        )

        # Show status
        interactive_cli.show_status()

    except Exception as e:
        logger.error(f"Status command failed: {e}")
        console.print(f"\n❌ [bold red]Error: {e}[/bold red]")
        sys.exit(1)


@cli.command()
@click.pass_context
def clear_cache(ctx):
    """
    Clear the application cache.
    """

    try:
        # Initialize interactive CLI for cache management
        interactive_cli = InteractiveCLI()
        interactive_cli.initialize(
            config_file=ctx.obj.get('config_file'),
            environment=ctx.obj.get('environment', 'development')
        )

        # Clear cache
        interactive_cli.clear_cache()

    except Exception as e:
        logger.error(f"Clear cache command failed: {e}")
        console.print(f"\n❌ [bold red]Error: {e}[/bold red]")
        sys.exit(1)


if __name__ == '__main__':
    cli()
