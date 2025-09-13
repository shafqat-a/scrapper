# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a web scraper system built on a provider-based architecture that allows plugging in different scraping methods for different websites. The system uses JSON workflow definitions to configure scraping processes. **Updated to use Python for superior web scraping ecosystem and extensive library support.**

## Core Architecture

### Provider Model
- **Scraping Providers**: Different scraping strategies (Scrapy, BeautifulSoup, Playwright-Python)
- **Storage Providers**: Multiple data storage options (CSV, PostgreSQL, SQL Server, MongoDB, SQLite, JSON files)
- **Workflow Engine**: JSON-based workflow definition and execution with Python async support

### Scraping Workflow Process
1. **Init**: Navigate to target website URL and scan
2. **Discovery**: Analyze page structure to identify available data
3. **Extraction**: Scrape and grab identified data elements
4. **Pagination**: Navigate to additional pages if available
5. **Post-processing**: Optional data transformation and cleanup

### Key Components
- Workflow definitions stored as JSON files with strict Pydantic schema validation
- Command-based workflow steps (init, discover, extract, paginate)
- Pluggable provider system for both scraping and storage
- Support for multi-page scraping with navigation logic
- Rate limiting and anti-detection strategies using Python libraries
- CLI interface with Click and Rich for beautiful terminal output

## Technology Stack

### Language & Runtime
- **Python 3.11+** (superior web scraping ecosystem)
- **Scrapy** as primary industrial-grade web scraping framework
- **Playwright-Python** for JavaScript-heavy sites requiring browser automation
- **BeautifulSoup + Requests** for lightweight HTML parsing
- **Click + Rich** for beautiful CLI interface with progress bars

### Core Python Libraries
- **Pydantic v2**: Data validation and settings management with JSON schema generation
- **asyncio + aiohttp**: Async concurrency for I/O-bound operations
- **SQLAlchemy**: Database ORM for storage providers
- **tenacity**: Sophisticated retry logic with exponential backoff
- **fake-useragent**: User-Agent rotation for anti-detection

### Storage Providers
- **CSV**: Built-in csv module + pandas for large datasets
- **PostgreSQL**: psycopg2/asyncpg + SQLAlchemy
- **MongoDB**: pymongo + motor for async support
- **SQL Server**: pyodbc + SQLAlchemy
- **SQLite**: Built-in sqlite3 + SQLAlchemy (development/testing)
- **JSON Lines**: Built-in json module for streaming large datasets

### Testing Strategy
- **pytest** with pytest-asyncio for comprehensive test coverage
- **pytest-playwright** for browser-based E2E testing
- **Docker containers** for database integration tests with real backends
- **pytest fixtures** for reusable test data and mock objects

## Development Notes

### Constitutional Compliance
This project follows strict constitutional principles with Python-specific implementations:

1. **Library-First Architecture**: All features implemented as standalone Python packages
2. **Test-Driven Development**: RED-GREEN-Refactor cycle with pytest
3. **Provider Pattern**: Pluggable architecture using Python protocols and abstract base classes
4. **CLI Interface**: Click-based CLI with --help/--version/--format for each component
5. **Structured Logging**: Python logging with structured output and error context
6. **Real Dependencies**: Actual storage backends for integration tests via Docker

### Project Structure
```
src/
├── scraper_core/       # Core workflow engine (Pydantic models, workflow execution)
│   ├── models/         # Data models and validation
│   ├── workflow/       # Workflow execution engine
│   └── __init__.py
├── providers/          # Provider implementations
│   ├── scrapers/       # Scraping providers (Scrapy, Playwright, BeautifulSoup)
│   ├── storage/        # Storage providers (PostgreSQL, MongoDB, CSV, etc.)
│   └── __init__.py
└── cli/               # Click-based command interface
    ├── commands/       # CLI command implementations
    └── __init__.py

tests/
├── contract/          # Provider interface contract tests with pytest
├── integration/       # Full workflow integration tests with Docker
├── unit/             # Individual function unit tests
└── fixtures/         # Test data and reusable fixtures

pyproject.toml         # Poetry configuration with dependencies
requirements.txt       # pip requirements for compatibility
```

### Key Files and Locations

#### Specifications
- `/specs/001-read-spec-md/spec.md` - Feature specification
- `/specs/001-read-spec-md/plan.md` - Implementation plan (Python-based)
- `/specs/001-read-spec-md/research.md` - Python technology research and decisions
- `/specs/001-read-spec-md/data-model.md` - Data model definitions with Pydantic
- `/specs/001-read-spec-md/contracts/` - API contracts and Python interfaces

#### Python Contracts
- JSON Schema at `/specs/001-read-spec-md/contracts/workflow.schema.json`
- Python interfaces at `/specs/001-read-spec-md/contracts/provider-interfaces.py`
- CLI API documentation at `/specs/001-read-spec-md/contracts/cli-api.md`

#### Documentation
- `/specs/001-read-spec-md/quickstart.md` - Python-based user onboarding guide

### Provider Development Guidelines

When implementing new Python providers:

1. **Implement Provider Protocol**: Follow contracts in `provider-interfaces.py`
2. **Use Abstract Base Classes**: Inherit from `BaseScraper` or `BaseStorage`
3. **Pydantic Configuration**: Use Pydantic models for all configuration classes
4. **Async Implementation**: Use asyncio for all I/O operations
5. **Error Handling**: Use tenacity for retry logic with exponential backoff
6. **Anti-Detection**: Leverage fake-useragent, session management, proxy support
7. **Resource Cleanup**: Proper cleanup in async context managers

### CLI Commands Structure
- `scrapper run <workflow.json>` - Execute workflow
- `scrapper validate <workflow.json>` - Validate workflow with Pydantic
- `scrapper providers list` - List available providers
- `scrapper providers test <name>` - Test provider connection

### Workflow JSON Example (Python-optimized)
```json
{
  "version": "1.0.0",
  "metadata": { "name": "Example", "targetSite": "https://example.com" },
  "scraping": {
    "provider": "scrapy",
    "config": {
      "concurrentRequests": 16,
      "downloadDelay": 1.0,
      "robotstxtObey": true
    }
  },
  "storage": {
    "provider": "postgresql",
    "config": {
      "connectionString": "postgresql://localhost/data",
      "tableName": "scraped_items"
    }
  },
  "steps": [
    { "id": "init", "command": "init", "config": { "url": "https://example.com" } },
    { "id": "extract", "command": "extract", "config": { "elements": {} } }
  ]
}
```

### Performance Goals (Python-optimized)
- Support 10-100 concurrent scrapers (asyncio.Semaphore)
- Memory usage cap at 1GB per workflow
- Rate limiting: 1-50 requests per second (configurable per site)
- Graceful degradation with memory monitoring (tracemalloc)

### Testing Requirements
- Contract tests validate provider protocols using pytest
- Integration tests use real websites (Flask/FastAPI test servers)
- E2E tests execute full workflows with Docker-based storage
- Real storage backends required (Docker containers for CI)
- Tests must fail before implementation (TDD with pytest)

### Python-Specific Development Features

#### Virtual Environment Setup
```bash
python -m venv scraper-env
source scraper-env/bin/activate
pip install -e .[dev]  # Editable install with dev dependencies
```

#### Poetry Development
```bash
poetry install                    # Install dependencies
poetry run pytest               # Run tests
poetry run scrapper run workflow.json  # Run CLI
poetry build                    # Build distribution packages
```

#### Development Tools Integration
- **Black**: Code formatting (`poetry run black .`)
- **isort**: Import sorting (`poetry run isort .`)
- **mypy**: Type checking (`poetry run mypy src/`)
- **pytest**: Testing (`poetry run pytest -v`)
- **pre-commit**: Git hooks for code quality

#### Interactive Development
```python
# IPython/Jupyter integration for workflow development
import asyncio
from scraper_core.workflow import WorkflowEngine
from scraper_core.models import Workflow

# Load and test workflow interactively
engine = WorkflowEngine()
workflow = Workflow.parse_file('workflow.json')
result = asyncio.run(engine.execute(workflow))
```

### Python Packaging and Distribution

#### PyPI Package Structure
- **Main package**: `web-scrapper-cli`
- **Provider packages**: `scrapper-provider-{name}` (e.g., `scrapper-provider-scrapy`)
- **Optional dependencies**: `pip install web-scrapper-cli[scrapy,playwright]`

#### Docker Integration
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN pip install -e .
CMD ["scrapper", "--help"]
```

### Recent Changes (Python Migration)
- **Language switch**: Migrated from Node.js/TypeScript to Python 3.11+
- **Provider architecture**: Implemented with Python protocols and ABC
- **Async architecture**: Built on asyncio and aiohttp
- **Data validation**: Using Pydantic v2 for schemas and validation
- **CLI framework**: Click with Rich for beautiful terminal output
- **Testing framework**: pytest with async support and Docker integration
- **Package management**: Poetry for modern Python dependency management

## Implementation Status
- **Phase 0**: Research complete ✓ (Python-based decisions)
- **Phase 1**: Design and contracts complete ✓ (Python interfaces)
- **Phase 2**: Task planning ready (awaiting /tasks command)
- **Phase 3-5**: Implementation pending

## Python-Specific Best Practices

### Code Style
- **PEP 8**: Follow Python style guide
- **Type hints**: Use typing module for all public APIs
- **Docstrings**: Google-style docstrings for all modules, classes, and functions
- **Async/await**: Prefer async/await over callbacks for I/O operations

### Error Handling
```python
# Use tenacity for retry logic
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def scrape_with_retry(url: str) -> str:
    # Scraping implementation with automatic retries
    pass
```

### Configuration Management
```python
# Use Pydantic for configuration
from pydantic import BaseSettings

class ScrapperSettings(BaseSettings):
    log_level: str = "INFO"
    max_concurrent: int = 10
    default_timeout: int = 30000

    class Config:
        env_prefix = "SCRAPPER_"
```

This project leverages Python's superior web scraping ecosystem while maintaining constitutional compliance and the same JSON-based workflow approach. The provider pattern ensures extensibility while Python's rich library ecosystem provides robust scraping, data processing, and storage capabilities.
