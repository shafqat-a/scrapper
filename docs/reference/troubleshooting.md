# Troubleshooting

Common issues, solutions, and debugging techniques for Web Scrapper CLI.

## 🔧 Quick Diagnostics

When encountering issues, start with these diagnostic commands:

```bash
# Check installation
scrapper --version
scrapper --help

# Validate your workflow
scrapper validate your-workflow.json --detailed

# Test providers
scrapper providers list
scrapper providers test beautifulsoup

# Run in debug mode
scrapper run workflow.json --debug --dry-run
```

## 🚨 Common Issues

### Installation Problems

#### Issue: `scrapper: command not found`

**Cause**: scrapper is not in your system PATH.

**Solutions:**
```bash
# Option 1: Install with --user flag
pip install --user web-scrapper-cli
export PATH=$PATH:~/.local/bin

# Option 2: Use pipx
pipx install web-scrapper-cli

# Option 3: Use full Python path
python -m scrapper run workflow.json

# Option 4: Check installation location
pip show web-scrapper-cli
```

#### Issue: `ImportError: No module named 'scrapper'`

**Cause**: Package not installed or virtual environment issues.

**Solutions:**
```bash
# Verify installation
pip list | grep scrapper

# Reinstall package
pip uninstall web-scrapper-cli
pip install web-scrapper-cli

# Check Python version
python --version  # Should be 3.11+
```

#### Issue: Permission denied during installation

**Cause**: Insufficient permissions to install system-wide packages.

**Solutions:**
```bash
# Use --user installation
pip install --user web-scrapper-cli

# Or use virtual environment
python -m venv scrapper-env
source scrapper-env/bin/activate
pip install web-scrapper-cli
```

### Provider Issues

#### Issue: `Provider 'playwright' not available`

**Cause**: Playwright dependencies not installed.

**Solutions:**
```bash
# Install Playwright provider
pip install web-scrapper-cli[playwright]

# Install browser binaries
playwright install

# Test installation
scrapper providers test playwright
```

#### Issue: `Browser launch failed` (Playwright)

**Cause**: Missing system dependencies or browser binaries.

**Solutions:**
```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y \
  libnss3-dev libatk-bridge2.0-dev libdrm-dev \
  libxkbcommon-dev libgtk-3-dev libgbm-dev

# Install browsers with dependencies
playwright install --with-deps

# Use different browser
{
  "scraping": {
    "provider": "playwright",
    "config": {
      "browser": "firefox"  // Try firefox or webkit
    }
  }
}
```

#### Issue: `Connection refused` (PostgreSQL)

**Cause**: PostgreSQL server not running or connection details incorrect.

**Solutions:**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Start PostgreSQL
sudo systemctl start postgresql

# Test connection
psql -h localhost -U username -d database_name

# Update connection string in workflow
{
  "storage": {
    "provider": "postgresql",
    "config": {
      "connection_string": "postgresql://user:password@localhost:5432/dbname"
    }
  }
}
```

### Workflow Execution Issues

#### Issue: `No elements found` during extraction

**Cause**: CSS selectors don't match page structure.

**Solutions:**

1. **Inspect the target page** in browser developer tools:
   - Right-click element → "Inspect"
   - Copy selector from DevTools
   - Test selector in browser console: `document.querySelector("your-selector")`

2. **Use multiple fallback selectors**:
   ```json
   {
     "selector": "h2.title, h1.heading, .article-title, [data-title]"
   }
   ```

3. **Add wait conditions** for dynamic content:
   ```json
   {
     "wait_for": ".content-loaded",
     "timeout": 45000
   }
   ```

4. **Enable debug mode** to see what selectors are being tried:
   ```bash
   scrapper run workflow.json --debug
   ```

#### Issue: `Timeout waiting for page to load`

**Cause**: Page loading slowly or waiting for wrong element.

**Solutions:**

1. **Increase timeout**:
   ```json
   {
     "timeout": 60000,  // 60 seconds
     "retries": 3
   }
   ```

2. **Change wait condition**:
   ```json
   {
     "wait_for": "body",  // Wait for basic page structure
     // or
     "wait_for": 2000     // Wait for specific time (ms)
   }
   ```

3. **Use different provider**:
   ```json
   {
     "scraping": {
       "provider": "beautifulsoup"  // Faster for static content
     }
   }
   ```

#### Issue: `Rate limited` or `429 Too Many Requests`

**Cause**: Making requests too quickly.

**Solutions:**

1. **Add delays between requests**:
   ```json
   {
     "scraping": {
       "config": {
         "delay_between_requests": 2000,  // 2 seconds
         "concurrent_requests": 1
       }
     }
   }
   ```

2. **Reduce concurrency**:
   ```bash
   scrapper run workflow.json --concurrent 1
   ```

3. **Use different User-Agent**:
   ```json
   {
     "headers": {
       "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
     }
   }
   ```

### Data Quality Issues

#### Issue: Extracted data contains HTML tags

**Cause**: Using wrong extraction type or HTML content not cleaned.

**Solutions:**

1. **Use correct extraction type**:
   ```json
   {
     "type": "text"  // Extracts text content only
     // instead of "html"
   }
   ```

2. **Add post-processing**:
   ```json
   {
     "post_processing": [
       {
         "type": "transform",
         "config": {
           "strip_html": true,
           "normalize_whitespace": true
         }
       }
     ]
   }
   ```

#### Issue: Data contains unwanted characters or formatting

**Cause**: Website includes extra characters or formatting.

**Solutions:**

1. **Add data transformations**:
   ```json
   {
     "elements": {
       "price": {
         "selector": ".price",
         "type": "text",
         "transform": "currency_to_float"  // Converts "$19.99" to 19.99
       }
     }
   }
   ```

2. **Use post-processing filters**:
   ```json
   {
     "post_processing": [
       {
         "type": "filter",
         "config": {
           "exclude_pattern": "advertisement|sponsored",
           "min_length": 5
         }
       }
     ]
   }
   ```

## 🐛 Debugging Techniques

### Enable Debug Logging

```bash
# Method 1: Command line flag
scrapper run workflow.json --debug

# Method 2: Environment variable
export SCRAPPER_LOG_LEVEL=DEBUG
scrapper run workflow.json

# Method 3: Global configuration
echo '{"logging": {"level": "DEBUG"}}' > ~/.scrapper/config.json
```

### Dry Run Testing

Test workflows without actually executing them:

```bash
# Validate configuration only
scrapper validate workflow.json --detailed

# Test execution plan without running
scrapper run workflow.json --dry-run

# Test specific providers
scrapper providers test playwright --config test-config.json
```

### Step-by-Step Debugging

Create minimal workflows to isolate issues:

```json
{
  "version": "1.0.0",
  "metadata": {"name": "Debug Test"},
  "scraping": {"provider": "beautifulsoup", "config": {}},
  "storage": {"provider": "json", "config": {"file_path": "./debug.json"}},
  "steps": [
    {
      "id": "test-init",
      "command": "init",
      "config": {"url": "https://httpbin.org/html"}
    }
  ]
}
```

### Browser Debugging (Playwright)

For Playwright provider issues, run in non-headless mode:

```json
{
  "scraping": {
    "provider": "playwright",
    "config": {
      "headless": false,  // Shows browser window
      "slowMo": 1000     // Slows down operations
    }
  }
}
```

### Network Debugging

Monitor network requests:

```bash
# Enable network logging
export SCRAPPER_LOG_LEVEL=DEBUG
export SCRAPPER_LOG_NETWORK=true

# Monitor with external tools
# tcpdump, wireshark, or browser network tab
```

## 📊 Performance Issues

### Issue: High memory usage

**Cause**: Processing large datasets or memory leaks.

**Solutions:**

1. **Enable batch processing**:
   ```json
   {
     "storage": {
       "config": {
         "batch_size": 100  // Process 100 items at a time
       }
     }
   }
   ```

2. **Reduce concurrency**:
   ```bash
   scrapper run workflow.json --concurrent 2
   ```

3. **Monitor memory usage**:
   ```bash
   # Linux/macOS
   top -p $(pgrep -f scrapper)
   
   # Alternative
   ps aux | grep scrapper
   ```

### Issue: Slow execution

**Cause**: Network latency, inefficient selectors, or provider overhead.

**Solutions:**

1. **Profile execution time**:
   ```bash
   time scrapper run workflow.json
   ```

2. **Optimize selectors** (use specific, efficient selectors):
   ```json
   {
     "selector": "#main-content .article"  // Specific
     // instead of: "div div div .article"  // Inefficient
   }
   ```

3. **Choose appropriate provider**:
   - **BeautifulSoup**: Fastest for static HTML
   - **Scrapy**: Best for large-scale scraping
   - **Playwright**: Necessary for JavaScript, but slower

4. **Increase concurrency** for I/O bound operations:
   ```bash
   scrapper run workflow.json --concurrent 10
   ```

## 🔐 Security and Access Issues

### Issue: `403 Forbidden` or `Access Denied`

**Cause**: Website blocking automated requests.

**Solutions:**

1. **Use realistic User-Agent**:
   ```json
   {
     "headers": {
       "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
     }
   }
   ```

2. **Add request headers**:
   ```json
   {
     "headers": {
       "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
       "Accept-Language": "en-US,en;q=0.5",
       "Accept-Encoding": "gzip, deflate"
     }
   }
   ```

3. **Use proxy servers** (if allowed):
   ```json
   {
     "scraping": {
       "config": {
         "proxy": "http://proxy-server:8080"
       }
     }
   }
   ```

### Issue: CAPTCHA or bot detection

**Cause**: Website has anti-bot measures.

**Solutions:**

1. **Reduce request frequency**:
   ```json
   {
     "config": {
       "delay_between_requests": 5000,  // 5 seconds
       "concurrent_requests": 1
     }
   }
   ```

2. **Use Playwright with stealth mode**:
   ```bash
   pip install playwright-stealth
   ```

3. **Rotate User-Agents and IP addresses**
4. **Consider using commercial scraping services for heavily protected sites**

## 📝 Configuration Issues

### Issue: `Invalid JSON syntax`

**Cause**: Malformed JSON in workflow file.

**Solutions:**

1. **Validate JSON syntax**:
   ```bash
   # Using jq
   cat workflow.json | jq .
   
   # Using Python
   python -m json.tool workflow.json
   
   # Online validators: jsonlint.com
   ```

2. **Common JSON errors**:
   - Missing commas between items
   - Trailing commas (not allowed in JSON)
   - Unescaped quotes in strings
   - Missing closing brackets/braces

### Issue: `Schema validation failed`

**Cause**: Workflow doesn't match expected structure.

**Solutions:**

1. **Check required fields**:
   ```bash
   scrapper validate workflow.json --detailed
   ```

2. **Use workflow templates**:
   ```bash
   scrapper init new-workflow.json --template basic
   ```

3. **Review schema documentation**:
   - [Schema Reference](schema.md)

## 🔄 Recovery Strategies

### Handling Partial Failures

1. **Enable continue-on-error** for non-critical steps:
   ```json
   {
     "continue_on_error": true,
     "retries": 3
   }
   ```

2. **Implement checkpointing** for long-running workflows:
   ```json
   {
     "storage": {
       "config": {
         "append": true,  // Append to existing file
         "checkpoint_interval": 100  // Save every 100 items
       }
     }
   }
   ```

### Error Recovery

1. **Automatic retries** with exponential backoff:
   ```json
   {
     "retries": 5,
     "timeout": 30000
   }
   ```

2. **Manual recovery**:
   ```bash
   # Resume from specific step
   scrapper run workflow.json --start-from step-id
   
   # Skip failed items
   scrapper run workflow.json --skip-errors
   ```

## 📞 Getting Help

### Community Support

1. **GitHub Issues**: [Report bugs](https://github.com/shafqat-a/scrapper/issues)
2. **Discussions**: [Ask questions](https://github.com/shafqat-a/scrapper/discussions)
3. **Discord**: [Join community](https://discord.gg/scrapper)

### Professional Support

1. **Email**: team@scrapper.dev
2. **Enterprise support**: Available for commercial users

### Diagnostic Information

When reporting issues, include:

```bash
# System information
scrapper --version
python --version
pip show web-scrapper-cli

# Error logs
scrapper run workflow.json --debug > debug.log 2>&1

# Workflow configuration (remove sensitive data)
cat workflow.json
```

## 📚 Additional Resources

### Documentation

- [Getting Started Guide](../getting-started/)
- [User Guide](../user-guide/)
- [API Reference](../development/api-reference.md)

### Tools

- **JSON Validators**: jsonlint.com, jq
- **CSS Selector Testers**: Browser DevTools, CSS Selector Tester
- **Network Monitors**: Browser Network Tab, Wireshark
- **Performance Monitors**: top, htop, Activity Monitor

### Best Practices

- [Production Deployment](../examples/best-practices.md)
- [Error Handling Patterns](../user-guide/error-handling.md)
- [Performance Optimization](../examples/advanced.md)

---

## 🎯 Quick Reference

### Emergency Commands

```bash
# Stop all scrapper processes
pkill -f scrapper

# Clean up temporary files  
rm -rf ~/.scrapper/cache/*

# Reset configuration
rm ~/.scrapper/config.json

# Reinstall package
pip uninstall web-scrapper-cli
pip install web-scrapper-cli
```

### Debug Checklist

- [ ] Workflow JSON is valid
- [ ] All required providers are available
- [ ] CSS selectors work in browser
- [ ] Target website is accessible
- [ ] Network connectivity is stable
- [ ] Sufficient disk space for output
- [ ] Proper permissions for file operations

---

This troubleshooting guide covers the most common issues encountered when using Web Scrapper CLI. For issues not covered here, please consult the community resources or submit a detailed bug report.