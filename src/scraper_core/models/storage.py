"""
Storage and data persistence models for the web scraper system.
These models define the structure for storing scraped data and managing schemas.
"""
# Standard library imports
from datetime import datetime
from typing import Any, Dict, List, Optional
# Third-party imports
from pydantic import BaseModel, Field, ConfigDict
# Local folder imports
# Local imports - SchemaDefinition and SchemaField are in workflow.py
from .workflow import SchemaDefinition, SchemaField
class ScrapedItem(BaseModel):
    """Individual scraped data item for storage."""
    id: str = Field(..., min_length=1, description="Unique item identifier")
    source_url: str = Field(..., min_length=1, description="URL where item was scraped")
    scraped_at: datetime = Field(
        default_factory=datetime.now, description="Timestamp when scraped"
    )
    data: Dict[str, Any] = Field(..., description="Scraped data fields")
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional metadata"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "product_123",
                    "source_url": "https://example.com/products/123",
                    "scraped_at": "2023-12-25T10:30:45",
                    "data": {
                        "title": "Premium Widget",
                        "price": 99.99,
                        "currency": "USD",
                        "availability": "In Stock",
                    },
                    "metadata": {
                        "scraper_version": "1.0.0",
                        "workflow_id": "product_scraper",
                    },
                }
            ]
        }
    )


class BatchInsertResult(BaseModel):
    """Result of a batch insert operation."""
    success: bool = Field(..., description="Whether the batch insert was successful")
    inserted_count: int = Field(
        ..., ge=0, description="Number of items successfully inserted"
    )
    failed_count: int = Field(
        default=0, ge=0, description="Number of items that failed to insert"
    )
    errors: List[str] = Field(
        default_factory=list, description="List of error messages"
    )
    duration_ms: int = Field(
        ..., ge=0, description="Operation duration in milliseconds"
    )
    model_config = ConfigDict(
        
        json_schema_extra = {
            "examples": [
                {
                    "success": True,
                    "inserted_count": 150,
                    "failed_count": 0,
                    "errors": [],
                    "duration_ms": 1250,
                },
                {
                    "success": False,
                    "inserted_count": 98,
                    "failed_count": 2,
                    "errors": [
                        "Duplicate key violation for item_id: product_456",
                        "Invalid data type for price field in item_id: product_789",
                    ],
                    "duration_ms": 2100,
                },
            ]
        }
    )


class StorageStats(BaseModel):
    """Storage provider statistics and metrics."""
    total_items: int = Field(..., ge=0, description="Total number of items stored")
    total_size_bytes: int = Field(..., ge=0, description="Total storage size in bytes")
    last_updated: datetime = Field(..., description="Timestamp of last update")
    provider_type: str = Field(..., min_length=1, description="Storage provider type")
    connection_info: Dict[str, Any] = Field(
        default_factory=dict, description="Connection information (no secrets)"
    )
    model_config = ConfigDict(
        
        json_schema_extra = {
            "examples": [
                {
                    "total_items": 10500,
                    "total_size_bytes": 52428800,  # 50MB
                    "last_updated": "2023-12-25T15:30:00",
                    "provider_type": "postgresql",
                    "connection_info": {
                        "host": "localhost",
                        "database": "scraper_db",
                        "table": "products",
                        "schema": "public",
                    },
                },
                {
                    "total_items": 2750,
                    "total_size_bytes": 1048576,  # 1MB
                    "last_updated": "2023-12-25T15:35:00",
                    "provider_type": "csv",
                    "connection_info": {
                        "file_path": "/data/scraped_items.csv",
                        "encoding": "utf-8",
                    },
                },
            ]
        }
    )


class StorageHealthCheck(BaseModel):
    """Storage provider health check result."""
    healthy: bool = Field(..., description="Whether the storage provider is healthy")
    response_time_ms: int = Field(
        ..., ge=0, description="Response time in milliseconds"
    )
    available_space_bytes: Optional[int] = Field(
        default=None, ge=0, description="Available storage space in bytes"
    )
    connection_status: str = Field(..., description="Connection status message")
    last_check: datetime = Field(
        default_factory=datetime.now, description="Timestamp of health check"
    )
    errors: List[str] = Field(
        default_factory=list, description="List of any error messages"
    )
    model_config = ConfigDict(
        
        json_schema_extra = {
            "examples": [
                {
                    "healthy": True,
                    "response_time_ms": 15,
                    "available_space_bytes": 10737418240,  # 10GB
                    "connection_status": "Connected successfully",
                    "last_check": "2023-12-25T15:40:00",
                    "errors": [],
                },
                {
                    "healthy": False,
                    "response_time_ms": 5000,
                    "available_space_bytes": None,
                    "connection_status": "Connection timeout",
                    "last_check": "2023-12-25T15:42:00",
                    "errors": [
                        "Connection timeout after 5000ms",
                        "Database not responding",
                    ],
                },
            ]
        }
    )
