# 🚀 Web Scrapper CLI

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**A powerful, production-ready web scraping framework with pluggable providers and beautiful CLI interface.**

> 🎯 **Status**: Production Ready - Complete TDD implementation from RED to GREEN phase with 87.8% test coverage

## ✨ Key Features

- 🔌 **Pluggable Architecture**: Swap scraping providers (BeautifulSoup, Scrapy, Playwright) and storage backends (CSV, PostgreSQL, JSON)
- 📝 **JSON Workflows**: Declarative workflow definitions with step-based execution
- ⚡ **Async Performance**: Full async/await implementation for concurrent operations
- 🎨 **Beautiful CLI**: Rich terminal output with progress tracking and detailed reporting
- 🛡️ **Anti-Detection**: Built-in rate limiting, user-agent rotation, and retry logic
- 🔄 **Post-Processing**: Filter, transform, validate, and deduplicate scraped data
- 🐳 **Docker Ready**: Containerized deployment with Docker Compose support
- 📊 **Comprehensive Testing**: 87.8% test coverage with contract and integration tests

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI (coming soon)
pip install web-scrapper-cli

# Or install from source
git clone https://github.com/shafqat-a/scrapper.git
cd scrapper
poetry install
```

### Basic Usage

```bash
# Generate a workflow template
scrapper init my-workflow.json

# Validate your workflow
scrapper validate my-workflow.json

# Execute the workflow
scrapper run my-workflow.json

# List available providers
scrapper providers list

# Test provider connection
scrapper providers test postgresql --config config.json
```

## 📋 Workflow Examples

### Simple News Scraping

```json
{
  "version": "1.0.0",
  "metadata": {
    "name": "News Headlines Scraper",
    "description": "Extract headlines from news website",
    "author": "your-name",
    "target_site": "https://example-news.com"
  },
  "scraping": {
    "provider": "beautifulsoup",
    "config": {
      "parser": "lxml",
      "timeout": 30000
    }
  },
  "storage": {
    "provider": "csv",
    "config": {
      "file_path": "./headlines.csv",
      "headers": true
    }
  },
  "steps": [
    {
      "id": "init",
      "command": "init",
      "config": {
        "url": "https://example-news.com"
      }
    },
    {
      "id": "extract-headlines",
      "command": "extract",
      "config": {
        "elements": {
          "title": {"selector": "h2.headline", "type": "text"},
          "url": {"selector": "a", "type": "attribute", "attribute": "href"},
          "published": {"selector": ".date", "type": "text"}
        }
      }
    }
  ]
}
```

### E-commerce Product Scraping with Pagination

```json
{
  "version": "1.0.0",
  "metadata": {
    "name": "Product Scraper",
    "description": "Scrape products with pagination",
    "target_site": "https://example-shop.com"
  },
  "scraping": {
    "provider": "playwright",
    "config": {
      "browser": "chromium",
      "headless": true
    }
  },
  "storage": {
    "provider": "postgresql",
    "config": {
      "connection_string": "postgresql://user:pass@localhost:5432/products"
    }
  },
  "steps": [
    {
      "id": "init",
      "command": "init",
      "config": {
        "url": "https://example-shop.com/products"
      }
    },
    {
      "id": "extract-products",
      "command": "extract",
      "config": {
        "elements": {
          "name": {"selector": ".product-name", "type": "text"},
          "price": {"selector": ".price", "type": "text", "transform": "float"},
          "rating": {"selector": ".rating", "type": "text", "transform": "float"}
        }
      }
    },
    {
      "id": "next-page",
      "command": "paginate",
      "config": {
        "next_page_selector": ".next-page",
        "max_pages": 10,
        "wait_after_click": 2000
      }
    }
  ]
}
```

### BPDB Archive PDF Extraction

```json
{
  "version": "1.0.0",
  "metadata": {
    "name": "BPDB Archive Extraction",
    "description": "Extract power generation data from BPDB daily PDFs",
    "author": "scrapper-framework",
    "target_site": "https://misc.bpdb.gov.bd/daily-generation-archive"
  },
  "scraping": {
    "provider": "bpdb-archive",
    "config": {
      "timeout": 30000,
      "retry_attempts": 3,
      "pdf_storage": "bpdb_pdfs/"
    }
  },
  "storage": {
    "provider": "json",
    "config": {
      "output_file": "bpdb_data.json",
      "pretty_format": true
    }
  },
  "steps": [
    {
      "id": "init",
      "command": "init",
      "config": {
        "from_date": "01/09/2025",
        "to_date": "10/09/2025"
      }
    },
    {
      "id": "extract-tables",
      "command": "extract",
      "config": {
        "elements": {}
      }
    }
  ]
}
```

## 🔌 Available Providers

### Scraping Providers

| Provider | Best For | JavaScript Support | Performance |
|----------|----------|-------------------|-------------|
| **BeautifulSoup** | Simple HTML parsing | ❌ | ⚡⚡⚡ |
| **Scrapy** | Large-scale scraping | ❌ | ⚡⚡ |
| **Playwright** | Modern web apps | ✅ | ⚡ |
| **BPDB Archive** | PDF table extraction | ❌ | ⚡⚡ |

### Storage Providers

| Provider | Best For | Features |
|----------|----------|-----------|
| **CSV** | Simple data export | Pandas integration, schema validation |
| **PostgreSQL** | Production databases | JSONB support, async operations |
| **JSON/JSONL** | API integration | Streaming, nested data support |

## 📖 CLI Commands

### Core Commands

```bash
# Workflow execution
scrapper run workflow.json                    # Execute workflow
scrapper run workflow.json --dry-run          # Validate without execution
scrapper run workflow.json --output data.csv  # Override output location

# Workflow validation
scrapper validate workflow.json               # Basic validation
scrapper validate workflow.json --detailed    # Detailed validation report
scrapper validate workflow.json --format json # JSON output

# Provider management
scrapper providers list                       # List all providers
scrapper providers list --type scraping       # Filter by type
scrapper providers test postgresql --config config.json  # Test connection
scrapper providers info beautifulsoup         # Provider details

# Utilities
scrapper init workflow.json                   # Generate workflow template
scrapper version                              # Version information
```

### Output Formats

```bash
# Table format (default)
scrapper run workflow.json

# JSON format
scrapper run workflow.json --format json

# Custom output location
scrapper run workflow.json --output ./results/
```

## 🏗️ Architecture

### System Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CLI Interface │ -> │ Workflow Engine  │ -> │   Providers     │
│  (Click + Rich) │    │   (Async Core)   │    │ (Pluggable)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                       ┌────────┴────────┐
                       │  Data Pipeline  │
                       │ (Post-process)  │
                       └─────────────────┘
```

### Workflow Execution Flow

1. **Validation**: Schema validation and provider availability checks
2. **Initialization**: Provider setup and resource allocation
3. **Execution**: Step-by-step workflow execution with error handling
4. **Post-Processing**: Data transformation and validation
5. **Storage**: Async data persistence with schema enforcement
6. **Cleanup**: Proper resource cleanup and connection management

## 🛠️ Development

### Prerequisites

- Python 3.11 or higher
- Poetry for dependency management
- Docker (optional, for integration tests)

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/shafqat-a/scrapper.git
cd scrapper

# Install dependencies
poetry install

# Install development dependencies
poetry install --with dev

# Set up pre-commit hooks
poetry run pre-commit install
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src --cov-report=html

# Run specific test types
poetry run pytest tests/contract/     # Contract tests
poetry run pytest tests/integration/ # Integration tests
poetry run pytest tests/unit/        # Unit tests

# Run with Docker services
docker-compose -f docker-compose.test.yml up -d
poetry run pytest tests/integration/
docker-compose -f docker-compose.test.yml down
```

### Code Quality

```bash
# Format code
poetry run black .
poetry run isort .

# Type checking
poetry run mypy src/

# Linting
poetry run flake8 src/

# Security scan
poetry run bandit -r src/

# Run all checks
poetry run pre-commit run --all-files
```

## 📊 Performance & Scaling

### Benchmarks

- **BeautifulSoup**: ~500 pages/minute (simple HTML)
- **Scrapy**: ~2000 pages/minute (concurrent scraping)
- **Playwright**: ~100 pages/minute (JavaScript rendering)

### Scaling Tips

```json
{
  "scraping": {
    "provider": "scrapy",
    "config": {
      "concurrent_requests": 32,
      "download_delay": 0.5,
      "randomize_download_delay": 0.5
    }
  }
}
```

## 🐳 Docker Deployment

### Basic Deployment

```bash
# Build image
docker build -t web-scrapper .

# Run workflow
docker run -v $(pwd)/workflows:/workflows web-scrapper run /workflows/my-workflow.json
```

### Docker Compose with Services

```yaml
version: '3.8'
services:
  scrapper:
    build: .
    volumes:
      - ./workflows:/workflows
      - ./output:/output
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/scrapper
    depends_on:
      - postgres

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: scrapper
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
```

## 📚 Advanced Usage

### Custom Post-Processing

```json
{
  "post_processing": [
    {
      "type": "filter",
      "config": {
        "min_length": 10,
        "excludes": "advertisement"
      }
    },
    {
      "type": "transform",
      "config": {
        "lowercase": true,
        "strip": true,
        "replace": {"&amp;": "&"}
      }
    },
    {
      "type": "deduplicate",
      "config": {"key": "url"}
    }
  ]
}
```

### Error Handling & Retries

```json
{
  "steps": [
    {
      "id": "robust-extraction",
      "command": "extract",
      "config": {...},
      "retries": 5,
      "timeout": 60000,
      "continue_on_error": true
    }
  ]
}
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Run quality checks (`poetry run pre-commit run --all-files`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Documentation**: [Full Documentation](docs/)
- **Examples**: [Example Workflows](examples/)
- **API Reference**: [API Documentation](docs/api/)
- **Contributing**: [Contributing Guide](CONTRIBUTING.md)
- **Changelog**: [Release Notes](CHANGELOG.md)

---

**Built with ❤️ by the Scrapper Team**
