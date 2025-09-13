"""
WorkflowStep and step configuration models for the web scraper system.
These models define the structure for individual workflow steps and their configurations.
"""

# Standard library imports
from typing import Any, Dict, List, Literal, Optional, Union

# Third-party imports
from pydantic import BaseModel, Field


class Cookie(BaseModel):
    """HTTP cookie model for web scraping sessions."""

    name: str = Field(..., min_length=1, description="Cookie name")
    value: str = Field(..., description="Cookie value")
    domain: str = Field(..., min_length=1, description="Cookie domain")
    path: str = Field(..., min_length=1, description="Cookie path")
    expires: Optional[int] = Field(
        default=None, ge=0, description="Cookie expiration timestamp"
    )
    http_only: bool = Field(default=False, description="Whether cookie is HTTP-only")
    secure: bool = Field(default=False, description="Whether cookie requires HTTPS")


class InitStepConfig(BaseModel):
    """Configuration for init workflow step."""

    url: str = Field(..., min_length=1, description="Target URL to navigate to")
    wait_for: Optional[Union[str, int]] = Field(
        default=None, description="CSS selector or milliseconds to wait"
    )
    cookies: List[Cookie] = Field(
        default_factory=list, description="Cookies to set before navigation"
    )
    headers: Dict[str, str] = Field(
        default_factory=dict, description="HTTP headers to include"
    )


class DiscoverStepConfig(BaseModel):
    """Configuration for discover workflow step."""

    selectors: Dict[str, str] = Field(
        ..., min_length=1, description="CSS selectors for different element types"
    )
    pagination: Optional[Dict[str, Any]] = Field(
        default=None, description="Pagination configuration"
    )


class ExtractStepConfig(BaseModel):
    """Configuration for extract workflow step."""

    elements: Dict[str, Dict[str, Any]] = Field(
        ..., min_length=1, description="Element extraction configuration"
    )


class PaginateStepConfig(BaseModel):
    """Configuration for paginate workflow step."""

    next_page_selector: str = Field(
        ..., min_length=1, description="CSS selector for next page link"
    )
    max_pages: Optional[int] = Field(
        default=None, ge=1, description="Maximum number of pages to scrape"
    )
    wait_after_click: int = Field(
        default=1000, ge=0, description="Milliseconds to wait after clicking next"
    )
    stop_condition: Optional[Dict[str, Any]] = Field(
        default=None, description="Condition to stop pagination"
    )


class WorkflowStep(BaseModel):
    """Individual workflow step definition."""

    id: str = Field(
        ..., pattern=r"^[a-zA-Z0-9_-]+$", description="Unique step identifier"
    )
    command: Literal["init", "discover", "extract", "paginate"] = Field(
        ..., description="Command to execute"
    )
    config: Dict[str, Any] = Field(
        default_factory=dict, description="Step-specific configuration"
    )
    retries: int = Field(default=3, ge=0, le=10, description="Number of retry attempts")
    timeout: int = Field(
        default=30000, gt=0, le=300000, description="Timeout in milliseconds"
    )
    continue_on_error: bool = Field(
        default=False, description="Whether to continue workflow on step failure"
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "examples": [
                {
                    "id": "init-step",
                    "command": "init",
                    "config": {
                        "url": "https://example.com",
                        "wait_for": "body",
                        "headers": {"User-Agent": "scrapper/1.0.0"},
                    },
                    "retries": 3,
                    "timeout": 30000,
                    "continue_on_error": False,
                },
                {
                    "id": "extract-products",
                    "command": "extract",
                    "config": {
                        "elements": {
                            "title": {"selector": ".product-title", "type": "text"},
                            "price": {
                                "selector": ".price",
                                "type": "text",
                                "transform": "float",
                            },
                        }
                    },
                    "retries": 5,
                    "timeout": 45000,
                },
            ]
        }
