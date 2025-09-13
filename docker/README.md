# 🐳 Docker Deployment Guide

This directory contains Docker configuration files for deploying Web Scrapper CLI in containerized environments.

## 🚀 Quick Start

### 1. Build and Run with Docker Compose

```bash
# Start all services (scrapper + databases)
docker-compose up -d

# View logs
docker-compose logs -f scrapper

# Run a specific workflow
docker-compose exec scrapper scrapper run /app/examples/news-headlines.json
```

### 2. Production Deployment

```bash
# Build production image
docker build -t web-scrapper-cli:1.0.0 .

# Run with external database
docker run -d \
  --name scrapper-production \
  -v $(pwd)/workflows:/app/workflows:ro \
  -v $(pwd)/output:/app/data \
  -e POSTGRES_HOST=your-db-host \
  -e POSTGRES_USER=scrapper \
  -e POSTGRES_PASSWORD=your-password \
  web-scrapper-cli:1.0.0 \
  scrapper run /app/workflows/production-workflow.json
```

## 📁 File Structure

```
docker/
├── README.md              # This file
├── init-postgres.sql      # PostgreSQL initialization script
└── docker-entrypoint.sh   # Container entrypoint with utilities

# Docker configuration files
├── Dockerfile             # Production image
├── Dockerfile.dev         # Development image
├── docker-compose.yml     # Production services
├── docker-compose.dev.yml # Development override
└── .dockerignore         # Build context exclusions
```

## 🏗️ Images

### Production Image (`Dockerfile`)
- **Base**: `python:3.11-slim`
- **Size**: ~500MB (optimized)
- **Features**:
  - All scraping providers (BeautifulSoup, Scrapy, Playwright)
  - PostgreSQL and MongoDB drivers
  - Non-root user for security
  - Health checks
  - Playwright browsers pre-installed

### Development Image (`Dockerfile.dev`)
- **Base**: `python:3.11-slim`
- **Features**:
  - Hot reloading with volume mounts
  - Development tools (IPython, Jupyter, debugpy)
  - Poetry for dependency management
  - Git for version control

## 🚀 Usage Examples

### Run Example Workflows

```bash
# News headlines scraping
docker-compose exec scrapper scrapper run /app/examples/news-headlines.json

# E-commerce product scraping
docker-compose exec scrapper scrapper run /app/examples/ecommerce-products.json

# Job listings with high concurrency
docker-compose exec scrapper scrapper run /app/examples/job-listings.json
```

### Custom Workflow Execution

```bash
# Mount your workflows directory
docker run -v $(pwd)/my-workflows:/app/workflows web-scrapper-cli:1.0.0 \
  scrapper run /app/workflows/custom-workflow.json

# With output directory
docker run \
  -v $(pwd)/workflows:/app/workflows:ro \
  -v $(pwd)/output:/app/data \
  web-scrapper-cli:1.0.0 \
  scrapper run /app/workflows/custom-workflow.json
```

### Development Mode

```bash
# Start development environment
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Access development container
docker-compose exec scrapper bash

# Run tests inside container
docker-compose exec scrapper pytest

# Install additional packages
docker-compose exec scrapper poetry add new-package
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SCRAPPER_LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `POSTGRES_HOST` | `postgres` | PostgreSQL hostname |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `POSTGRES_DB` | `scrapper_data` | Database name |
| `POSTGRES_USER` | `scrapper` | Database username |
| `POSTGRES_PASSWORD` | `scrapper_pass` | Database password |
| `MONGODB_URL` | `mongodb://mongodb:27017/scrapper_data` | MongoDB connection string |

### Volume Mounts

| Host Path | Container Path | Purpose |
|-----------|----------------|---------|
| `./workflows` | `/app/workflows` | Workflow definitions (read-only) |
| `./output` | `/app/data` | Scraped data output |
| `./logs` | `/app/logs` | Application logs |

## 🎯 Production Best Practices

### 1. Resource Limits

```yaml
services:
  scrapper:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### 2. Health Monitoring

```yaml
healthcheck:
  test: ["CMD", "scrapper", "--version"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### 3. Security Configuration

```yaml
services:
  scrapper:
    user: "1000:1000"  # Run as specific user
    read_only: true     # Read-only filesystem
    tmpfs:
      - /tmp
      - /app/logs
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
```

### 4. Secrets Management

```yaml
services:
  scrapper:
    secrets:
      - db_password
      - api_keys
    environment:
      - POSTGRES_PASSWORD_FILE=/run/secrets/db_password

secrets:
  db_password:
    file: ./secrets/db_password.txt
  api_keys:
    external: true
```

## 🔍 Troubleshooting

### Common Issues

1. **Container Exits Immediately**
   ```bash
   # Check logs
   docker-compose logs scrapper

   # Interactive debugging
   docker-compose run scrapper bash
   ```

2. **Database Connection Failed**
   ```bash
   # Verify database is running
   docker-compose ps postgres

   # Test connection
   docker-compose exec postgres psql -U scrapper -d scrapper_data
   ```

3. **Playwright Browser Issues**
   ```bash
   # Reinstall browsers
   docker-compose exec scrapper playwright install chromium

   # Run in headed mode for debugging
   docker-compose run -e PLAYWRIGHT_HEADLESS=false scrapper
   ```

4. **Memory Issues**
   ```bash
   # Monitor resource usage
   docker stats scrapper

   # Increase memory limit
   docker-compose up --scale scrapper=1 --memory=2g
   ```

### Debug Commands

```bash
# View all container processes
docker-compose top

# Execute commands in running container
docker-compose exec scrapper scrapper providers list

# Access PostgreSQL
docker-compose exec postgres psql -U scrapper -d scrapper_data

# View real-time logs
docker-compose logs -f --tail=100 scrapper
```

## 📊 Monitoring & Observability

### Log Aggregation

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### Metrics Collection

```yaml
# Add Prometheus monitoring
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./docker/prometheus.yml:/etc/prometheus/prometheus.yml
```

## 🚀 Scaling & Performance

### Horizontal Scaling

```bash
# Scale scrapper instances
docker-compose up --scale scrapper=3

# Load balance with nginx
docker-compose -f docker-compose.yml -f docker-compose.scale.yml up
```

### Performance Tuning

```yaml
services:
  scrapper:
    environment:
      # Optimize for concurrent scraping
      - SCRAPY_CONCURRENT_REQUESTS=32
      - PLAYWRIGHT_BROWSER_COUNT=4
      - POSTGRES_POOL_SIZE=20
```

---

**Happy Containerized Scraping! 🐳**
