"""
Run command - Execute workflows.
"""

# Standard library imports
import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

# Third-party imports
import click
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

# Local folder imports
# Local imports
from ...scraper_core.models.workflow import Workflow
from ...scraper_core.workflow import (
    WorkflowEngine,
    WorkflowExecutionError,
    WorkflowValidationError,
)


@click.command()
@click.argument("workflow_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Override output file/directory for scraped data",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "csv", "table"]),
    default="table",
    help="Output format for results summary",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Validate workflow but don't execute it",
)
@click.option(
    "--continue-on-error",
    is_flag=True,
    help="Continue execution even if individual steps fail",
)
@click.pass_context
def run(
    ctx,
    workflow_file: Path,
    output: Optional[Path],
    format: str,
    dry_run: bool,
    continue_on_error: bool,
):
    """
    Execute a scraping workflow.

    WORKFLOW_FILE is the path to the JSON workflow definition file.

    Examples:

      # Run a basic workflow
      scrapper run workflow.json

      # Run with custom output location
      scrapper run workflow.json --output ./custom_output.csv

      # Validate workflow without running
      scrapper run workflow.json --dry-run

      # Continue on errors and output as JSON
      scrapper run workflow.json --continue-on-error --format json
    """
    console = ctx.obj["console"]

    try:
        # Load workflow
        with open(workflow_file, "r", encoding="utf-8") as f:
            workflow_data = json.load(f)

        workflow = Workflow(**workflow_data)

        # Override output if specified
        if output:
            if workflow.storage.provider == "csv":
                workflow.storage.config["file_path"] = str(output)
            elif workflow.storage.provider == "json":
                workflow.storage.config["file_path"] = str(output)
            elif workflow.storage.provider == "postgresql":
                console.print(
                    "⚠️  Cannot override output for PostgreSQL storage", style="yellow"
                )

        # Override continue_on_error if specified
        if continue_on_error:
            for step in workflow.steps:
                step.continue_on_error = True

        # Create workflow engine
        engine = WorkflowEngine()

        if dry_run:
            console.print("🔍 [bold]Dry run mode - validating workflow only[/bold]")

        # Show workflow info
        _display_workflow_info(console, workflow)

        if dry_run:
            # Just validate
            console.print("\n🔍 Validating workflow...")
            asyncio.run(engine.validate_workflow(workflow))
            console.print("✅ [bold green]Workflow validation successful![/bold green]")
            console.print("\n💡 Run without --dry-run to execute the workflow")
            return

        # Execute workflow with progress tracking
        console.print("\n🚀 Starting workflow execution...")

        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            # Add overall progress task
            overall_task = progress.add_task("Executing workflow", total=100)

            # Execute workflow
            result = asyncio.run(engine.execute_workflow(workflow))

            progress.update(overall_task, completed=100)

        # Display results
        _display_execution_results(console, result, format)

        # Exit with appropriate code
        if not result.success:
            sys.exit(1)

    except FileNotFoundError:
        console.print(
            f"❌ Workflow file not found: [bold]{workflow_file}[/bold]", style="red"
        )
        sys.exit(1)
    except json.JSONDecodeError as e:
        console.print(f"❌ Invalid JSON in workflow file: {e}", style="red")
        sys.exit(1)
    except WorkflowValidationError as e:
        console.print(f"❌ Workflow validation failed: {e}", style="red")
        sys.exit(1)
    except WorkflowExecutionError as e:
        console.print(f"❌ Workflow execution failed: {e}", style="red")
        if e.step_id:
            console.print(f"   Failed at step: [bold]{e.step_id}[/bold]", style="red")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n❌ Execution cancelled by user", style="red")
        sys.exit(130)
    except Exception as e:
        console.print(f"❌ Unexpected error: {e}", style="red")
        sys.exit(1)


def _display_workflow_info(console, workflow: Workflow):
    """Display workflow information."""
    console.print(f"\n📋 [bold]Workflow: {workflow.metadata.name}[/bold]")
    console.print(f"   Description: {workflow.metadata.description}")
    console.print(f"   Author: {workflow.metadata.author}")
    console.print(f"   Target: [link]{workflow.metadata.target_site}[/link]")
    console.print(f"   Steps: {len(workflow.steps)}")
    console.print(
        f"   Scraping Provider: [bold cyan]{workflow.scraping.provider}[/bold cyan]"
    )
    console.print(
        f"   Storage Provider: [bold magenta]{workflow.storage.provider}[/bold magenta]"
    )


def _display_execution_results(console, result, format: str):
    """Display workflow execution results."""
    if format == "json":
        # Output as JSON
        console.print(json.dumps(result.to_dict(), indent=2))
        return

    # Display summary
    console.print("\n" + "=" * 60)
    console.print("📊 [bold]Execution Summary[/bold]")
    console.print("=" * 60)

    # Status
    status_color = "green" if result.success else "red"
    status_icon = "✅" if result.success else "❌"
    console.print(
        f"{status_icon} Status: [bold {status_color}]{'SUCCESS' if result.success else 'FAILED'}[/bold {status_color}]"
    )

    # Stats
    console.print(f"⏱️  Execution Time: [bold]{result.execution_time:.2f}s[/bold]")
    console.print(
        f"📝 Steps Completed: [bold]{result.completed_steps}/{result.total_steps}[/bold]"
    )

    if result.failed_steps > 0:
        console.print(f"💥 Failed Steps: [bold red]{result.failed_steps}[/bold red]")

    console.print(f"📦 Data Elements: [bold]{len(result.extracted_data)}[/bold]")

    # Errors
    if result.errors:
        console.print("\n❌ [bold red]Errors:[/bold red]")
        for error in result.errors:
            console.print(
                f"   • Step [bold]{error['step_id']}[/bold]: {error['message']}"
            )

    # Data preview if available and format is table
    if format == "table" and result.extracted_data:
        console.print("\n📋 [bold]Data Preview (first 10 items):[/bold]")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Type", style="cyan")
        table.add_column("Selector", style="dim")
        table.add_column("Value", style="white")

        for element in result.extracted_data[:10]:
            # Truncate long values
            value = str(element.value)
            if len(value) > 50:
                value = value[:47] + "..."

            table.add_row(element.type, element.selector, value)

        console.print(table)

        if len(result.extracted_data) > 10:
            console.print(f"... and {len(result.extracted_data) - 10} more items")

    console.print("\n" + "=" * 60)
