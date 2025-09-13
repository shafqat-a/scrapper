# Quickstart Guide: Provider-Based Web Scraping System (Python)

## Installation

### Prerequisites
- Python 3.11+ installed
- pip or pipx package manager
- (Optional) Docker for storage provider testing

### Install CLI
```bash
pip install web-scrapper-cli
# or with pipx for isolated installation
pipx install web-scrapper-cli
```

### Verify Installation
```bash
scrapper --version
scrapper --help
```

## Quick Start: Your First Scraping Workflow

### Step 1: Create a Simple Workflow

Create a file `news-scraper.json`:

```json
{
  "version": "1.0.0",
  "metadata": {
    "name": "News Headlines Scraper",
    "description": "Extract news headlines from example news site",
    "author": "quickstart-user",
    "targetSite": "https://example-news.com",
    "tags": ["news", "headlines"]
  },
  "scraping": {
    "provider": "beautifulsoup",
    "config": {
      "parser": "lxml",
      "timeout": 10000,
      "userAgent": "scrapper/1.0.0 (Python)"
    }
  },
  "storage": {
    "provider": "csv",
    "config": {
      "filePath": "./scraped-news.csv",
      "headers": true
    }
  },
  "steps": [
    {
      "id": "init",
      "command": "init",
      "config": {
        "url": "https://example-news.com",
        "waitFor": 2000
      }
    },
    {
      "id": "extract-headlines",
      "command": "extract",
      "config": {
        "elements": {
          "headline": {
            "selector": "h2.article-title",
            "type": "text"
          },
          "link": {
            "selector": "h2.article-title a",
            "type": "attribute",
            "attribute": "href"
          },
          "published": {
            "selector": ".article-date",
            "type": "text"
          }
        }
      }
    }
  ]
}
```

### Step 2: Validate the Workflow

```bash
scrapper validate news-scraper.json
```

Expected output:
```
✓ Workflow schema validation passed
✓ Provider 'beautifulsoup' available
✓ Provider 'csv' available
✓ All workflow steps valid
✓ Workflow ready to execute
```

### Step 3: Run the Workflow

```bash
scrapper run news-scraper.json
```

Expected output:
```
✓ Workflow validated successfully
▶ Executing step: init
  → Navigating to https://example-news.com
  → Page loaded: "Example News - Latest Headlines"
▶ Executing step: extract-headlines
  → Found 15 headlines
  → Extracted 15 records
✓ Workflow completed successfully
📊 Total records: 15
💾 Stored in: ./scraped-news.csv
```

### Step 4: Check Results

```bash
head -5 scraped-news.csv
```

Expected output:
```
headline,link,published
"Breaking News: Technology Advances","./article/tech-advances","2025-09-13"
"Market Updates This Morning","./article/market-update","2025-09-13"
"Sports: Championship Results","./article/sports-results","2025-09-13"
"Weather: Storm Warning Issued","./article/weather-warning","2025-09-13"
```

## Advanced Example: Multi-page E-commerce with Scrapy

Create `products-scraper.json`:

```json
{
  "version": "1.0.0",
  "metadata": {
    "name": "Product Catalog Scraper",
    "description": "Extract product information with pagination using Scrapy",
    "author": "advanced-user",
    "targetSite": "https://example-shop.com",
    "tags": ["ecommerce", "products", "catalog"]
  },
  "scraping": {
    "provider": "scrapy",
    "config": {
      "concurrentRequests": 16,
      "downloadDelay": 1.0,
      "randomizeDownloadDelay": true,
      "userAgent": "Mozilla/5.0 (compatible; ScrapyBot/1.0)",
      "robotstxtObey": true
    }
  },
  "storage": {
    "provider": "postgresql",
    "config": {
      "connectionString": "postgresql://localhost/ecommerce_data",
      "tableName": "products",
      "createTable": true
    }
  },
  "steps": [
    {
      "id": "init",
      "command": "init",
      "config": {
        "url": "https://example-shop.com/products",
        "waitFor": "networkidle"
      }
    },
    {
      "id": "discover-products",
      "command": "discover",
      "config": {
        "selectors": {
          "product": ".product-card",
          "pagination": ".pagination a[rel='next']"
        }
      }
    },
    {
      "id": "extract-product-data",
      "command": "extract",
      "config": {
        "elements": {
          "name": {
            "selector": ".product-title",
            "type": "text"
          },
          "price": {
            "selector": ".price",
            "type": "text",
            "transform": "float"
          },
          "image": {
            "selector": ".product-image img",
            "type": "attribute",
            "attribute": "src"
          },
          "description": {
            "selector": ".product-description",
            "type": "text"
          },
          "availability": {
            "selector": ".stock-status",
            "type": "text"
          }
        }
      },
      "retries": 5
    },
    {
      "id": "next-page",
      "command": "paginate",
      "config": {
        "nextPageSelector": ".pagination a[rel='next']",
        "maxPages": 10,
        "waitAfterClick": 3000,
        "stopCondition": {
          "selector": ".no-more-products",
          "condition": "exists"
        }
      }
    }
  ],
  "postProcessing": [
    {
      "type": "validate",
      "config": {
        "rules": {
          "name": { "required": true, "minLength": 1 },
          "price": { "required": true, "type": "number" }
        }
      }
    },
    {
      "type": "deduplicate",
      "config": {
        "key": "name"
      }
    }
  ]
}
```

### Run Advanced Scraper with Playwright (JavaScript Sites)

Create `spa-scraper.json` for JavaScript-heavy sites:

```json
{
  "version": "1.0.0",
  "metadata": {
    "name": "SPA Product Scraper",
    "description": "Extract data from JavaScript-heavy single page application",
    "author": "spa-user",
    "targetSite": "https://spa-shop.com",
    "tags": ["spa", "javascript", "products"]
  },
  "scraping": {
    "provider": "playwright",
    "config": {
      "browser": "chromium",
      "headless": true,
      "viewport": {
        "width": 1920,
        "height": 1080
      },
      "userAgent": "Mozilla/5.0 (compatible; PlaywrightBot/1.0)",
      "timeout": 30000
    }
  },
  "storage": {
    "provider": "json",
    "config": {
      "filePath": "./spa-products.json",
      "pretty": true
    }
  },
  "steps": [
    {
      "id": "init",
      "command": "init",
      "config": {
        "url": "https://spa-shop.com/products",
        "waitFor": "networkidle"
      }
    },
    {
      "id": "extract-spa-data",
      "command": "extract",
      "config": {
        "elements": {
          "productId": {
            "selector": "[data-product-id]",
            "type": "attribute",
            "attribute": "data-product-id"
          },
          "title": {
            "selector": ".product-name",
            "type": "text"
          },
          "rating": {
            "selector": ".rating-value",
            "type": "text",
            "transform": "float"
          }
        }
      }
    }
  ]
}
```

```bash
# Test connection first
scrapper providers test postgresql --config postgres-config.json

# Run with JSON output for monitoring
scrapper run spa-scraper.json --format json --output execution-log.json
```

## Storage Provider Examples

### CSV Storage
```json
{
  "provider": "csv",
  "config": {
    "filePath": "./data/scraped-data.csv",
    "delimiter": ",",
    "headers": true,
    "append": false
  }
}
```

### PostgreSQL Storage
```json
{
  "provider": "postgresql",
  "config": {
    "connectionString": "postgresql://username:password@localhost:5432/scraper_db",
    "tableName": "scraped_data",
    "createTable": true,
    "batchSize": 1000
  }
}
```

### MongoDB Storage
```json
{
  "provider": "mongodb",
  "config": {
    "connectionString": "mongodb://localhost:27017",
    "database": "scraper_data",
    "collection": "scraped_items",
    "upsert": true
  }
}
```

### SQLite Storage (Development)
```json
{
  "provider": "sqlite",
  "config": {
    "databasePath": "./data/scraped_data.db",
    "tableName": "items",
    "createTable": true
  }
}
```

## Common Workflow Patterns

### Pattern 1: Static Website Scraping (BeautifulSoup)
Use `beautifulsoup` provider for fast, lightweight scraping:

```json
{
  "scraping": {
    "provider": "beautifulsoup",
    "config": {
      "parser": "lxml",
      "timeout": 10000,
      "followRedirects": true
    }
  }
}
```

### Pattern 2: Production Scraping (Scrapy)
Use `scrapy` for robust, production-ready scraping:

```json
{
  "scraping": {
    "provider": "scrapy",
    "config": {
      "concurrentRequests": 32,
      "downloadDelay": 0.5,
      "robotstxtObey": true,
      "userAgent": "MyBot 1.0"
    }
  }
}
```

### Pattern 3: JavaScript-Heavy Sites (Playwright)
Use `playwright` with wait conditions:

```json
{
  "scraping": {
    "provider": "playwright",
    "config": {
      "browser": "chromium",
      "headless": true
    }
  },
  "steps": [
    {
      "id": "init",
      "command": "init",
      "config": {
        "url": "https://spa-website.com",
        "waitFor": "networkidle"
      }
    }
  ]
}
```

### Pattern 4: Authenticated Scraping
Include cookies or custom headers:

```json
{
  "steps": [
    {
      "id": "login",
      "command": "init",
      "config": {
        "url": "https://site.com/protected",
        "cookies": [
          {
            "name": "session_id",
            "value": "your-session-token",
            "domain": "site.com"
          }
        ],
        "headers": {
          "Authorization": "Bearer your-token"
        }
      }
    }
  ]
}
```

## Python-Specific Features

### Virtual Environment Setup
```bash
# Create isolated environment
python -m venv scraper-env
source scraper-env/bin/activate  # On Windows: scraper-env\Scripts\activate

# Install with all providers
pip install web-scrapper-cli[all]

# Or install specific providers only
pip install web-scrapper-cli[scrapy,playwright]
```

### Configuration with Python
Create `scrapper_config.py` for advanced configuration:

```python
# scrapper_config.py
import logging
from scrapper.config import ScrapperConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Custom configuration
config = ScrapperConfig(
    max_concurrent_workflows=5,
    default_timeout=30000,
    user_agent_pool=[
        'Mozilla/5.0 (compatible; ScrapperBot/1.0)',
        'Mozilla/5.0 (compatible; DataBot/1.0)'
    ]
)
```

### Data Processing Integration
```python
# post_process.py - Custom post-processing
import pandas as pd
from scrapper.processors import BaseProcessor

class PandasProcessor(BaseProcessor):
    def process(self, data):
        # Convert to DataFrame for advanced processing
        df = pd.DataFrame(data)

        # Clean and transform data
        df['price'] = df['price'].str.replace('$', '').astype(float)
        df['title'] = df['title'].str.strip().str.title()

        # Remove duplicates
        df = df.drop_duplicates(subset=['title'])

        return df.to_dict('records')
```

## Testing Your Workflows

### Dry Run Testing
```bash
scrapper run workflow.json --dry-run
```

### Provider Testing
```bash
# Test scraping provider
scrapper providers test scrapy

# Test storage provider with config
scrapper providers test postgresql --config db-config.json
```

### Schema Validation Only
```bash
scrapper validate workflow.json --schema-only
```

### Interactive Development
```python
# test_workflow.py - Interactive testing
import asyncio
from scrapper import WorkflowEngine, load_workflow

async def test_workflow():
    engine = WorkflowEngine()
    workflow = load_workflow('workflow.json')

    # Validate first
    validation = await engine.validate(workflow)
    if not validation['valid']:
        print("Validation errors:", validation['errors'])
        return

    # Execute
    result = await engine.execute(workflow)
    print(f"Status: {result.status}")
    print(f"Records: {result.total_records}")

# Run test
asyncio.run(test_workflow())
```

## Troubleshooting

### Common Issues

**Issue**: "Provider 'scrapy' not found"
**Solution**: Install the provider package:
```bash
pip install scrapper-provider-scrapy
```

**Issue**: "Connection refused" for PostgreSQL
**Solution**: Check database service and connection:
```bash
# Test connection
scrapper providers test postgresql --config db-config.json

# Check if PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list | grep postgresql  # macOS
```

**Issue**: "ImportError: No module named 'lxml'"
**Solution**: Install required parsing libraries:
```bash
pip install lxml beautifulsoup4 html5lib
# On Ubuntu/Debian also install:
sudo apt-get install libxml2-dev libxslt1-dev
```

### Debug Mode
```bash
# Enable debug logging
SCRAPPER_LOG_LEVEL=DEBUG scrapper run workflow.json

# Python debug with pdb
python -c "
import pdb; pdb.set_trace()
from scrapper import WorkflowEngine
# Interactive debugging session
"
```

### Memory Profiling
```bash
# Install memory profiler
pip install memory-profiler

# Run with memory monitoring
python -m memory_profiler -c "
from scrapper import run_workflow
run_workflow('large-workflow.json')
"
```

## Next Steps

1. **Explore Providers**: `scrapper providers list`
2. **Create Custom Workflows**: Adapt examples for your target websites
3. **Set Up Databases**: Configure PostgreSQL, MongoDB, or other storage
4. **Scale with Async**: Use Python's asyncio for concurrent workflows
5. **Integrate with Data Science**: Use pandas, numpy for data analysis
6. **Deploy with Docker**: Containerize your scraping workflows

## Configuration Files

### Global Config (~/.scrapper/config.json)
```json
{
  "defaults": {
    "timeout": 30000,
    "retries": 3,
    "downloadDelay": 1.0
  },
  "providers": {
    "postgresql": {
      "connectionString": "postgresql://localhost/default_db"
    }
  },
  "logging": {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  }
}
```

### Project Config (./pyproject.toml)
```toml
[tool.scrapper]
workflows_dir = "./workflows"
output_dir = "./output"
log_level = "INFO"

[tool.scrapper.providers]
default_scraper = "scrapy"
default_storage = "postgresql"

[tool.scrapper.scrapy]
concurrent_requests = 16
download_delay = 1.0
robotstxt_obey = true
```

### Python Requirements (requirements.txt)
```
web-scrapper-cli>=0.1.0
scrapy>=2.11.0
playwright>=1.40.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
pandas>=2.0.0
psycopg2-binary>=2.9.0
pymongo>=4.5.0
```

This quickstart guide leverages Python's rich ecosystem for web scraping while maintaining the same JSON-based workflow configuration approach. The provider system allows you to choose the right tool for each scraping task, from lightweight BeautifulSoup to industrial-strength Scrapy to browser automation with Playwright.