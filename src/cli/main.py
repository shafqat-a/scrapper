"""
Main CLI entry point for the web scraper system.
Provides the primary command interface using Click.
"""

# Standard library imports
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Optional

# Third-party imports
import click
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Local folder imports
# Local imports
from ..scraper_core.models.workflow import Workflow
from ..scraper_core.workflow import (
    WorkflowEngine,
    WorkflowExecutionError,
    WorkflowValidationError,
)
from .commands import providers, run, validate

# Setup rich console
console = Console()

# Configure logging with rich
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console)],
)


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version="1.0.0", prog_name="scrapper")
@click.option(
    "--verbose",
    "-v",
    count=True,
    help="Increase verbosity (-v for INFO, -vv for DEBUG)",
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    help="Suppress all output except errors",
)
@click.pass_context
def cli(ctx, verbose: int, quiet: bool):
    """
    Web Scrapper - A provider-based web scraping system.

    This tool allows you to define JSON workflows that orchestrate
    different scraping providers (BeautifulSoup, Scrapy, Playwright)
    with various storage backends (CSV, PostgreSQL, JSON).

    Examples:

      # Run a workflow
      scrapper run workflow.json

      # Validate a workflow
      scrapper validate workflow.json

      # List available providers
      scrapper providers list

      # Test provider connection
      scrapper providers test postgresql --config config.json
    """
    # Ensure context object exists
    if ctx.obj is None:
        ctx.obj = {}

    # Configure logging level
    if quiet:
        logging.getLogger().setLevel(logging.ERROR)
    elif verbose == 0:
        logging.getLogger().setLevel(logging.WARNING)
    elif verbose == 1:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.DEBUG)

    # Store configuration in context
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    ctx.obj["console"] = console


# Add command groups
cli.add_command(run.run)
cli.add_command(validate.validate)
cli.add_command(providers.providers)


@cli.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file for the generated workflow",
)
@click.pass_context
def init(ctx, output: Optional[str]):
    """Initialize a new workflow configuration file."""
    console = ctx.obj["console"]

    # Default workflow template
    workflow_template = {
        "version": "1.0.0",
        "metadata": {
            "name": "My Scraping Workflow",
            "description": "A sample web scraping workflow",
            "author": "scrapper-user",
            "target_site": "https://example.com",
            "tags": ["example", "template"],
        },
        "scraping": {
            "provider": "beautifulsoup",
            "config": {
                "parser": "lxml",
                "timeout": 30000,
                "headers": {"User-Agent": "scrapper/1.0.0"},
            },
        },
        "storage": {
            "provider": "csv",
            "config": {
                "file_path": "./scraped_data.csv",
                "headers": True,
                "delimiter": ",",
                "append": False,
            },
        },
        "steps": [
            {
                "id": "init-step",
                "command": "init",
                "config": {"url": "https://example.com", "wait_for": "body"},
                "retries": 3,
                "timeout": 30000,
                "continue_on_error": False,
            },
            {
                "id": "extract-data",
                "command": "extract",
                "config": {
                    "elements": {
                        "title": {"selector": "h1", "type": "text"},
                        "description": {"selector": ".description", "type": "text"},
                    }
                },
                "retries": 3,
                "timeout": 30000,
            },
        ],
    }

    output_file = output or "workflow.json"
    output_path = Path(output_file)

    try:
        # Check if file already exists
        if output_path.exists():
            if not click.confirm(f"File {output_file} already exists. Overwrite?"):
                console.print("❌ Workflow initialization cancelled.", style="red")
                return

        # Write workflow template
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(workflow_template, f, indent=2)

        console.print(
            f"✅ Workflow template created: [bold]{output_file}[/bold]", style="green"
        )
        console.print("\n📝 Next steps:")
        console.print("  1. Edit the workflow file to match your target website")
        console.print(
            "  2. Validate the workflow: [bold]scrapper validate workflow.json[/bold]"
        )
        console.print("  3. Run the workflow: [bold]scrapper run workflow.json[/bold]")

    except Exception as e:
        console.print(f"❌ Failed to create workflow template: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.pass_context
def version(ctx):
    """Show version information."""
    console = ctx.obj["console"]

    console.print("🚀 [bold]Web Scrapper[/bold] v1.0.0")
    console.print("A provider-based web scraping system")
    console.print("\n📦 Core Components:")
    console.print("  • Scraping Providers: BeautifulSoup, Scrapy, Playwright")
    console.print("  • Storage Providers: CSV, PostgreSQL, JSON/JSONL")
    console.print("  • Workflow Engine: JSON-based workflow orchestration")
    console.print("  • CLI Interface: Click + Rich for beautiful terminal experience")
    console.print("\n🔗 More info: https://github.com/example/scrapper")


def main():
    """Main CLI entry point."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n❌ Operation cancelled by user.", style="red")
        sys.exit(130)
    except Exception as e:
        console.print(f"❌ Unexpected error: {e}", style="red")
        if "--debug" in sys.argv:
            # Standard library imports
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
