# 📋 Example Workflows

This directory contains practical workflow examples demonstrating various use cases for the Web Scrapper CLI.

## 🚀 Quick Start

1. Choose an example workflow
2. Modify the target URLs and selectors for your specific needs
3. Test the workflow: `scrapper validate example.json`
4. Run the workflow: `scrapper run example.json`

## 📄 Available Examples

### 📰 [News Headlines](./news-headlines.json)
**Provider**: BeautifulSoup | **Storage**: CSV

Extract news headlines, links, and publication dates from news websites.

```bash
# Validate and run
scrapper validate examples/news-headlines.json
scrapper run examples/news-headlines.json
```

**Features:**
- Simple HTML parsing with BeautifulSoup
- CSV output with headers
- Post-processing filters and transforms
- Deduplication by URL

---

### 🛒 [E-commerce Products](./ecommerce-products.json)
**Provider**: Playwright | **Storage**: PostgreSQL

Scrape product listings with pagination support for e-commerce sites.

```bash
# Setup PostgreSQL database first
createdb products_db

# Run workflow
scrapper run examples/ecommerce-products.json
```

**Features:**
- JavaScript rendering with Playwright
- Database storage with schema validation
- Pagination handling
- Price and rating transformations
- Database indexing for performance

---

### 💼 [Job Listings](./job-listings.json)
**Provider**: Scrapy | **Storage**: JSON Lines

Extract job postings from job board websites with high-performance scraping.

```bash
# Run with concurrent scraping
scrapper run examples/job-listings.json
```

**Features:**
- Industrial-grade scraping with Scrapy
- JSONL streaming output format
- Discovery step to analyze page structure
- Concurrent request handling
- Rate limiting and robots.txt compliance

---

### 📱 [Social Media Posts](./social-media-posts.json)
**Provider**: Playwright | **Storage**: JSON

Scrape social media posts with engagement metrics.

```bash
# Run with browser automation
scrapper run examples/social-media-posts.json
```

**Features:**
- Full browser automation for JavaScript-heavy sites
- Cookie management for session handling
- Scroll-based pagination
- Engagement metrics extraction
- Media URL collection

## 🔧 Customization Guide

### 1. Modify Target URLs
Update the `target_site` and step URLs to match your target website:

```json
{
  "metadata": {
    "target_site": "https://your-target-site.com"
  },
  "steps": [
    {
      "id": "init",
      "config": {
        "url": "https://your-target-site.com/page"
      }
    }
  ]
}
```

### 2. Update Selectors
Inspect your target website and update CSS selectors:

```json
{
  "config": {
    "elements": {
      "title": {"selector": "h1.your-title-class", "type": "text"},
      "price": {"selector": ".your-price-class", "type": "text", "transform": "float"}
    }
  }
}
```

### 3. Choose Storage Provider
Swap storage providers based on your needs:

```json
// CSV for simple exports
{
  "storage": {
    "provider": "csv",
    "config": {
      "file_path": "./output.csv",
      "headers": true
    }
  }
}

// PostgreSQL for production databases
{
  "storage": {
    "provider": "postgresql",
    "config": {
      "connection_string": "postgresql://user:pass@localhost/db"
    }
  }
}

// JSON for API integration
{
  "storage": {
    "provider": "json",
    "config": {
      "file_path": "./output.json",
      "format": "json",
      "pretty_print": true
    }
  }
}
```

### 4. Configure Anti-Detection
Add anti-detection measures for production scraping:

```json
{
  "scraping": {
    "provider": "playwright",
    "config": {
      "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
      "viewport": {"width": 1920, "height": 1080},
      "timeout": 30000
    }
  }
}
```

## 🎯 Common Patterns

### Pagination Handling
```json
{
  "id": "pagination",
  "command": "paginate",
  "config": {
    "next_page_selector": ".next-page",
    "max_pages": 50,
    "wait_after_click": 2000,
    "stop_condition": {
      "selector": ".no-results",
      "text": "No more results"
    }
  }
}
```

### Data Transformation
```json
{
  "post_processing": [
    {
      "type": "filter",
      "config": {
        "min_length": 5,
        "excludes": "advertisement"
      }
    },
    {
      "type": "transform",
      "config": {
        "strip": true,
        "replace": {"$": "", ",": ""},
        "lowercase": true
      }
    },
    {
      "type": "deduplicate",
      "config": {"key": "url"}
    }
  ]
}
```

### Error Handling
```json
{
  "steps": [
    {
      "id": "robust-step",
      "command": "extract",
      "config": {...},
      "retries": 5,
      "timeout": 60000,
      "continue_on_error": true
    }
  ]
}
```

## 🚨 Best Practices

### 1. **Respect Robots.txt**
Always check and comply with the website's robots.txt file:
```json
{
  "scraping": {
    "provider": "scrapy",
    "config": {
      "robotstxt_obey": true
    }
  }
}
```

### 2. **Use Appropriate Delays**
Add delays to avoid overwhelming servers:
```json
{
  "scraping": {
    "provider": "scrapy",
    "config": {
      "download_delay": 1.0,
      "randomize_download_delay": true
    }
  }
}
```

### 3. **Handle Dynamic Content**
For JavaScript-heavy sites, use Playwright:
```json
{
  "scraping": {
    "provider": "playwright",
    "config": {
      "wait_for": ".dynamic-content",
      "timeout": 30000
    }
  }
}
```

### 4. **Validate Before Production**
Always validate workflows before running:
```bash
scrapper validate your-workflow.json --detailed
```

### 5. **Monitor and Test**
Test your workflows regularly as websites change:
```bash
scrapper providers test postgresql --config config.json
scrapper run workflow.json --dry-run
```

## 📞 Support

If you need help customizing these examples:

1. Check the [main documentation](../README.md)
2. Validate your workflow: `scrapper validate workflow.json --detailed`
3. Test individual providers: `scrapper providers test provider-name`
4. Open an issue on [GitHub](https://github.com/shafqat-a/scrapper/issues)

---

**Happy Scraping! 🚀**
