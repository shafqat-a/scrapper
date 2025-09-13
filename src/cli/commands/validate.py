"""
Validate command - Validate workflow definitions.
"""

# Standard library imports
import json
import sys
from pathlib import Path

# Third-party imports
import click
from rich.table import Table

# Local folder imports
# Local imports
from ...scraper_core.models.workflow import Workflow
from ...scraper_core.workflow import WorkflowEngine, WorkflowValidationError


@click.command()
@click.argument("workflow_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format for validation results",
)
@click.option(
    "--detailed",
    "-d",
    is_flag=True,
    help="Show detailed validation information",
)
@click.pass_context
def validate(ctx, workflow_file: Path, format: str, detailed: bool):
    """
    Validate a workflow definition file.

    WORKFLOW_FILE is the path to the JSON workflow definition file.

    This command validates:
    - JSON syntax and structure
    - Pydantic model validation
    - Business logic validation
    - Provider availability
    - Step configuration validity

    Examples:

      # Basic validation
      scrapper validate workflow.json

      # Detailed validation with JSON output
      scrapper validate workflow.json --detailed --format json
    """
    console = ctx.obj["console"]

    validation_results = {
        "file_path": str(workflow_file),
        "valid": False,
        "errors": [],
        "warnings": [],
        "workflow_info": None,
    }

    try:
        # Load and parse JSON
        console.print("🔍 Loading workflow file...")
        with open(workflow_file, "r", encoding="utf-8") as f:
            workflow_data = json.load(f)

        console.print("✅ JSON syntax valid")

        # Parse with Pydantic
        console.print("🔍 Validating workflow structure...")
        workflow = Workflow(**workflow_data)
        console.print("✅ Workflow structure valid")

        # Store workflow info for detailed output
        validation_results["workflow_info"] = {
            "name": workflow.metadata.name,
            "version": workflow.version,
            "description": workflow.metadata.description,
            "author": workflow.metadata.author,
            "target_site": workflow.metadata.target_site,
            "steps_count": len(workflow.steps),
            "scraping_provider": workflow.scraping.provider,
            "storage_provider": workflow.storage.provider,
            "has_post_processing": bool(workflow.post_processing),
        }

        # Business logic validation
        console.print("🔍 Validating workflow logic...")
        engine = WorkflowEngine()
        # Note: We'll use a synchronous wrapper for the async validation
        # Standard library imports
        import asyncio

        asyncio.run(engine.validate_workflow(workflow))

        console.print("✅ Workflow logic valid")

        validation_results["valid"] = True

        # Display results
        if format == "json":
            console.print(json.dumps(validation_results, indent=2))
        else:
            _display_validation_table(console, workflow, detailed)

        console.print("\n✅ [bold green]Workflow validation successful![/bold green]")
        console.print(f"   File: [bold]{workflow_file}[/bold]")
        console.print(f"   Workflow: [bold]{workflow.metadata.name}[/bold]")

    except FileNotFoundError:
        validation_results["errors"].append("File not found")
        console.print(
            f"❌ Workflow file not found: [bold]{workflow_file}[/bold]", style="red"
        )
        sys.exit(1)

    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON syntax: {e}"
        validation_results["errors"].append(error_msg)
        console.print(f"❌ {error_msg}", style="red")

        if format == "json":
            console.print(json.dumps(validation_results, indent=2))
        sys.exit(1)

    except Exception as e:
        # Handle both Pydantic and workflow validation errors
        error_msg = str(e)
        validation_results["errors"].append(error_msg)

        console.print(f"❌ Validation failed: {error_msg}", style="red")

        if format == "json":
            console.print(json.dumps(validation_results, indent=2))
        sys.exit(1)


def _display_validation_table(console, workflow: Workflow, detailed: bool):
    """Display validation results in table format."""
    # Basic workflow info
    console.print("\n📋 [bold]Workflow Information[/bold]")

    info_table = Table(show_header=True, header_style="bold magenta")
    info_table.add_column("Property", style="cyan")
    info_table.add_column("Value", style="white")

    info_table.add_row("Name", workflow.metadata.name)
    info_table.add_row("Version", workflow.version)
    info_table.add_row("Description", workflow.metadata.description)
    info_table.add_row("Author", workflow.metadata.author)
    info_table.add_row("Target Site", workflow.metadata.target_site)
    info_table.add_row("Steps", str(len(workflow.steps)))
    info_table.add_row("Scraping Provider", workflow.scraping.provider)
    info_table.add_row("Storage Provider", workflow.storage.provider)

    if workflow.metadata.tags:
        info_table.add_row("Tags", ", ".join(workflow.metadata.tags))

    console.print(info_table)

    if detailed:
        # Step details
        console.print("\n🔧 [bold]Workflow Steps[/bold]")

        steps_table = Table(show_header=True, header_style="bold magenta")
        steps_table.add_column("ID", style="cyan")
        steps_table.add_column("Command", style="yellow")
        steps_table.add_column("Retries", style="dim")
        steps_table.add_column("Timeout", style="dim")
        steps_table.add_column("Continue on Error", style="dim")

        for step in workflow.steps:
            steps_table.add_row(
                step.id,
                step.command,
                str(step.retries),
                f"{step.timeout}ms",
                "✅" if step.continue_on_error else "❌",
            )

        console.print(steps_table)

        # Provider configurations
        console.print("\n⚙️  [bold]Provider Configurations[/bold]")

        # Scraping provider config
        console.print(
            f"\n[bold cyan]Scraping Provider ({workflow.scraping.provider}):[/bold cyan]"
        )
        for key, value in workflow.scraping.config.items():
            console.print(f"  • {key}: [dim]{value}[/dim]")

        # Storage provider config
        console.print(
            f"\n[bold magenta]Storage Provider ({workflow.storage.provider}):[/bold magenta]"
        )
        for key, value in workflow.storage.config.items():
            console.print(f"  • {key}: [dim]{value}[/dim]")

        # Post-processing if available
        if workflow.post_processing:
            console.print(
                f"\n🔄 [bold]Post-processing ({len(workflow.post_processing)} steps):[/bold]"
            )
            for i, step in enumerate(workflow.post_processing, 1):
                console.print(f"  {i}. [yellow]{step.type}[/yellow]")
                for key, value in step.config.items():
                    console.print(f"     • {key}: [dim]{value}[/dim]")

        # Schema definition if available
        if workflow.storage.data_schema:
            schema = workflow.storage.data_schema
            console.print(f"\n📊 [bold]Data Schema ({schema.name}):[/bold]")

            schema_table = Table(show_header=True, header_style="bold magenta")
            schema_table.add_column("Field", style="cyan")
            schema_table.add_column("Type", style="yellow")
            schema_table.add_column("Required", style="dim")
            schema_table.add_column("Max Length", style="dim")
            schema_table.add_column("Index", style="dim")

            for field_name, field_def in schema.fields.items():
                schema_table.add_row(
                    field_name,
                    field_def.type,
                    "✅" if field_def.required else "❌",
                    str(field_def.max_length) if field_def.max_length else "—",
                    "✅" if field_def.index else "❌",
                )

            console.print(schema_table)

            if schema.primary_key:
                console.print(
                    f"   Primary Key: [bold]{', '.join(schema.primary_key)}[/bold]"
                )
