# CLI Reference

Complete reference for all Web Scrapper CLI commands, options, and usage patterns.

## 📋 Command Overview

```bash
scrapper <command> [options] [arguments]
```

### Available Commands

| Command | Description | Usage |
|---------|-------------|--------|
| `run` | Execute a workflow | `scrapper run workflow.json` |
| `validate` | Validate workflow configuration | `scrapper validate workflow.json` |
| `providers` | Manage providers | `scrapper providers <subcommand>` |
| `init` | Create workflow template | `scrapper init workflow.json` |
| `--help` | Show help information | `scrapper --help` |
| `--version` | Show version information | `scrapper --version` |

## 🚀 scrapper run

Execute a workflow from a JSON configuration file.

### Syntax
```bash
scrapper run <workflow-file> [options]
```

### Arguments
- `workflow-file` - Path to the workflow JSON file (required)

### Options

| Option | Short | Type | Description | Default |
|--------|-------|------|-------------|---------|
| `--format` | `-f` | string | Output format: `human`, `json`, `csv` | `human` |
| `--output` | `-o` | string | Save execution log to file | - |
| `--silent` | `-s` | flag | Suppress progress output | `false` |
| `--dry-run` | | flag | Validate workflow without executing | `false` |
| `--concurrent` | `-c` | number | Max concurrent operations | `5` |
| `--timeout` | `-t` | number | Global timeout in seconds | `300` |
| `--debug` | `-d` | flag | Enable debug logging | `false` |
| `--config` | | string | Path to global config file | - |

### Examples

**Basic execution:**
```bash
scrapper run my-workflow.json
```

**With custom output format:**
```bash
scrapper run workflow.json --format json --output results.log
```

**Silent mode with high concurrency:**
```bash
scrapper run workflow.json --silent --concurrent 10
```

**Dry run validation:**
```bash
scrapper run workflow.json --dry-run
```

### Output Formats

#### Human (Default)
```
🚀 Starting workflow: News Scraper
📋 Target: https://example-news.com

▶  Executing step: navigate
   → Navigating to https://example-news.com
   ✓ Page loaded successfully (1.2s)

▶  Executing step: extract-news
   → Extracting elements with selectors
   → Found 15 items
   ✓ Extracted 15 items (2.3s)

✅ Workflow completed successfully!

Results Summary:
  📊 Items scraped: 15
  ⏱  Total time: 3.7 seconds
  💾 Output: ./news-headlines.csv
  🔄 Success rate: 100%
```

#### JSON
```json
{
  "workflow": {
    "name": "News Scraper",
    "status": "completed",
    "started_at": "2025-01-15T10:30:00Z",
    "completed_at": "2025-01-15T10:30:03Z",
    "duration": 3.7
  },
  "steps": [
    {
      "id": "navigate", 
      "status": "completed",
      "duration": 1.2,
      "retries": 0
    },
    {
      "id": "extract-news",
      "status": "completed", 
      "duration": 2.3,
      "items_extracted": 15
    }
  ],
  "results": {
    "total_items": 15,
    "success_rate": 1.0,
    "storage": {
      "provider": "csv",
      "location": "./news-headlines.csv"
    }
  }
}
```

#### CSV
```csv
step_id,status,duration,items_extracted,errors
navigate,completed,1.2,0,0
extract-news,completed,2.3,15,0
```

### Exit Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 0 | Success | Workflow completed successfully |
| 1 | Validation Error | Invalid workflow configuration |
| 2 | Execution Error | Error during workflow execution |
| 3 | Storage Error | Failed to store results |
| 4 | Provider Error | Provider initialization failed |
| 5 | Timeout Error | Workflow execution timed out |

## ✅ scrapper validate

Validate workflow configuration without execution.

### Syntax
```bash
scrapper validate <workflow-file> [options]
```

### Arguments  
- `workflow-file` - Path to the workflow JSON file (required)

### Options

| Option | Short | Type | Description | Default |
|--------|-------|------|-------------|---------|
| `--detailed` | `-d` | flag | Show detailed validation results | `false` |
| `--format` | `-f` | string | Output format: `human`, `json` | `human` |
| `--schema` | | flag | Validate against JSON schema only | `false` |
| `--providers` | | flag | Check provider availability | `true` |

### Examples

**Basic validation:**
```bash
scrapper validate workflow.json
```

**Detailed validation:**
```bash
scrapper validate workflow.json --detailed
```

**JSON output:**
```bash
scrapper validate workflow.json --format json
```

### Output

#### Success (Human)
```
✓ Workflow schema validation passed
✓ Provider 'beautifulsoup' available
✓ Provider 'csv' available  
✓ All workflow steps valid
✓ Configuration complete
✓ Workflow ready to execute

Summary:
  Name: News Scraper
  Steps: 2 (navigate, extract-news)
  Providers: beautifulsoup → csv
  Estimated runtime: 30-60 seconds
```

#### Error (Human)
```
❌ Validation failed

Errors found:
  • Line 15: Invalid provider name 'invalid_provider'
  • Line 23: Missing required field 'url' in init step
  • Line 34: Invalid selector syntax in extract step

Warnings:
  • Consider adding retries to step 'extract-news'
  • No post-processing configured - data may need cleaning

Fix these issues before running the workflow.
```

#### JSON Output
```json
{
  "valid": true,
  "errors": [],
  "warnings": [
    "Consider adding retries to step 'extract-news'"
  ],
  "summary": {
    "name": "News Scraper",
    "steps": 2,
    "providers": ["beautifulsoup", "csv"],
    "estimated_runtime": "30-60 seconds"
  }
}
```

## 🔌 scrapper providers

Manage and inspect available providers.

### Subcommands

| Subcommand | Description | Usage |
|------------|-------------|-------|
| `list` | List all available providers | `scrapper providers list` |
| `show` | Show provider details | `scrapper providers show <name>` |
| `test` | Test provider connection | `scrapper providers test <name>` |
| `install` | Install provider dependencies | `scrapper providers install <name>` |

### scrapper providers list

List all available providers.

```bash
scrapper providers list [options]
```

#### Options
- `--type` - Filter by provider type: `scraping`, `storage`
- `--format` - Output format: `human`, `json`, `csv`

#### Example Output
```
┌─────────────┬─────────────┬─────────┬──────────────────────────┐
│ Provider    │ Type        │ Version │ Description              │
├─────────────┼─────────────┼─────────┼──────────────────────────┤
│ beautifulsoup│ scraping   │ 1.0.0   │ HTML parsing, lightweight│
│ scrapy      │ scraping    │ 1.0.0   │ Industrial-grade scraper │
│ playwright  │ scraping    │ 1.0.0   │ Browser automation       │
│ csv         │ storage     │ 1.0.0   │ CSV file storage         │
│ json        │ storage     │ 1.0.0   │ JSON file storage        │
│ postgresql  │ storage     │ 1.0.0   │ PostgreSQL database      │
│ mongodb     │ storage     │ 1.0.0   │ MongoDB database         │
└─────────────┴─────────────┴─────────┴──────────────────────────┘
```

### scrapper providers show

Show detailed information about a specific provider.

```bash
scrapper providers show <provider-name> [options]
```

#### Example
```bash
scrapper providers show playwright
```

#### Output
```
Provider: playwright
Type: scraping
Version: 1.0.0
Status: ✓ Available

Description:
  Browser automation provider using Playwright. Supports JavaScript
  execution, screenshots, and complex user interactions.

Capabilities:
  • JavaScript execution
  • Multiple browsers (Chromium, Firefox, WebKit)
  • Screenshots and PDFs
  • Mobile device emulation
  • Network interception

Configuration Options:
  browser       string    Browser type (chromium|firefox|webkit)
  headless      boolean   Run in headless mode
  viewport      object    Browser viewport size
  timeout       number    Navigation timeout (ms)
  proxy         string    Proxy server URL

Dependencies:
  ✓ playwright>=1.38.0
  ✓ Browser binaries installed

Example Configuration:
{
  "provider": "playwright",
  "config": {
    "browser": "chromium",
    "headless": true,
    "timeout": 30000
  }
}
```

### scrapper providers test

Test connection to a specific provider.

```bash
scrapper providers test <provider-name> [options]
```

#### Options
- `--config` - Path to configuration file for provider
- `--format` - Output format: `human`, `json`

#### Examples

**Test scraping provider:**
```bash
scrapper providers test playwright
```

**Test storage provider with config:**
```bash
scrapper providers test postgresql --config db-config.json
```

#### Output
```
Testing provider: postgresql

✓ Provider loaded successfully
✓ Configuration valid
✓ Database connection established
✓ Required permissions available
✓ Test write operation successful

Connection Details:
  Host: localhost:5432
  Database: scrapper_data
  User: scrapper_user
  Tables: 3 existing
  Free space: 15.2 GB

✅ Provider test passed
```

## 🆕 scrapper init

Create a new workflow template.

### Syntax
```bash
scrapper init <workflow-file> [options]
```

### Options

| Option | Short | Type | Description | Default |
|--------|-------|------|-------------|---------|
| `--template` | `-t` | string | Template type | `basic` |
| `--provider` | `-p` | string | Scraping provider | `beautifulsoup` |
| `--storage` | `-s` | string | Storage provider | `csv` |
| `--url` | `-u` | string | Target URL | - |
| `--interactive` | `-i` | flag | Interactive template creation | `false` |

### Templates

| Template | Description | Use Case |
|----------|-------------|----------|
| `basic` | Simple single-page scraper | Static websites |
| `pagination` | Multi-page scraper | Paginated content |
| `ecommerce` | Product listing scraper | E-commerce sites |
| `news` | News article scraper | News websites |
| `social` | Social media scraper | Social platforms |

### Examples

**Basic template:**
```bash
scrapper init my-workflow.json
```

**E-commerce template with Playwright:**
```bash
scrapper init shop-scraper.json --template ecommerce --provider playwright
```

**Interactive creation:**
```bash
scrapper init workflow.json --interactive
```

#### Interactive Mode
```
🚀 Web Scrapper CLI - Workflow Creator

? What type of website are you scraping? (Use arrow keys)
  ❯ News/Blog Articles
    E-commerce Products  
    Job Listings
    Social Media Posts
    Custom

? What's the target URL? https://example-shop.com

? Which scraping provider? (Use arrow keys)
    BeautifulSoup (Simple HTML parsing)
  ❯ Playwright (JavaScript support)
    Scrapy (Industrial-grade)

? Where should results be stored? (Use arrow keys)
  ❯ CSV File
    JSON File
    PostgreSQL Database
    MongoDB Database

? Enable pagination support? (y/N) y

✅ Workflow template created: workflow.json
📝 Edit the file to customize selectors and configuration
🚀 Run with: scrapper validate workflow.json
```

## 🔧 Global Options

These options work with all commands:

| Option | Description | Example |
|--------|-------------|---------|
| `--config` | Global configuration file | `--config /path/to/config.json` |
| `--log-level` | Logging verbosity | `--log-level DEBUG` |
| `--no-color` | Disable colored output | `--no-color` |
| `--version` | Show version and exit | `--version` |
| `--help` | Show help and exit | `--help` |

### Global Configuration File

Create a `~/.scrapper/config.json` file for default settings:

```json
{
  "defaults": {
    "timeout": 60000,
    "retries": 3,
    "concurrent": 5,
    "user_agent": "scrapper/1.0.0 (custom)"
  },
  "providers": {
    "beautifulsoup": {
      "parser": "lxml",
      "verify_ssl": true
    },
    "postgresql": {
      "connection_string": "postgresql://localhost/scrapper"
    }
  },
  "logging": {
    "level": "INFO",
    "file": "~/.scrapper/logs/scrapper.log"
  }
}
```

## 🌍 Environment Variables

Configure scrapper behavior with environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `SCRAPPER_CONFIG_FILE` | Path to global config file | `~/.scrapper/config.json` |
| `SCRAPPER_LOG_LEVEL` | Logging level | `INFO` |
| `SCRAPPER_DATA_DIR` | Data storage directory | `./data` |
| `SCRAPPER_CACHE_DIR` | Cache directory | `~/.scrapper/cache` |
| `SCRAPPER_USER_AGENT` | Default User-Agent string | `scrapper/1.0.0` |
| `SCRAPPER_TIMEOUT` | Default timeout (seconds) | `300` |

### Example Usage
```bash
export SCRAPPER_LOG_LEVEL=DEBUG
export SCRAPPER_DATA_DIR=/tmp/scrapper-data
scrapper run workflow.json
```

## 🐳 Docker Usage

Run scrapper in Docker containers:

### Basic Usage
```bash
# Run workflow
docker run --rm -v $(pwd):/workspace \
  ghcr.io/shafqat-a/scrapper:latest \
  scrapper run /workspace/workflow.json

# Validate workflow  
docker run --rm -v $(pwd):/workspace \
  ghcr.io/shafqat-a/scrapper:latest \
  scrapper validate /workspace/workflow.json
```

### With Custom Configuration
```bash
docker run --rm \
  -v $(pwd)/workflows:/app/workflows \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/config.json:/app/config.json \
  -e SCRAPPER_CONFIG_FILE=/app/config.json \
  ghcr.io/shafqat-a/scrapper:latest \
  scrapper run /app/workflows/my-workflow.json
```

## 🔍 Troubleshooting

### Common Issues and Solutions

#### Command not found
```bash
# Issue: scrapper: command not found
# Solution: Ensure scrapper is in PATH
pip install --user web-scrapper-cli
export PATH=$PATH:~/.local/bin
```

#### Permission denied
```bash
# Issue: Permission denied writing output
# Solution: Check file permissions or use different output directory
scrapper run workflow.json --output ~/scrapper-output/results.csv
```

#### Provider not available
```bash
# Issue: Provider 'playwright' not available
# Solution: Install provider dependencies
pip install web-scrapper-cli[playwright]
playwright install
```

#### Memory issues
```bash
# Issue: Out of memory during large scraping
# Solution: Reduce concurrency and enable batching
scrapper run workflow.json --concurrent 2 --config low-memory.json
```

### Debug Mode

Enable verbose logging for troubleshooting:

```bash
# Enable debug logging
scrapper run workflow.json --debug

# Or with environment variable
SCRAPPER_LOG_LEVEL=DEBUG scrapper run workflow.json
```

### Log Files

Scrapper logs execution details to help diagnose issues:

- **Console output**: Real-time progress and errors
- **Log files**: Detailed execution history (if configured)
- **Debug mode**: Verbose internal operations

---

## 🎯 Next Steps

- **[Workflow Configuration](../user-guide/workflow-configuration.md)** - Detailed configuration options
- **[Error Handling](../user-guide/error-handling.md)** - Troubleshooting guide
- **[Examples](../examples/basic.md)** - Practical usage examples
- **[Best Practices](../examples/best-practices.md)** - Production deployment

---

This reference covers all CLI commands and options available in Web Scrapper CLI.