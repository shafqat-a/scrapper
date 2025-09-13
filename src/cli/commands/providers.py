"""
Providers command - Manage and test providers.
"""

# Standard library imports
import asyncio
import json
import sys
from typing import Optional

# Third-party imports
import click
from rich.table import Table

# Local folder imports
# Local imports
from ...scraper_core.models.provider_config import ConnectionConfig
from ...scraper_core.providers.factory import get_provider_factory


@click.group()
def providers():
    """
    Manage scraping and storage providers.

    This command group allows you to:
    - List available providers
    - Test provider connections
    - Get provider information

    Examples:

      # List all providers
      scrapper providers list

      # List only scraping providers
      scrapper providers list --type scraping

      # Test a provider connection
      scrapper providers test postgresql --config config.json
    """
    pass


@providers.command()
@click.option(
    "--type",
    "-t",
    "provider_type",
    type=click.Choice(["scraping", "storage"]),
    help="Filter by provider type",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
@click.pass_context
def list(ctx, provider_type: Optional[str], format: str):
    """
    List available providers.

    Shows all registered scraping and storage providers
    with their capabilities and metadata.

    Examples:

      # List all providers
      scrapper providers list

      # List only scraping providers
      scrapper providers list --type scraping

      # Output as JSON
      scrapper providers list --format json
    """
    console = ctx.obj["console"]

    try:
        # Get provider factory
        factory = get_provider_factory()

        # Get providers
        providers = asyncio.run(factory.list_providers(type_filter=provider_type))

        if format == "json":
            # Output as JSON
            providers_data = []
            for provider in providers:
                providers_data.append(
                    {
                        "name": provider.name,
                        "version": provider.version,
                        "type": provider.provider_type,
                        "capabilities": provider.capabilities,
                        "description": provider.description,
                    }
                )
            console.print(json.dumps(providers_data, indent=2))
            return

        # Display as table
        if not providers:
            console.print("❌ No providers found", style="red")
            return

        console.print("\n📦 [bold]Available Providers[/bold]")
        if provider_type:
            console.print(f"   Type: [cyan]{provider_type}[/cyan]")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan", width=20)
        table.add_column("Type", style="yellow", width=12)
        table.add_column("Version", style="dim", width=10)
        table.add_column("Capabilities", style="green")
        table.add_column("Description", style="white")

        # Group providers by type
        scraping_providers = [p for p in providers if p.provider_type == "scraping"]
        storage_providers = [p for p in providers if p.provider_type == "storage"]

        # Add scraping providers
        for provider in scraping_providers:
            capabilities_text = ", ".join(provider.capabilities[:3])
            if len(provider.capabilities) > 3:
                capabilities_text += f" (+{len(provider.capabilities) - 3} more)"

            table.add_row(
                provider.name,
                "scraping",
                provider.version,
                capabilities_text,
                (
                    provider.description[:50] + "..."
                    if len(provider.description) > 50
                    else provider.description
                ),
            )

        # Add storage providers
        for provider in storage_providers:
            capabilities_text = ", ".join(provider.capabilities[:3])
            if len(provider.capabilities) > 3:
                capabilities_text += f" (+{len(provider.capabilities) - 3} more)"

            table.add_row(
                provider.name,
                "storage",
                provider.version,
                capabilities_text,
                (
                    provider.description[:50] + "..."
                    if len(provider.description) > 50
                    else provider.description
                ),
            )

        console.print(table)

        # Summary
        console.print("\n📊 [bold]Summary:[/bold]")
        console.print(
            f"   • Scraping Providers: [bold cyan]{len(scraping_providers)}[/bold cyan]"
        )
        console.print(
            f"   • Storage Providers: [bold magenta]{len(storage_providers)}[/bold magenta]"
        )
        console.print(f"   • Total: [bold]{len(providers)}[/bold]")

    except Exception as e:
        console.print(f"❌ Failed to list providers: {e}", style="red")
        sys.exit(1)


@providers.command()
@click.argument("provider_name")
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Configuration file for the provider (JSON format)",
)
@click.option(
    "--timeout",
    "-t",
    type=int,
    default=30,
    help="Test timeout in seconds",
)
@click.pass_context
def test(ctx, provider_name: str, config: Optional[str], timeout: int):
    """
    Test a provider connection.

    PROVIDER_NAME is the name of the provider to test.

    This command attempts to:
    - Create a provider instance
    - Initialize/connect with the provided configuration
    - Perform a basic health check

    Examples:

      # Test PostgreSQL with config file
      scrapper providers test postgresql --config pg_config.json

      # Test CSV provider (no config needed)
      scrapper providers test csv

      # Test with custom timeout
      scrapper providers test playwright --timeout 60
    """
    console = ctx.obj["console"]

    try:
        # Load configuration if provided
        provider_config = {}
        if config:
            console.print(f"📁 Loading configuration from: [bold]{config}[/bold]")
            with open(config, "r", encoding="utf-8") as f:
                provider_config = json.load(f)

        # Get provider factory
        factory = get_provider_factory()

        console.print(f"🔍 Testing provider: [bold cyan]{provider_name}[/bold cyan]")

        # Test the provider
        async def test_provider():
            try:
                connection_config = ConnectionConfig(provider_config)
                success = await asyncio.wait_for(
                    factory.test_provider(provider_name, connection_config),
                    timeout=timeout,
                )
                return success
            except asyncio.TimeoutError:
                return False

        success = asyncio.run(test_provider())

        if success:
            console.print("✅ [bold green]Provider test successful![/bold green]")
            console.print(f"   Provider: [bold]{provider_name}[/bold]")
            console.print("   Status: [bold green]Connected and healthy[/bold green]")
        else:
            console.print("❌ [bold red]Provider test failed![/bold red]", style="red")
            console.print(f"   Provider: [bold]{provider_name}[/bold]")
            console.print(
                "   Status: [bold red]Connection failed or unhealthy[/bold red]"
            )
            sys.exit(1)

    except FileNotFoundError:
        console.print(
            f"❌ Configuration file not found: [bold]{config}[/bold]", style="red"
        )
        sys.exit(1)
    except json.JSONDecodeError as e:
        console.print(f"❌ Invalid JSON in configuration file: {e}", style="red")
        sys.exit(1)
    except ValueError as e:
        # Provider not found or other validation errors
        console.print(f"❌ {e}", style="red")

        # Show available providers
        factory = get_provider_factory()
        providers = asyncio.run(factory.list_providers())
        provider_names = [p.name for p in providers]

        if provider_names:
            console.print(
                f"\n💡 Available providers: [dim]{', '.join(provider_names)}[/dim]"
            )

        sys.exit(1)
    except Exception as e:
        console.print(f"❌ Provider test failed: {e}", style="red")
        sys.exit(1)


@providers.command()
@click.argument("provider_name")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
@click.pass_context
def info(ctx, provider_name: str, format: str):
    """
    Get detailed information about a provider.

    PROVIDER_NAME is the name of the provider to inspect.

    Examples:

      # Get info about PostgreSQL provider
      scrapper providers info postgresql

      # Output as JSON
      scrapper providers info beautifulsoup --format json
    """
    console = ctx.obj["console"]

    try:
        # Get provider factory
        factory = get_provider_factory()

        # Get all providers and find the requested one
        providers = asyncio.run(factory.list_providers())
        provider = None

        for p in providers:
            if p.name == provider_name:
                provider = p
                break

        if not provider:
            console.print(
                f"❌ Provider not found: [bold]{provider_name}[/bold]", style="red"
            )

            # Show available providers
            provider_names = [p.name for p in providers]
            if provider_names:
                console.print(
                    f"💡 Available providers: [dim]{', '.join(provider_names)}[/dim]"
                )

            sys.exit(1)

        if format == "json":
            # Output as JSON
            provider_info = {
                "name": provider.name,
                "version": provider.version,
                "type": provider.provider_type,
                "capabilities": provider.capabilities,
                "description": provider.description,
            }
            console.print(json.dumps(provider_info, indent=2))
            return

        # Display as table
        console.print("\n📦 [bold]Provider Information[/bold]")

        info_table = Table(show_header=True, header_style="bold magenta")
        info_table.add_column("Property", style="cyan", width=15)
        info_table.add_column("Value", style="white")

        info_table.add_row("Name", provider.name)
        info_table.add_row("Type", provider.provider_type)
        info_table.add_row("Version", provider.version)
        info_table.add_row("Description", provider.description)

        console.print(info_table)

        # Capabilities
        if provider.capabilities:
            console.print("\n🚀 [bold]Capabilities[/bold]")
            for i, capability in enumerate(provider.capabilities, 1):
                console.print(f"   {i}. [green]{capability}[/green]")

    except Exception as e:
        console.print(f"❌ Failed to get provider info: {e}", style="red")
        sys.exit(1)
