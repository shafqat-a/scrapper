"""
Provider configuration models for the web scraper system.
These models define the structure for configuring different scraping and storage providers.
"""
# Standard library imports
from typing import Literal, Optional
# Third-party imports
from pydantic import BaseModel, Field, ConfigDict
# Local folder imports
# Local imports - Viewport is already defined in page_context.py
from .page_context import Viewport
class ConnectionConfig(BaseModel):
    """Base configuration for provider connections."""
    pass
# Scraping Provider Configurations
class ScrapyConfig(ConnectionConfig):
    """Configuration for Scrapy scraping provider."""
    concurrent_requests: int = Field(
        default=8, ge=1, le=100, description="Number of concurrent requests"
    )
    download_delay: float = Field(
        default=0.5, ge=0, description="Delay between requests in seconds"
    )
    randomize_download_delay: bool = Field(
        default=True, description="Randomize download delay (0.5 * to 1.5 * delay)"
    )
    user_agent: Optional[str] = Field(
        default=None, description="User agent string to use"
    )
    robotstxt_obey: bool = Field(default=True, description="Whether to obey robots.txt")
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "concurrent_requests": 16,
                "download_delay": 1.0,
                "randomize_download_delay": False,
                "user_agent": "MyBot/1.0",
                "robotstxt_obey": True,
            }
    )
    )
class PlaywrightConfig(ConnectionConfig):
    """Configuration for Playwright browser automation provider."""
    browser: Literal["chromium", "firefox", "webkit"] = Field(
        default="chromium", description="Browser engine to use"
    )
    headless: bool = Field(default=True, description="Run browser in headless mode")
    viewport: Viewport = Field(
        default_factory=lambda: Viewport(width=1920, height=1080),
        description="Browser viewport dimensions",
    )
    user_agent: Optional[str] = Field(
        default=None, description="User agent string to use"
    )
    timeout: int = Field(
        default=30000, gt=0, description="Default timeout in milliseconds"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "browser": "firefox",
                "headless": False,
                "viewport": {"width": 1280, "height": 720},
                "user_agent": "Mozilla/5.0 (compatible; PlaywrightBot/1.0)",
                "timeout": 60000,
            }
    )
        }
class BeautifulSoupConfig(ConnectionConfig):
    """Configuration for BeautifulSoup HTML parsing provider."""
    parser: Literal["html.parser", "lxml", "html5lib"] = Field(
        default="lxml", description="HTML parser to use"
    )
    timeout: int = Field(
        default=10000, gt=0, description="Request timeout in milliseconds"
    )
    user_agent: Optional[str] = Field(
        default=None, description="User agent string to use"
    )
    follow_redirects: bool = Field(
        default=True, description="Whether to follow HTTP redirects"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "parser": "html.parser",
                "timeout": 5000,
                "user_agent": "Custom Parser/1.0",
                "follow_redirects": False,
            }
    )
        }
# Storage Provider Configurations
class CSVStorageConfig(ConnectionConfig):
    """Configuration for CSV file storage provider."""
    file_path: str = Field(..., min_length=1, description="Path to the CSV file")
    delimiter: str = Field(default=",", description="CSV field delimiter")
    headers: bool = Field(default=True, description="Whether to include column headers")
    append: bool = Field(
        default=False, description="Whether to append to existing file"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "file_path": "/tmp/scraped_data.csv",
                "delimiter": ";",
                "headers": False,
                "append": True,
            }
    )
        }
class PostgreSQLStorageConfig(ConnectionConfig):
    """Configuration for PostgreSQL database storage provider."""
    connection_string: str = Field(
        ..., min_length=1, description="PostgreSQL connection string"
    )
    table_name: str = Field(..., min_length=1, description="Database table name")
    create_table: bool = Field(
        default=True, description="Whether to create table if not exists"
    )
    batch_size: int = Field(
        default=1000, ge=1, description="Batch size for bulk inserts"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "connection_string": "postgresql://user:pass@localhost:5432/mydb",
                "table_name": "scraped_products",
                "create_table": False,
                "batch_size": 500,
            }
    )
        }
class MongoDBStorageConfig(ConnectionConfig):
    """Configuration for MongoDB storage provider."""
    connection_string: str = Field(
        ..., min_length=1, description="MongoDB connection string"
    )
    database: str = Field(..., min_length=1, description="Database name")
    collection: str = Field(..., min_length=1, description="Collection name")
    upsert: bool = Field(
        default=False, description="Whether to use upsert for duplicates"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "connection_string": "mongodb://user:pass@localhost:27017/mydb",
                "database": "scraping_db",
                "collection": "products",
                "upsert": True,
            }
    )
        }
class SQLiteStorageConfig(ConnectionConfig):
    """Configuration for SQLite database storage provider."""
    database_path: str = Field(
        ..., min_length=1, description="Path to SQLite database file"
    )
    table_name: str = Field(..., min_length=1, description="Database table name")
    create_table: bool = Field(
        default=True, description="Whether to create table if not exists"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "database_path": "/tmp/scraping.db",
                "table_name": "scraped_data",
                "create_table": False,
            }
    )
        }
