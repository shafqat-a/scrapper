"""
PageContext and browser-related models for the web scraper system.
These models define the structure for browser context and viewport information.
"""

# Standard library imports
from typing import List

# Third-party imports
from pydantic import BaseModel, Field

# Local folder imports
# Local imports - Cookie is already defined in workflow_step.py
from .workflow_step import Cookie


class Viewport(BaseModel):
    """Browser viewport dimensions."""

    width: int = Field(ge=320, le=7680, description="Viewport width in pixels")
    height: int = Field(ge=240, le=4320, description="Viewport height in pixels")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "examples": [
                {"width": 1920, "height": 1080},  # Desktop HD
                {"width": 1366, "height": 768},  # Laptop
                {"width": 375, "height": 667},  # iPhone
                {"width": 414, "height": 896},  # iPhone XR
                {"width": 768, "height": 1024},  # iPad
            ]
        }


class PageContext(BaseModel):
    """Current page context during web scraping session."""

    url: str = Field(..., min_length=1, description="Current page URL")
    title: str = Field(..., description="Page title")
    cookies: List[Cookie] = Field(
        default_factory=list, description="Current session cookies"
    )
    navigation_history: List[str] = Field(
        default_factory=list, description="Navigation history URLs"
    )
    viewport: Viewport = Field(
        default_factory=lambda: Viewport(width=1920, height=1080),
        description="Browser viewport dimensions",
    )
    user_agent: str = Field(default="scrapper/1.0.0", description="User agent string")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "examples": [
                {
                    "url": "https://example.com/products?page=1",
                    "title": "Products - Example Store",
                    "cookies": [
                        {
                            "name": "session_id",
                            "value": "abc123def456",
                            "domain": ".example.com",
                            "path": "/",
                            "expires": 1703505045,
                            "http_only": True,
                            "secure": True,
                        }
                    ],
                    "navigation_history": [
                        "https://example.com",
                        "https://example.com/categories",
                        "https://example.com/products?page=1",
                    ],
                    "viewport": {"width": 1920, "height": 1080},
                    "user_agent": "Mozilla/5.0 (compatible; scrapper/2.0.0)",
                },
                {
                    "url": "https://mobile.example.com",
                    "title": "Mobile Example",
                    "viewport": {"width": 375, "height": 667},
                    "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
                },
            ]
        }
