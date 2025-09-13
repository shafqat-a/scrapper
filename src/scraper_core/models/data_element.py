"""
DataElement and ElementMetadata models for the web scraper system.
These models define the structure for scraped data elements and their metadata.
"""
# Standard library imports
from datetime import datetime
from typing import Any, Literal, Optional
# Third-party imports
from pydantic import BaseModel, Field, ConfigDict
class ElementMetadata(BaseModel):
    """Metadata for scraped data elements."""
    selector: str = Field(
        ..., min_length=1, description="CSS selector used to find element"
    )
    source_url: str = Field(
        ..., min_length=1, description="URL where element was found"
    )
    timestamp: datetime = Field(..., description="Timestamp when element was scraped")
    xpath: Optional[str] = Field(
        default=None, description="XPath selector (if available)"
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "selector": "h1.product-title",
                    "source_url": "https://example.com/product/123",
                    "timestamp": "2023-12-25T10:30:45",
                    "xpath": "/html/body/div[1]/h1",
                },
                {
                    "selector": ".price",
                    "source_url": "https://shop.example.com/item/456",
                    "timestamp": "2023-12-25T10:35:22",
                },
            ]
        }
    )
class DataElement(BaseModel):
    """Individual scraped data element."""
    id: str = Field(..., min_length=1, description="Unique element identifier")
    type: Literal["text", "link", "image", "structured"] = Field(
        ..., description="Type of scraped element"
    )
    value: Any = Field(..., description="Scraped value (content depends on type)")
    metadata: ElementMetadata = Field(..., description="Element metadata")
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "title-element-1",
                    "type": "text",
                    "value": "Sample Product Title",
                    "metadata": {
                        "selector": "h1.product-title",
                        "source_url": "https://example.com/product/123",
                        "timestamp": "2023-12-25T10:30:45",
                        "xpath": "/html/body/div[1]/h1",
                    },
                },
                {
                    "id": "product-link-2",
                    "type": "link",
                    "value": {
                        "href": "https://example.com/product/456",
                        "text": "View Product Details",
                        "target": "_blank",
                    },
                    "metadata": {
                        "selector": "a.product-link",
                        "source_url": "https://example.com/category/electronics",
                        "timestamp": "2023-12-25T10:32:15",
                    },
                },
                {
                    "id": "product-image-3",
                    "type": "image",
                    "value": {
                        "src": "https://example.com/images/product-456.jpg",
                        "alt": "Product 456 - High Quality Widget",
                        "width": 300,
                        "height": 200,
                    },
                    "metadata": {
                        "selector": "img.product-image",
                        "source_url": "https://example.com/product/456",
                        "timestamp": "2023-12-25T10:33:45",
                        "xpath": "//img[@class='product-image']",
                    },
                },
                {
                    "id": "product-details-4",
                    "type": "structured",
                    "value": {
                        "product": {
                            "name": "Advanced Widget Pro",
                            "price": 199.99,
                            "currency": "USD",
                            "availability": "In Stock",
                            "rating": 4.5,
                            "reviews": 127,
                        }
                    },
                    "metadata": {
                        "selector": ".product-details",
                        "source_url": "https://example.com/product/pro-widget",
                        "timestamp": "2023-12-25T10:35:00",
                    },
                },
            ]
        }
    )
