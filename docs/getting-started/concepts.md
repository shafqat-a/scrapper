# Basic Concepts

This document introduces the core concepts and terminology used throughout the Web Scrapper CLI system.

## 🎯 Overview

Web Scrapper CLI is built around four fundamental concepts that work together to create powerful, flexible scraping solutions:

```mermaid
graph TD
    A[Workflow] --> B[Providers]
    A --> C[Steps] 
    A --> D[Post-Processing]
    
    B --> B1[Scraping Providers]
    B --> B2[Storage Providers]
    
    C --> C1[Init]
    C --> C2[Discover]
    C --> C3[Extract]
    C --> C4[Paginate]
    
    D --> D1[Filter]
    D --> D2[Transform]
    D --> D3[Validate]
    D --> D4[Deduplicate]
```

## 📋 Workflow

A **Workflow** is a JSON configuration file that defines a complete scraping operation from start to finish.

### Core Structure
```json
{
  "version": "1.0.0",           // Schema version
  "metadata": {...},           // Workflow information
  "scraping": {...},          // Scraping provider configuration
  "storage": {...},           // Storage provider configuration  
  "steps": [...],             // Execution steps
  "post_processing": [...]    // Data transformation steps
}
```

### Key Characteristics
- **Declarative**: Describe what to scrape, not how to scrape it
- **Reproducible**: Same workflow produces same results
- **Version-controlled**: JSON files can be stored in git
- **Testable**: Validate workflows before execution
- **Shareable**: Share workflows across teams and projects

### Workflow Lifecycle

```mermaid
graph LR
    A[Created] --> B[Validated]
    B --> C[Executing]
    C --> D[Completed]
    C --> E[Failed]
    E --> F[Retrying]
    F --> C
```

## 🔌 Providers

**Providers** are pluggable components that handle specific aspects of the scraping process. There are two main types:

### Scraping Providers
Handle the actual web scraping and data extraction:

| Provider | Best For | Technology | JavaScript |
|----------|----------|------------|------------|
| **beautifulsoup** | Simple HTML sites | Requests + BeautifulSoup | ❌ No |
| **scrapy** | Large-scale scraping | Scrapy framework | ❌ No |
| **playwright** | Modern web apps | Browser automation | ✅ Yes |

**Example Configuration:**
```json
{
  "scraping": {
    "provider": "playwright",
    "config": {
      "browser": "chromium",
      "headless": true,
      "timeout": 30000
    }
  }
}
```

### Storage Providers
Handle data persistence and output formatting:

| Provider | Best For | Format | Scalability |
|----------|----------|---------|-------------|
| **csv** | Simple tabular data | CSV files | Small-Medium |
| **json** | Structured data | JSON files | Small-Medium |
| **postgresql** | Relational data | SQL database | Large |
| **mongodb** | Document data | NoSQL database | Large |

**Example Configuration:**
```json
{
  "storage": {
    "provider": "postgresql",
    "config": {
      "connection_string": "postgresql://user:pass@localhost/db",
      "table_name": "scraped_products"
    }
  }
}
```

## 🪜 Steps

**Steps** are the individual operations that make up a workflow. Each step has a specific purpose and executes in sequence.

### Step Types

#### 1. Init Step
**Purpose**: Navigate to the target website and establish initial context.

```json
{
  "id": "navigate-to-site",
  "command": "init", 
  "config": {
    "url": "https://example.com",
    "wait_for": "body"
  }
}
```

**What it does:**
- Navigates to specified URL
- Waits for page to load
- Sets up cookies and headers
- Creates PageContext for subsequent steps

#### 2. Discover Step (Optional)
**Purpose**: Analyze page structure and identify available elements.

```json
{
  "id": "find-products",
  "command": "discover",
  "config": {
    "selectors": {
      "items": ".product-item",
      "pagination": ".next-page"
    }
  }
}
```

**What it does:**
- Scans page for specified selectors
- Counts available items
- Identifies pagination elements
- Provides metadata for extraction

#### 3. Extract Step
**Purpose**: Extract actual data from the page elements.

```json
{
  "id": "get-product-data",
  "command": "extract",
  "config": {
    "elements": {
      "name": {"selector": "h2", "type": "text"},
      "price": {"selector": ".price", "type": "text", "transform": "float"}
    }
  }
}
```

**What it does:**
- Finds elements using CSS selectors
- Extracts text, attributes, or HTML content
- Applies data transformations
- Returns structured data objects

#### 4. Paginate Step (Optional)
**Purpose**: Navigate to next page and continue extraction.

```json
{
  "id": "next-page",
  "command": "paginate",
  "config": {
    "next_page_selector": ".next-page",
    "max_pages": 10
  }
}
```

**What it does:**
- Clicks next page link
- Waits for new page to load
- Updates PageContext
- Enables multi-page scraping

### Step Configuration

Every step includes common configuration options:

```json
{
  "id": "unique-step-name",        // Step identifier
  "command": "init|discover|extract|paginate",  // Step type
  "config": {...},                 // Step-specific configuration
  "retries": 3,                    // Number of retry attempts
  "timeout": 30000,                // Timeout in milliseconds
  "continue_on_error": false       // Whether to continue if step fails
}
```

## 🔄 Post-Processing

**Post-processing** steps clean, transform, and validate extracted data before storage.

### Processing Types

#### Filter
Remove unwanted data based on conditions:
```json
{
  "type": "filter",
  "config": {
    "min_length": 10,
    "exclude_pattern": "advertisement",
    "required_fields": ["title", "price"]
  }
}
```

#### Transform
Modify data values and formats:
```json
{
  "type": "transform", 
  "config": {
    "price": "parseFloat",
    "title": "trim",
    "url": "absolute_url"
  }
}
```

#### Validate
Ensure data quality and completeness:
```json
{
  "type": "validate",
  "config": {
    "rules": [
      "required:title,price",
      "numeric:price", 
      "url:product_url"
    ]
  }
}
```

#### Deduplicate
Remove duplicate entries:
```json
{
  "type": "deduplicate",
  "config": {
    "key": "product_url",
    "strategy": "first"
  }
}
```

## 🔄 Data Flow

Understanding how data flows through the system:

```mermaid
graph TD
    A[Workflow JSON] --> B[Validation]
    B --> C[Provider Setup]
    C --> D[Step Execution]
    
    D --> E[Init Step]
    E --> F[PageContext]
    
    F --> G[Discover Step]
    G --> H[Element Metadata]
    
    H --> I[Extract Step] 
    I --> J[Raw Data]
    
    J --> K[Paginate Step]
    K --> L{More Pages?}
    L -->|Yes| F
    L -->|No| M[Post-Processing]
    
    M --> N[Clean Data]
    N --> O[Storage Provider]
    O --> P[Final Output]
```

### Data Types

#### PageContext
Contains information about the current page state:
```python
{
  "url": "https://example.com/products",
  "title": "Products - Example Store",
  "html_content": "<html>...",
  "cookies": [...],
  "metadata": {...}
}
```

#### Extracted Data
Structured data objects from extraction:
```python
[
  {
    "title": "Product Name",
    "price": 29.99,
    "url": "https://example.com/product/123",
    "extracted_at": "2025-01-15T10:30:00Z"
  }
]
```

## ⚙️ Configuration

### Environment Variables
Control scrapper behavior:
```bash
SCRAPPER_LOG_LEVEL=DEBUG      # Logging verbosity
SCRAPPER_CONFIG_FILE=config.json  # Default config file
SCRAPPER_DATA_DIR=./data      # Data storage directory
```

### Global Configuration
```json
{
  "defaults": {
    "timeout": 30000,
    "retries": 3,
    "user_agent": "scrapper/1.0.0"
  },
  "rate_limiting": {
    "requests_per_second": 5,
    "burst_limit": 10
  },
  "storage": {
    "batch_size": 100,
    "compression": true
  }
}
```

## 🔍 Debugging and Monitoring

### Execution States
Monitor workflow progress through execution states:

- **Created**: Workflow loaded and parsed
- **Validated**: Configuration verified  
- **Initialized**: Providers set up
- **Executing**: Steps running
- **Completed**: Successfully finished
- **Failed**: Error encountered
- **Retrying**: Attempting recovery

### Logging Levels
```python
CRITICAL  # System failures
ERROR     # Step failures  
WARNING   # Recoverable issues
INFO      # Execution progress (default)
DEBUG     # Detailed operations
```

### Metrics
Track performance and reliability:
- **Success Rate**: Percentage of successful extractions
- **Execution Time**: Total workflow runtime
- **Items Scraped**: Number of data items extracted  
- **Error Rate**: Frequency of step failures
- **Resource Usage**: Memory and CPU consumption

## 🎯 Key Principles

### 1. Separation of Concerns
- **Workflows** define what to scrape
- **Providers** handle how to scrape
- **Steps** control when to scrape
- **Post-processing** ensures data quality

### 2. Error Resilience
- Configurable retries at step level
- Graceful degradation options
- Comprehensive error logging
- Recovery strategies

### 3. Scalability
- Async/await for concurrent operations
- Provider-specific optimizations  
- Batch processing for large datasets
- Resource usage monitoring

### 4. Maintainability
- JSON configuration (version-controlled)
- Provider abstraction (swap implementations)
- Clear error messages
- Comprehensive logging

---

## 🚀 Next Steps

Now that you understand the core concepts:

1. **[Installation](installation.md)** - Set up Web Scrapper CLI
2. **[Quick Start](quickstart.md)** - Create your first workflow
3. **[Creating Workflows](../user-guide/creating-workflows.md)** - Detailed workflow creation
4. **[Provider Guide](../user-guide/providers.md)** - Choose the right providers

---

These concepts form the foundation of Web Scrapper CLI. Understanding them will help you create effective, maintainable scraping workflows.