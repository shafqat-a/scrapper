# CLI API Contract (Python Implementation)

## Command Structure

### scrapper run
Execute a workflow from JSON configuration file.

**Usage**: `scrapper run <workflow-file> [options]`

**Arguments**:
- `workflow-file`: Path to workflow JSON file (required)

**Options**:
- `--format <format>`: Output format (human|json|csv) [default: human]
- `--silent`: Suppress progress output
- `--dry-run`: Validate workflow without executing
- `--concurrent <number>`: Max concurrent pages [default: 5]
- `--output <file>`: Save execution log to file

**Exit Codes**:
- 0: Success
- 1: Workflow validation error
- 2: Execution error
- 3: Storage error
- 4: Provider not found

**Output Formats**:

*Human (default)*:
```
✓ Workflow validated successfully
▶ Executing step: init
  → Navigating to https://example.com
▶ Executing step: discover
  → Found 25 data elements
▶ Executing step: extract
  → Extracted 25 records
▶ Executing step: paginate
  → Moving to next page (2/5)
✓ Workflow completed successfully
📊 Total records: 125
💾 Stored in: postgres://localhost/scraped_data
```

*JSON*:
```json
{
  "status": "completed",
  "workflow": {
    "id": "example-workflow",
    "startTime": "2025-09-13T10:00:00Z",
    "endTime": "2025-09-13T10:05:30Z",
    "duration": 330000
  },
  "execution": {
    "steps": [
      {
        "id": "init",
        "status": "completed",
        "duration": 2000,
        "output": {"url": "https://example.com", "title": "Example Site"}
      }
    ]
  },
  "results": {
    "totalRecords": 125,
    "storage": {
      "provider": "postgresql",
      "location": "postgres://localhost/scraped_data"
    }
  }
}
```

### scrapper validate
Validate workflow JSON schema and provider availability.

**Usage**: `scrapper validate <workflow-file> [options]`

**Arguments**:
- `workflow-file`: Path to workflow JSON file (required)

**Options**:
- `--schema-only`: Only validate JSON schema, skip provider checks
- `--format <format>`: Output format (human|json) [default: human]

**Exit Codes**:
- 0: Valid
- 1: Schema validation error
- 2: Provider validation error

### scrapper providers
Manage and inspect available providers.

#### scrapper providers list
List all available providers.

**Usage**: `scrapper providers list [options]`

**Options**:
- `--type <type>`: Filter by provider type (scraping|storage)
- `--format <format>`: Output format (human|json|table) [default: table]

**Output Example**:
```
┌─────────────┬─────────────┬─────────┬──────────────────────────┐
│ Provider    │ Type        │ Version │ Capabilities             │
├─────────────┼─────────────┼─────────┼──────────────────────────┤
│ playwright  │ scraping    │ 1.0.0   │ js-rendering, cookies    │
│ cheerio     │ scraping    │ 1.0.0   │ static-html              │
│ postgresql  │ storage     │ 1.0.0   │ relational, transactions │
│ csv         │ storage     │ 1.0.0   │ file-based, portable     │
└─────────────┴─────────────┴─────────┴──────────────────────────┘
```

#### scrapper providers test
Test connectivity to a specific provider.

**Usage**: `scrapper providers test <provider-name> [options]`

**Arguments**:
- `provider-name`: Name of provider to test (required)

**Options**:
- `--config <file>`: Configuration file for provider connection
- `--format <format>`: Output format (human|json) [default: human]

### scrapper --version
Display version information.

**Usage**: `scrapper --version`

**Output Example**:
```
scrapper version 0.1.0
Python 3.11.5
Platform: darwin-arm64
```

### scrapper --help
Display help information.

**Usage**: `scrapper --help`

## Error Handling

### Error Response Format

**Human Format**:
```
❌ Error: Workflow validation failed
   └─ Step 'extract': Invalid selector '.non-existent'
   └─ Storage config missing required field 'connectionString'

💡 Fix suggestions:
   • Check CSS selector syntax in extract step
   • Add connectionString to storage configuration
```

**JSON Format**:
```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Workflow validation failed",
    "details": [
      {
        "step": "extract",
        "field": "selector",
        "message": "Invalid selector '.non-existent'"
      },
      {
        "section": "storage.config",
        "field": "connectionString",
        "message": "Missing required field"
      }
    ]
  },
  "suggestions": [
    "Check CSS selector syntax in extract step",
    "Add connectionString to storage configuration"
  ]
}
```

### Common Error Codes

- `SCHEMA_VALIDATION_ERROR`: JSON schema validation failed
- `PROVIDER_NOT_FOUND`: Specified provider not available
- `CONNECTION_ERROR`: Unable to connect to storage provider
- `EXTRACTION_ERROR`: Data extraction failed
- `TIMEOUT_ERROR`: Operation exceeded timeout limit
- `RATE_LIMIT_ERROR`: Rate limit exceeded
- `AUTHENTICATION_ERROR`: Invalid credentials for provider

## Environment Variables

### Configuration
- `SCRAPPER_LOG_LEVEL`: Logging level (debug|info|warn|error) [default: info]
- `SCRAPPER_USER_AGENT`: Default user agent string
- `SCRAPPER_TIMEOUT`: Default timeout in milliseconds [default: 30000]

### Storage Providers
- `POSTGRES_CONNECTION_STRING`: Default PostgreSQL connection
- `MONGODB_CONNECTION_STRING`: Default MongoDB connection
- `MSSQL_CONNECTION_STRING`: Default SQL Server connection

### Scraping Providers
- `SCRAPPER_BROWSER_PATH`: Custom browser executable path
- `SCRAPPER_PROXY_URL`: Default proxy server URL

## Configuration Files

### Global Configuration
Location: `~/.scrapper/config.json`

```json
{
  "defaults": {
    "timeout": 30000,
    "retries": 3,
    "rateLimit": {
      "requestsPerSecond": 2
    },
    "browser": {
      "headless": true,
      "userAgent": "scrapper/0.1.0"
    }
  },
  "providers": {
    "postgresql": {
      "connectionString": "postgres://localhost/scrapper"
    }
  }
}
```

### Project Configuration
Location: `./scrapper.config.json`

```json
{
  "workflowsDir": "./workflows",
  "outputDir": "./output",
  "logLevel": "info",
  "providers": {
    "storage": {
      "default": "postgresql"
    },
    "scraping": {
      "default": "playwright"
    }
  }
}
```

## Plugin System

### Provider Registration
Providers can be registered as npm packages following naming convention:
- Scraping providers: `scrapper-provider-{name}`
- Storage providers: `scrapper-storage-{name}`

### Provider Discovery
CLI automatically discovers providers by:
1. Scanning `node_modules` for packages matching naming convention
2. Loading provider metadata from `package.json`
3. Validating provider interface compliance

### Custom Provider Development
Providers must export standardized interface:

```typescript
// scrapping provider example
export default {
  name: 'custom-scraper',
  version: '1.0.0',
  type: 'scraping',
  initialize: async (config) => { /* ... */ },
  executeInit: async (stepConfig) => { /* ... */ },
  // ... other required methods
}
```
