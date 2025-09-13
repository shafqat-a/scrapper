"""
Workflow Pydantic models for the web scraper system.
These models define the structure and validation for JSON workflow definitions.
"""

# Standard library imports
from datetime import datetime

# Import after definition to avoid circular imports
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional

# Third-party imports
from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    # Local folder imports
    from .workflow_step import WorkflowStep


class SchemaField(BaseModel):
    """Database schema field definition."""

    type: Literal["string", "number", "boolean", "date", "json"] = Field(
        ..., description="Data type of the field"
    )
    required: bool = Field(default=False, description="Whether the field is required")
    max_length: Optional[int] = Field(
        default=None, ge=1, description="Maximum length for string fields"
    )
    index: bool = Field(default=False, description="Whether to create database index")


class SchemaDefinition(BaseModel):
    """Database schema definition for scraped data."""

    name: str = Field(..., min_length=1, max_length=100, description="Schema name")
    fields: Dict[str, SchemaField] = Field(..., description="Field definitions")
    primary_key: List[str] = Field(
        default_factory=list, description="Primary key field names"
    )


class WorkflowMetadata(BaseModel):
    """Metadata for workflow definitions."""

    name: str = Field(..., min_length=1, max_length=100, description="Workflow name")
    description: str = Field(
        ..., min_length=1, max_length=500, description="Workflow description"
    )
    author: str = Field(..., min_length=1, description="Author of the workflow")
    created: datetime = Field(
        default_factory=datetime.now, description="Creation timestamp"
    )
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    target_site: str = Field(..., description="Target website URL or domain")


class ScrapingConfig(BaseModel):
    """Scraping provider configuration."""

    provider: str = Field(..., min_length=1, description="Scraping provider name")
    config: Dict[str, Any] = Field(
        default_factory=dict, description="Provider-specific configuration"
    )


class StorageConfig(BaseModel):
    """Storage provider configuration."""

    provider: str = Field(..., min_length=1, description="Storage provider name")
    config: Dict[str, Any] = Field(
        default_factory=dict, description="Provider-specific configuration"
    )
    data_schema: Optional[SchemaDefinition] = Field(
        default=None, description="Optional schema definition for structured storage"
    )


# WorkflowStep is now imported from .workflow_step
class PostProcessingStep(BaseModel):
    """Post-processing step for data transformation."""

    type: Literal["filter", "transform", "validate", "deduplicate"] = Field(
        ..., description="Type of post-processing operation"
    )
    config: Dict[str, Any] = Field(
        default_factory=dict, description="Operation-specific configuration"
    )


class Workflow(BaseModel):
    """Complete workflow definition."""

    version: str = Field(
        ..., pattern=r"^\d+\.\d+\.\d+$", description="Workflow version (semantic)"
    )
    metadata: WorkflowMetadata = Field(..., description="Workflow metadata")
    scraping: ScrapingConfig = Field(..., description="Scraping provider configuration")
    storage: StorageConfig = Field(..., description="Storage provider configuration")
    steps: List["WorkflowStep"] = Field(
        ..., min_length=1, description="Workflow execution steps"
    )
    post_processing: Optional[List[PostProcessingStep]] = Field(
        default=None, description="Optional post-processing steps"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "version": "1.0.0",
                "metadata": {
                    "name": "News Headlines Scraper",
                    "description": "Extract news headlines from example news site",
                    "author": "quickstart-user",
                    "target_site": "https://example-news.com",
                    "tags": ["news", "headlines"],
                },
                "scraping": {
                    "provider": "beautifulsoup",
                    "config": {"parser": "lxml", "timeout": 10000},
                },
                "storage": {
                    "provider": "csv",
                    "config": {"file_path": "./scraped-news.csv", "headers": True},
                },
                "steps": [
                    {
                        "id": "init",
                        "command": "init",
                        "config": {"url": "https://example-news.com"},
                    },
                    {
                        "id": "extract-headlines",
                        "command": "extract",
                        "config": {
                            "elements": {
                                "headline": {
                                    "selector": "h2.article-title",
                                    "type": "text",
                                }
                            }
                        },
                    },
                ],
            }
        }
    )
