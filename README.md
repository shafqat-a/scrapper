# Web Scrapper CLI

Provider-based web scraping system with pluggable scraping and storage providers.

## Features

- **Provider-based architecture**: Pluggable scraping providers (Scrapy, Playwright, BeautifulSoup)
- **Multiple storage options**: CSV, PostgreSQL, MongoDB, SQLite, JSON
- **JSON workflow definitions**: Declarative scraping workflows
- **Async execution**: High-performance concurrent scraping
- **Anti-detection**: User-agent rotation, rate limiting, proxy support
- **CLI interface**: Beautiful terminal output with progress tracking

## Quick Start

```bash
# Install
pip install web-scrapper-cli

# Run a workflow
scrapper run workflow.json

# Validate workflow
scrapper validate workflow.json

# List providers
scrapper providers list
```

## Development

This project uses Poetry for dependency management:

```bash
# Install dependencies
poetry install

# Run tests
poetry run pytest

# Format code
poetry run black .
poetry run isort .

# Type checking
poetry run mypy src/
```

## License

MIT License
