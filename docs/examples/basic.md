# Basic Examples

This document provides practical examples of common scraping scenarios using Web Scrapper CLI.

## 📰 Example 1: News Headlines

Scrape news headlines from a simple news website.

### Workflow: `news-headlines.json`

```json
{
  "version": "1.0.0",
  "metadata": {
    "name": "News Headlines Scraper",
    "description": "Extract latest news headlines and links",
    "author": "example-user",
    "target_site": "https://example-news.com",
    "tags": ["news", "headlines"]
  },
  "scraping": {
    "provider": "beautifulsoup",
    "config": {
      "parser": "lxml",
      "timeout": 30,
      "headers": {
        "User-Agent": "Mozilla/5.0 (compatible; scrapper/1.0)"
      }
    }
  },
  "storage": {
    "provider": "csv",
    "config": {
      "file_path": "./news-headlines.csv",
      "headers": true,
      "delimiter": ","
    }
  },
  "steps": [
    {
      "id": "navigate",
      "command": "init",
      "config": {
        "url": "https://example-news.com",
        "wait_for": 2000
      }
    },
    {
      "id": "extract",
      "command": "extract",
      "config": {
        "elements": {
          "headline": {
            "selector": "h2.headline, h1.article-title",
            "type": "text"
          },
          "url": {
            "selector": "h2.headline a, h1.article-title a",
            "type": "attribute",
            "attribute": "href"
          },
          "published_date": {
            "selector": ".publish-date, .article-date",
            "type": "text"
          },
          "summary": {
            "selector": ".article-summary, .excerpt",
            "type": "text"
          }
        }
      }
    }
  ],
  "post_processing": [
    {
      "type": "filter",
      "config": {
        "min_length": 10,
        "exclude_empty": true
      }
    },
    {
      "type": "transform",
      "config": {
        "strip_whitespace": true,
        "normalize_urls": true
      }
    }
  ]
}
```

### Usage

```bash
# Validate the workflow
scrapper validate news-headlines.json

# Run the scraper
scrapper run news-headlines.json

# View results
head -5 news-headlines.csv
```

### Expected Output

```csv
headline,url,published_date,summary
"Breaking: Tech Giant Announces AI Platform","https://example-news.com/ai-platform","2025-01-15","Revolutionary AI platform promises to..."
"Global Climate Summit Reaches Agreement","https://example-news.com/climate","2025-01-15","World leaders unite on carbon reduction..."
```

## 🛍️ Example 2: E-commerce Products

Scrape product listings from an online store.

### Workflow: `ecommerce-products.json`

```json
{
  "version": "1.0.0",
  "metadata": {
    "name": "Product Listings Scraper",
    "description": "Extract product information from e-commerce site",
    "author": "example-user",
    "target_site": "https://example-shop.com",
    "tags": ["ecommerce", "products", "shopping"]
  },
  "scraping": {
    "provider": "playwright",
    "config": {
      "browser": "chromium",
      "headless": true,
      "timeout": 30000,
      "viewport": {
        "width": 1920,
        "height": 1080
      }
    }
  },
  "storage": {
    "provider": "json",
    "config": {
      "file_path": "./products.json",
      "pretty_print": true
    }
  },
  "steps": [
    {
      "id": "navigate",
      "command": "init",
      "config": {
        "url": "https://example-shop.com/products",
        "wait_for": ".product-grid"
      }
    },
    {
      "id": "extract",
      "command": "extract", 
      "config": {
        "container_selector": ".product-item",
        "elements": {
          "name": {
            "selector": "h3.product-name",
            "type": "text"
          },
          "price": {
            "selector": ".price .current",
            "type": "text",
            "transform": "currency_to_float"
          },
          "original_price": {
            "selector": ".price .original",
            "type": "text", 
            "transform": "currency_to_float",
            "default": null
          },
          "rating": {
            "selector": ".rating",
            "type": "attribute",
            "attribute": "data-rating",
            "transform": "float"
          },
          "image_url": {
            "selector": ".product-image img",
            "type": "attribute",
            "attribute": "src",
            "transform": "absolute_url"
          },
          "product_url": {
            "selector": "a.product-link",
            "type": "attribute",
            "attribute": "href",
            "transform": "absolute_url"
          },
          "in_stock": {
            "selector": ".stock-status",
            "type": "text",
            "transform": "boolean",
            "mapping": {
              "In Stock": true,
              "Out of Stock": false
            }
          }
        }
      }
    }
  ],
  "post_processing": [
    {
      "type": "filter",
      "config": {
        "price_min": 0,
        "required_fields": ["name", "price"]
      }
    },
    {
      "type": "validate",
      "config": {
        "rules": [
          "required:name,price",
          "numeric:price,rating",
          "url:product_url,image_url"
        ]
      }
    },
    {
      "type": "transform",
      "config": {
        "add_scraped_at": true,
        "add_source_url": true
      }
    }
  ]
}
```

### Usage

```bash
# Run the scraper
scrapper run ecommerce-products.json

# View results with pretty formatting
cat products.json | jq '.[0]'
```

### Expected Output

```json
{
  "name": "Wireless Bluetooth Headphones",
  "price": 89.99,
  "original_price": 129.99,
  "rating": 4.5,
  "image_url": "https://example-shop.com/images/headphones-1.jpg",
  "product_url": "https://example-shop.com/products/headphones-123",
  "in_stock": true,
  "scraped_at": "2025-01-15T10:30:00Z",
  "source_url": "https://example-shop.com/products"
}
```

## 💼 Example 3: Job Listings

Scrape job postings from a job board.

### Workflow: `job-listings.json`

```json
{
  "version": "1.0.0",
  "metadata": {
    "name": "Job Listings Scraper",
    "description": "Extract job postings and details",
    "author": "example-user", 
    "target_site": "https://example-jobs.com",
    "tags": ["jobs", "careers", "listings"]
  },
  "scraping": {
    "provider": "scrapy",
    "config": {
      "concurrent_requests": 8,
      "download_delay": 1,
      "robotstxt_obey": true,
      "user_agent": "scrapper/1.0.0 (Job Search Bot)"
    }
  },
  "storage": {
    "provider": "csv",
    "config": {
      "file_path": "./job-listings.csv",
      "headers": true,
      "append": false
    }
  },
  "steps": [
    {
      "id": "navigate",
      "command": "init",
      "config": {
        "url": "https://example-jobs.com/search?q=python+developer",
        "wait_for": 3000
      }
    },
    {
      "id": "extract",
      "command": "extract",
      "config": {
        "container_selector": ".job-listing",
        "elements": {
          "title": {
            "selector": "h3.job-title a",
            "type": "text"
          },
          "company": {
            "selector": ".company-name",
            "type": "text"
          },
          "location": {
            "selector": ".job-location",
            "type": "text"
          },
          "salary": {
            "selector": ".salary-range",
            "type": "text",
            "default": "Not specified"
          },
          "job_type": {
            "selector": ".job-type",
            "type": "text"
          },
          "posted_date": {
            "selector": ".posted-date",
            "type": "text"
          },
          "job_url": {
            "selector": "h3.job-title a",
            "type": "attribute",
            "attribute": "href",
            "transform": "absolute_url"
          },
          "description": {
            "selector": ".job-summary",
            "type": "text",
            "transform": "strip"
          }
        }
      }
    }
  ],
  "post_processing": [
    {
      "type": "filter",
      "config": {
        "exclude_keywords": ["internship", "unpaid"],
        "required_fields": ["title", "company"]
      }
    },
    {
      "type": "transform",
      "config": {
        "normalize_location": true,
        "parse_salary": true,
        "standardize_job_type": true
      }
    },
    {
      "type": "deduplicate",
      "config": {
        "key": "job_url",
        "strategy": "first"
      }
    }
  ]
}
```

## 📱 Example 4: Social Media Posts

Scrape public social media posts (respecting terms of service).

### Workflow: `social-posts.json`

```json
{
  "version": "1.0.0",
  "metadata": {
    "name": "Social Media Posts Scraper",
    "description": "Extract public posts from social platform",
    "author": "example-user",
    "target_site": "https://example-social.com",
    "tags": ["social", "posts", "content"]
  },
  "scraping": {
    "provider": "playwright",
    "config": {
      "browser": "chromium",
      "headless": false,
      "timeout": 45000,
      "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
  },
  "storage": {
    "provider": "json",
    "config": {
      "file_path": "./social-posts.json",
      "pretty_print": true
    }
  },
  "steps": [
    {
      "id": "navigate",
      "command": "init",
      "config": {
        "url": "https://example-social.com/hashtag/webdevelopment",
        "wait_for": "[data-testid='post-item']",
        "cookies": []
      }
    },
    {
      "id": "scroll",
      "command": "paginate",
      "config": {
        "pagination_type": "infinite_scroll",
        "scroll_pause": 2000,
        "max_scrolls": 5,
        "load_more_selector": "[data-testid='load-more']"
      }
    },
    {
      "id": "extract",
      "command": "extract",
      "config": {
        "container_selector": "[data-testid='post-item']",
        "elements": {
          "username": {
            "selector": ".post-author .username",
            "type": "text"
          },
          "content": {
            "selector": ".post-content",
            "type": "text"
          },
          "timestamp": {
            "selector": ".post-timestamp",
            "type": "attribute",
            "attribute": "datetime"
          },
          "likes": {
            "selector": ".like-count",
            "type": "text",
            "transform": "int",
            "default": 0
          },
          "shares": {
            "selector": ".share-count", 
            "type": "text",
            "transform": "int",
            "default": 0
          },
          "hashtags": {
            "selector": ".hashtag",
            "type": "text_array"
          },
          "post_url": {
            "selector": ".post-link",
            "type": "attribute",
            "attribute": "href",
            "transform": "absolute_url"
          }
        }
      }
    }
  ],
  "post_processing": [
    {
      "type": "filter",
      "config": {
        "min_content_length": 10,
        "exclude_retweets": true
      }
    },
    {
      "type": "transform",
      "config": {
        "parse_mentions": true,
        "extract_links": true,
        "sentiment_analysis": false
      }
    }
  ]
}
```

## 🏠 Example 5: Real Estate Listings

Scrape property listings from real estate websites.

### Workflow: `real-estate.json`

```json
{
  "version": "1.0.0",
  "metadata": {
    "name": "Real Estate Listings",
    "description": "Extract property listings and details",
    "author": "example-user",
    "target_site": "https://example-realty.com",
    "tags": ["real-estate", "properties", "listings"]
  },
  "scraping": {
    "provider": "beautifulsoup",
    "config": {
      "parser": "lxml",
      "timeout": 30,
      "delay_between_requests": 2000
    }
  },
  "storage": {
    "provider": "csv",
    "config": {
      "file_path": "./properties.csv",
      "headers": true
    }
  },
  "steps": [
    {
      "id": "navigate",
      "command": "init",
      "config": {
        "url": "https://example-realty.com/search?city=seattle&type=house"
      }
    },
    {
      "id": "extract",
      "command": "extract",
      "config": {
        "container_selector": ".property-listing",
        "elements": {
          "address": {
            "selector": ".property-address",
            "type": "text"
          },
          "price": {
            "selector": ".price",
            "type": "text",
            "transform": "currency_to_float"
          },
          "bedrooms": {
            "selector": ".bedrooms",
            "type": "text",
            "transform": "int"
          },
          "bathrooms": {
            "selector": ".bathrooms", 
            "type": "text",
            "transform": "float"
          },
          "sqft": {
            "selector": ".square-feet",
            "type": "text",
            "transform": "int"
          },
          "property_type": {
            "selector": ".property-type",
            "type": "text"
          },
          "listing_date": {
            "selector": ".listing-date",
            "type": "text"
          },
          "agent_name": {
            "selector": ".agent-name",
            "type": "text"
          },
          "property_url": {
            "selector": ".property-link",
            "type": "attribute",
            "attribute": "href",
            "transform": "absolute_url"
          }
        }
      }
    },
    {
      "id": "paginate",
      "command": "paginate",
      "config": {
        "next_page_selector": ".pagination .next:not(.disabled)",
        "max_pages": 10,
        "wait_after_click": 3000
      }
    }
  ],
  "post_processing": [
    {
      "type": "filter",
      "config": {
        "price_min": 50000,
        "price_max": 5000000,
        "required_fields": ["address", "price"]
      }
    },
    {
      "type": "transform",
      "config": {
        "calculate_price_per_sqft": true,
        "standardize_address": true
      }
    }
  ]
}
```

## 🎯 Usage Patterns

### Running Examples

```bash
# Validate before running
scrapper validate news-headlines.json

# Run with progress output
scrapper run news-headlines.json

# Run in silent mode
scrapper run ecommerce-products.json --silent

# Run with custom output
scrapper run job-listings.json --output logs/job-scraping.log

# Run with higher concurrency
scrapper run social-posts.json --concurrent 10
```

### Monitoring Progress

```bash
# Watch output file in real-time
tail -f products.csv

# Check JSON output
cat social-posts.json | jq length

# Validate extracted data
head -10 job-listings.csv | column -t -s ','
```

### Error Handling

```bash
# Run with debug mode
scrapper run workflow.json --debug

# Dry run to test configuration
scrapper run workflow.json --dry-run

# Test individual providers
scrapper providers test playwright
```

## 🔧 Customization Tips

### Adjusting Selectors

1. **Inspect the target website** using browser developer tools
2. **Test selectors** in the browser console
3. **Use fallback selectors** for better reliability:
   ```json
   "selector": "h2.title, h1.heading, .article-title"
   ```

### Handling Dynamic Content

1. **Use Playwright** for JavaScript-heavy sites
2. **Add wait conditions** for dynamic loading:
   ```json
   "wait_for": "#content-loaded"
   ```
3. **Enable infinite scroll** for social media:
   ```json
   "pagination_type": "infinite_scroll"
   ```

### Data Quality

1. **Add validation rules** in post-processing:
   ```json
   "rules": ["required:title,price", "numeric:price"]
   ```
2. **Use transformations** to clean data:
   ```json
   "transform": "currency_to_float"
   ```
3. **Filter out unwanted content**:
   ```json
   "exclude_keywords": ["advertisement", "sponsored"]
   ```

## ⚠️ Best Practices

1. **Respect robots.txt** and rate limits
2. **Use appropriate delays** between requests
3. **Handle errors gracefully** with retries
4. **Test workflows** before production use
5. **Monitor website changes** and update selectors
6. **Store results safely** with backups
7. **Follow website terms of service**

---

## 🚀 Next Steps

- **[Advanced Use Cases](advanced.md)** - Complex multi-page scraping
- **[Industry Examples](industry.md)** - Domain-specific scraping patterns
- **[Best Practices](best-practices.md)** - Production deployment guidelines
- **[Error Handling](../user-guide/error-handling.md)** - Troubleshooting and debugging

---

These examples provide a foundation for building your own scraping workflows with Web Scrapper CLI.