# Installation

This guide covers all installation methods for the Web Scrapper CLI, from simple PyPI installation to development setup.

## 🐍 Python Requirements

Web Scrapper CLI requires **Python 3.11 or higher**. Check your Python version:

```bash
python --version  # Should be 3.11+
```

If you need to upgrade Python, visit [python.org](https://www.python.org/downloads/) or use a version manager like [pyenv](https://github.com/pyenv/pyenv).

## 📦 Installation Methods

### Method 1: PyPI Installation (Recommended)

Install the latest stable release from PyPI:

```bash
# Basic installation
pip install web-scrapper-cli

# Install with all optional dependencies
pip install web-scrapper-cli[all]

# Install specific provider dependencies
pip install web-scrapper-cli[postgresql,playwright]
```

#### Optional Dependencies

| Extra | Providers | Install Command |
|-------|-----------|-----------------|
| `postgresql` | PostgreSQL storage | `pip install web-scrapper-cli[postgresql]` |
| `mongodb` | MongoDB storage | `pip install web-scrapper-cli[mongodb]` |
| `playwright` | Browser automation | `pip install web-scrapper-cli[playwright]` |
| `scrapy` | Industrial scraping | `pip install web-scrapper-cli[scrapy]` |
| `all` | All providers | `pip install web-scrapper-cli[all]` |

### Method 2: Pipx Installation (Isolated)

For isolated installation without affecting system Python:

```bash
# Install pipx if not already installed
pip install --user pipx
pipx ensurepath

# Install web-scrapper-cli
pipx install web-scrapper-cli

# Install with extras
pipx install "web-scrapper-cli[all]"
```

### Method 3: Development Installation

For contributing or customizing the scrapper:

```bash
# Clone the repository
git clone https://github.com/shafqat-a/scrapper.git
cd scrapper

# Install in development mode
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### Method 4: Docker Installation

Run scrapper in a containerized environment:

```bash
# Pull the official image
docker pull ghcr.io/shafqat-a/scrapper:latest

# Run a workflow
docker run --rm -v $(pwd):/workspace ghcr.io/shafqat-a/scrapper:latest \
  scrapper run /workspace/my-workflow.json

# Interactive shell
docker run --rm -it ghcr.io/shafqat-a/scrapper:latest bash
```

## 🎯 Verify Installation

After installation, verify that scrapper is working correctly:

```bash
# Check version
scrapper --version

# Show help
scrapper --help

# List available providers
scrapper providers list
```

Expected output:
```
$ scrapper --version
Web Scrapper CLI v1.0.0

$ scrapper providers list
┌─────────────┬─────────────┬─────────┬──────────────────────────┐
│ Provider    │ Type        │ Version │ Description              │
├─────────────┼─────────────┼─────────┼──────────────────────────┤
│ beautifulsoup│ scraping   │ 1.0.0   │ HTML parsing, lightweight│
│ scrapy      │ scraping    │ 1.0.0   │ Industrial-grade scraper │
│ playwright  │ scraping    │ 1.0.0   │ Browser automation       │
│ csv         │ storage     │ 1.0.0   │ CSV file storage         │
│ json        │ storage     │ 1.0.0   │ JSON file storage        │
│ postgresql  │ storage     │ 1.0.0   │ PostgreSQL database      │
└─────────────┴─────────────┴─────────┴──────────────────────────┘
```

## 🔧 Provider-Specific Setup

### Playwright Setup

Playwright requires browser binaries to be installed:

```bash
# Install scrapper with playwright
pip install web-scrapper-cli[playwright]

# Install browser binaries
playwright install

# Install specific browsers
playwright install chromium firefox webkit
```

### PostgreSQL Setup

For PostgreSQL storage provider:

```bash
# Install with PostgreSQL support
pip install web-scrapper-cli[postgresql]

# Ensure PostgreSQL is running
# Ubuntu/Debian:
sudo systemctl start postgresql

# macOS with Homebrew:
brew services start postgresql

# Create database
createdb scrapper_data
```

### MongoDB Setup

For MongoDB storage provider:

```bash
# Install with MongoDB support
pip install web-scrapper-cli[mongodb]

# Start MongoDB service
# Ubuntu/Debian:
sudo systemctl start mongod

# macOS with Homebrew:
brew services start mongodb-community
```

### Scrapy Setup

Scrapy provider works out of the box, but some optional dependencies enhance functionality:

```bash
# Full Scrapy installation
pip install web-scrapper-cli[scrapy]

# Additional Scrapy tools (optional)
pip install scrapy-splash scrapy-proxy-middleware
```

## 🐳 Docker Setup

### Using Pre-built Image

```bash
# Pull latest image
docker pull ghcr.io/shafqat-a/scrapper:latest

# Create alias for convenience
alias scrapper-docker="docker run --rm -v \$(pwd):/workspace ghcr.io/shafqat-a/scrapper:latest scrapper"

# Use like regular scrapper
scrapper-docker run my-workflow.json
```

### Building Custom Image

```dockerfile
FROM ghcr.io/shafqat-a/scrapper:latest

# Add custom providers or configurations
COPY my-providers/ /app/providers/
COPY my-config.json /app/config.json

# Install additional dependencies
RUN pip install custom-package

CMD ["scrapper", "--config", "/app/config.json"]
```

### Docker Compose for Development

```yaml
# docker-compose.yml
version: '3.8'
services:
  scrapper:
    build: .
    volumes:
      - ./workflows:/app/workflows
      - ./output:/app/output
    environment:
      - SCRAPPER_LOG_LEVEL=DEBUG
    depends_on:
      - postgres
      - mongodb
  
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: scrapper
      POSTGRES_USER: scrapper
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
  
  mongodb:
    image: mongo:7
    ports:
      - "27017:27017"
```

## 🛠 Troubleshooting Installation

### Common Issues

#### Python Version Mismatch
```bash
# Error: Requires Python >=3.11
# Solution: Upgrade Python or use pyenv
pyenv install 3.11.0
pyenv global 3.11.0
```

#### Permission Denied (pip)
```bash
# Error: Permission denied when installing
# Solution: Use --user flag or virtual environment
pip install --user web-scrapper-cli
# OR
python -m venv scrapper-env
source scrapper-env/bin/activate
pip install web-scrapper-cli
```

#### Missing System Dependencies
```bash
# Error: Failed building lxml
# Solution: Install system dependencies

# Ubuntu/Debian
sudo apt-get install python3-dev libxml2-dev libxslt1-dev

# CentOS/RHEL
sudo yum install python3-devel libxml2-devel libxslt-devel

# macOS
brew install libxml2 libxslt
```

#### Playwright Installation Issues
```bash
# Error: Playwright browsers not found
# Solution: Install browsers manually
playwright install

# Error: Permission denied for browser installation
# Solution: Use --with-deps flag
playwright install --with-deps
```

### Environment Variables

Configure scrapper behavior with environment variables:

```bash
# Set log level
export SCRAPPER_LOG_LEVEL=DEBUG

# Set default config file
export SCRAPPER_CONFIG_FILE=/path/to/config.json

# Set storage directory
export SCRAPPER_DATA_DIR=/path/to/data

# Set cache directory
export SCRAPPER_CACHE_DIR=/path/to/cache
```

### Virtual Environment Setup (Recommended)

Always use virtual environments to avoid dependency conflicts:

```bash
# Create virtual environment
python -m venv scrapper-env

# Activate (Linux/macOS)
source scrapper-env/bin/activate

# Activate (Windows)
scrapper-env\Scripts\activate

# Install scrapper
pip install web-scrapper-cli

# Deactivate when done
deactivate
```

## ✅ Verification Checklist

After installation, verify everything works:

- [ ] `scrapper --version` shows correct version
- [ ] `scrapper --help` displays help information
- [ ] `scrapper providers list` shows available providers
- [ ] `scrapper validate examples/news-headlines.json` validates successfully
- [ ] Required storage systems (PostgreSQL/MongoDB) are accessible if needed
- [ ] Playwright browsers are installed if using playwright provider

## 🚀 Next Steps

Now that you have Web Scrapper CLI installed:

1. **[Quick Start](quickstart.md)** - Create your first workflow in 5 minutes
2. **[Basic Concepts](concepts.md)** - Understand core concepts and terminology  
3. **[Creating Workflows](../user-guide/creating-workflows.md)** - Learn workflow creation
4. **[Examples](../examples/basic.md)** - Explore practical examples

---

**Need Help?** Check the [Troubleshooting Guide](../reference/troubleshooting.md) or open an issue on [GitHub](https://github.com/shafqat-a/scrapper/issues).