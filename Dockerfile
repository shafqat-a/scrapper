# Web Scrapper CLI - Production Docker Image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for web scraping
RUN apt-get update && apt-get install -y \
    # Essential build tools
    gcc \
    g++ \
    make \
    # Network and SSL
    ca-certificates \
    curl \
    wget \
    # Database drivers
    libpq-dev \
    # Playwright dependencies
    libnss3 \
    libatk-bridge2.0-0 \
    libxcomposite1 \
    libxrandr2 \
    libxdamage1 \
    libxss1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# Create app user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install Poetry
RUN pip install poetry==1.6.1

# Configure Poetry: don't create virtual environment in container
RUN poetry config virtualenvs.create false

# Install Python dependencies
RUN poetry install --no-dev --no-interaction --no-ansi

# Install Playwright browsers (for headless browsing)
RUN playwright install chromium --with-deps

# Copy application code
COPY src/ ./src/
COPY examples/ ./examples/
COPY README.md CHANGELOG.md LICENSE ./

# Install the application in editable mode
RUN pip install -e .

# Create directories for data and logs
RUN mkdir -p /app/data /app/logs && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD scrapper --version || exit 1

# Default command
CMD ["scrapper", "--help"]

# Labels for metadata
LABEL org.opencontainers.image.title="Web Scrapper CLI" \
      org.opencontainers.image.description="Production-ready web scraping framework with pluggable providers" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.authors="Scrapper Team <team@scrapper.dev>" \
      org.opencontainers.image.url="https://github.com/shafqat-a/scrapper" \
      org.opencontainers.image.source="https://github.com/shafqat-a/scrapper" \
      org.opencontainers.image.licenses="MIT"
