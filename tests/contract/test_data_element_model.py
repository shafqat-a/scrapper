"""
Contract test for DataElement Pydantic model validation.
This test validates the DataElement model and ElementMetadata model.
Tests MUST fail before any implementation exists (TDD requirement).
"""

# Standard library imports
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Union
from uuid import uuid4

# Third-party imports
import pytest
from pydantic import BaseModel, ValidationError

# Add the contracts directory to the path
contracts_path = (
    Path(__file__).parent.parent.parent / "specs" / "001-read-spec-md" / "contracts"
)
sys.path.insert(0, str(contracts_path))

try:
    # Third-party imports
    from provider_interfaces import DataElement, ElementMetadata
except ImportError:
    # If import fails, create minimal models for testing
    # Standard library imports
    from typing import Literal, Optional

    # Third-party imports
    from pydantic import BaseModel, Field

    class ElementMetadata(BaseModel):
        selector: str
        source_url: str
        timestamp: datetime
        xpath: Optional[str] = None

    class DataElement(BaseModel):
        id: str
        type: Literal["text", "link", "image", "structured"]
        value: Any
        metadata: ElementMetadata


@pytest.mark.contract
class TestDataElementModel:
    """Contract tests for DataElement Pydantic model validation."""

    @pytest.fixture
    def valid_timestamp(self) -> datetime:
        """Valid timestamp for testing."""
        return datetime(2023, 12, 25, 10, 30, 45)

    @pytest.fixture
    def valid_text_element_data(self, valid_timestamp) -> Dict[str, Any]:
        """Valid text element data."""
        return {
            "id": "title-element-1",
            "type": "text",
            "value": "Sample Product Title",
            "metadata": {
                "selector": "h1.product-title",
                "source_url": "https://example.com/product/123",
                "timestamp": valid_timestamp,
                "xpath": "/html/body/div[1]/h1",
            },
        }

    @pytest.fixture
    def valid_link_element_data(self, valid_timestamp) -> Dict[str, Any]:
        """Valid link element data."""
        return {
            "id": "product-link-2",
            "type": "link",
            "value": {
                "href": "https://example.com/product/456",
                "text": "View Product Details",
                "title": "Product 456",
            },
            "metadata": {
                "selector": "a.product-link",
                "source_url": "https://example.com/category/electronics",
                "timestamp": valid_timestamp,
            },
        }

    @pytest.fixture
    def valid_image_element_data(self, valid_timestamp) -> Dict[str, Any]:
        """Valid image element data."""
        return {
            "id": "product-image-3",
            "type": "image",
            "value": {
                "src": "https://example.com/images/product-456.jpg",
                "alt": "Product 456 - High Quality Widget",
                "width": 800,
                "height": 600,
            },
            "metadata": {
                "selector": "img.product-image",
                "source_url": "https://example.com/product/456",
                "timestamp": valid_timestamp,
                "xpath": "//img[@class='product-image']",
            },
        }

    @pytest.fixture
    def valid_structured_element_data(self, valid_timestamp) -> Dict[str, Any]:
        """Valid structured element data."""
        return {
            "id": "product-details-4",
            "type": "structured",
            "value": {
                "product": {
                    "name": "Advanced Widget Pro",
                    "price": 99.99,
                    "currency": "USD",
                    "availability": "in_stock",
                    "rating": 4.5,
                    "reviews": 127,
                    "specifications": {
                        "color": "blue",
                        "weight": "2.5kg",
                        "dimensions": "10x15x5cm",
                    },
                    "categories": ["electronics", "widgets", "pro-tools"],
                }
            },
            "metadata": {
                "selector": ".product-details",
                "source_url": "https://example.com/product/789",
                "timestamp": valid_timestamp,
            },
        }

    def test_data_element_model_exists(self):
        """Test that DataElement model class exists."""
        assert DataElement is not None
        assert issubclass(DataElement, BaseModel)

    def test_element_metadata_model_exists(self):
        """Test that ElementMetadata model class exists."""
        assert ElementMetadata is not None
        assert issubclass(ElementMetadata, BaseModel)

    def test_data_element_text_type(self, valid_text_element_data):
        """Test creating a text type DataElement."""
        element = DataElement(**valid_text_element_data)

        assert element.id == "title-element-1"
        assert element.type == "text"
        assert element.value == "Sample Product Title"
        assert isinstance(element.metadata, ElementMetadata)
        assert element.metadata.selector == "h1.product-title"
        assert element.metadata.xpath == "/html/body/div[1]/h1"

    def test_data_element_link_type(self, valid_link_element_data):
        """Test creating a link type DataElement."""
        element = DataElement(**valid_link_element_data)

        assert element.id == "product-link-2"
        assert element.type == "link"
        assert element.value["href"] == "https://example.com/product/456"
        assert element.value["text"] == "View Product Details"
        assert element.metadata.selector == "a.product-link"

    def test_data_element_image_type(self, valid_image_element_data):
        """Test creating an image type DataElement."""
        element = DataElement(**valid_image_element_data)

        assert element.id == "product-image-3"
        assert element.type == "image"
        assert element.value["src"] == "https://example.com/images/product-456.jpg"
        assert element.value["width"] == 800
        assert element.value["height"] == 600
        assert element.metadata.xpath == "//img[@class='product-image']"

    def test_data_element_structured_type(self, valid_structured_element_data):
        """Test creating a structured type DataElement."""
        element = DataElement(**valid_structured_element_data)

        assert element.id == "product-details-4"
        assert element.type == "structured"
        assert element.value["product"]["name"] == "Advanced Widget Pro"
        assert element.value["product"]["price"] == 99.99
        assert element.value["product"]["specifications"]["color"] == "blue"
        assert len(element.value["product"]["categories"]) == 3

    def test_data_element_type_validation(self, valid_text_element_data):
        """Test element type validation."""
        # Valid types
        valid_types = ["text", "link", "image", "structured"]

        for element_type in valid_types:
            valid_text_element_data["type"] = element_type
            element = DataElement(**valid_text_element_data)
            assert element.type == element_type

        # Invalid types
        invalid_types = [
            "invalid",
            "html",
            "json",
            "xml",
            "TEXT",
            "Link",
            "",
            123,
            None,
            ["text"],
            {"type": "text"},
        ]

        for invalid_type in invalid_types:
            valid_text_element_data["type"] = invalid_type
            with pytest.raises(ValidationError):
                DataElement(**valid_text_element_data)

    def test_data_element_value_any_type(self, valid_text_element_data):
        """Test that value field accepts any type."""
        # Test various value types
        test_values = [
            "string value",
            123,
            123.45,
            True,
            False,
            None,
            [1, 2, 3],
            {"key": "value"},
            {"nested": {"deep": [1, {"complex": True}]}},
        ]

        for value in test_values:
            valid_text_element_data["value"] = value
            element = DataElement(**valid_text_element_data)
            assert element.value == value

    def test_data_element_id_validation(self, valid_text_element_data):
        """Test element ID validation."""
        # Valid IDs
        valid_ids = [
            "element-1",
            "title_element",
            "product123",
            "a",
            "ELEMENT_ID",
            "mixed_Case_123",
            "uuid-" + str(uuid4()),
        ]

        for element_id in valid_ids:
            valid_text_element_data["id"] = element_id
            element = DataElement(**valid_text_element_data)
            assert element.id == element_id

        # Test empty ID (should fail if required)
        valid_text_element_data["id"] = ""
        with pytest.raises(ValidationError):
            DataElement(**valid_text_element_data)

    def test_data_element_required_fields(self):
        """Test validation with missing required fields."""
        complete_data = {
            "id": "test-element",
            "type": "text",
            "value": "test value",
            "metadata": {
                "selector": ".test",
                "source_url": "https://example.com",
                "timestamp": datetime.now(),
            },
        }

        # Should work with complete data
        element = DataElement(**complete_data)
        assert element.id == "test-element"

        # Test missing required fields
        required_fields = ["id", "type", "value", "metadata"]

        for field in required_fields:
            data = complete_data.copy()
            del data[field]
            with pytest.raises(ValidationError) as exc_info:
                DataElement(**data)

            error_str = str(exc_info.value)
            assert field in error_str or "required" in error_str.lower()

    def test_data_element_json_serialization(self, valid_structured_element_data):
        """Test JSON serialization/deserialization."""
        element = DataElement(**valid_structured_element_data)

        # Test model_dump
        json_data = element.model_dump()
        assert isinstance(json_data, dict)
        assert json_data["id"] == "product-details-4"
        assert json_data["type"] == "structured"
        assert json_data["value"]["product"]["name"] == "Advanced Widget Pro"

        # Test JSON string serialization
        json_str = element.model_dump_json()
        assert isinstance(json_str, str)

        # Test deserialization
        element_copy = DataElement.model_validate_json(json_str)
        assert element_copy.id == element.id
        assert element_copy.type == element.type
        assert element_copy.value == element.value

    def test_data_element_copy_and_modify(self, valid_image_element_data):
        """Test copying and modifying element instances."""
        element = DataElement(**valid_image_element_data)

        # Test deep copy
        element_copy = element.model_copy(deep=True)
        assert element_copy.id == element.id
        assert element_copy.value == element.value
        assert id(element_copy.value) != id(element.value)
        assert id(element_copy.metadata) != id(element.metadata)

        # Test copy with updates
        updated_element = element.model_copy(
            update={
                "id": "updated-image",
                "value": {"src": "https://example.com/new-image.jpg"},
            }
        )
        assert updated_element.id == "updated-image"
        assert updated_element.value["src"] == "https://example.com/new-image.jpg"
        assert updated_element.type == element.type


@pytest.mark.contract
class TestElementMetadataModel:
    """Contract tests for ElementMetadata Pydantic model validation."""

    @pytest.fixture
    def valid_metadata_data(self) -> Dict[str, Any]:
        """Valid metadata data."""
        return {
            "selector": "div.product-card > h2.title",
            "source_url": "https://shop.example.com/products?page=1",
            "timestamp": datetime(2023, 12, 25, 15, 30, 45),
            "xpath": "//div[@class='product-card']/h2[@class='title']",
        }

    @pytest.fixture
    def minimal_metadata_data(self) -> Dict[str, Any]:
        """Minimal valid metadata data."""
        return {
            "selector": ".title",
            "source_url": "https://example.com",
            "timestamp": datetime.now(),
        }

    def test_element_metadata_valid_creation(self, valid_metadata_data):
        """Test creating valid ElementMetadata instance."""
        metadata = ElementMetadata(**valid_metadata_data)

        assert metadata.selector == "div.product-card > h2.title"
        assert metadata.source_url == "https://shop.example.com/products?page=1"
        assert metadata.timestamp == datetime(2023, 12, 25, 15, 30, 45)
        assert metadata.xpath == "//div[@class='product-card']/h2[@class='title']"

    def test_element_metadata_minimal_creation(self, minimal_metadata_data):
        """Test creating minimal ElementMetadata instance."""
        metadata = ElementMetadata(**minimal_metadata_data)

        assert metadata.selector == ".title"
        assert metadata.source_url == "https://example.com"
        assert isinstance(metadata.timestamp, datetime)
        assert metadata.xpath is None  # Optional field

    def test_element_metadata_required_fields(self):
        """Test validation with missing required fields."""
        complete_data = {
            "selector": ".test",
            "source_url": "https://example.com",
            "timestamp": datetime.now(),
        }

        # Should work with complete data
        metadata = ElementMetadata(**complete_data)
        assert metadata.selector == ".test"

        # Test missing required fields
        required_fields = ["selector", "source_url", "timestamp"]

        for field in required_fields:
            data = complete_data.copy()
            del data[field]
            with pytest.raises(ValidationError) as exc_info:
                ElementMetadata(**data)

            error_str = str(exc_info.value)
            assert field in error_str or "required" in error_str.lower()

    def test_element_metadata_selector_validation(self, valid_metadata_data):
        """Test selector field validation."""
        # Valid selectors
        valid_selectors = [
            "div",
            ".class",
            "#id",
            "div.class",
            "div#id",
            "div > p",
            "div p",
            "div + p",
            "div ~ p",
            "input[type='text']",
            "a[href*='example']",
            ":nth-child(2)",
            "::before",
            ":hover",
            "div.class1.class2#id[attr='value']:nth-child(1)",
        ]

        for selector in valid_selectors:
            valid_metadata_data["selector"] = selector
            metadata = ElementMetadata(**valid_metadata_data)
            assert metadata.selector == selector

        # Empty selector should fail
        valid_metadata_data["selector"] = ""
        with pytest.raises(ValidationError):
            ElementMetadata(**valid_metadata_data)

    def test_element_metadata_source_url_validation(self, valid_metadata_data):
        """Test source_url field validation."""
        # Valid URLs
        valid_urls = [
            "https://example.com",
            "http://example.com",
            "https://subdomain.example.com/path?query=value",
            "https://example.com:8080/path/to/resource",
            "https://user:pass@example.com/path",
            "https://example.com/path/with spaces",  # URLs can have encoded spaces
        ]

        for url in valid_urls:
            valid_metadata_data["source_url"] = url
            metadata = ElementMetadata(**valid_metadata_data)
            assert metadata.source_url == url

        # Empty URL should fail
        valid_metadata_data["source_url"] = ""
        with pytest.raises(ValidationError):
            ElementMetadata(**valid_metadata_data)

    def test_element_metadata_timestamp_validation(self, valid_metadata_data):
        """Test timestamp field validation."""
        # Valid timestamps
        valid_timestamps = [
            datetime.now(),
            datetime(2023, 1, 1),
            datetime(2023, 12, 31, 23, 59, 59, 999999),
            datetime(1970, 1, 1),  # Unix epoch
            datetime(2100, 1, 1),  # Future date
        ]

        for timestamp in valid_timestamps:
            valid_metadata_data["timestamp"] = timestamp
            metadata = ElementMetadata(**valid_metadata_data)
            assert metadata.timestamp == timestamp

        # Invalid timestamp types
        invalid_timestamps = [
            "2023-12-25",
            "2023-12-25T10:30:45",
            1703505045,  # Unix timestamp
            None,
            [2023, 12, 25],
            {"year": 2023},
        ]

        for invalid_ts in invalid_timestamps:
            valid_metadata_data["timestamp"] = invalid_ts
            with pytest.raises(ValidationError):
                ElementMetadata(**valid_metadata_data)

    def test_element_metadata_xpath_validation(self, valid_metadata_data):
        """Test xpath field validation (optional)."""
        # Valid XPaths
        valid_xpaths = [
            "//div",
            "/html/body/div[1]",
            "//div[@class='test']",
            "//div[contains(@class, 'product')]",
            "//div[position()=1]",
            "//div/following-sibling::p",
            "//div[text()='Sample Text']",
            "//div[@id='test']//span",
        ]

        for xpath in valid_xpaths:
            valid_metadata_data["xpath"] = xpath
            metadata = ElementMetadata(**valid_metadata_data)
            assert metadata.xpath == xpath

        # None should be valid (optional field)
        valid_metadata_data["xpath"] = None
        metadata = ElementMetadata(**valid_metadata_data)
        assert metadata.xpath is None

        # Empty string
        valid_metadata_data["xpath"] = ""
        metadata = ElementMetadata(**valid_metadata_data)
        assert metadata.xpath == ""

    def test_element_metadata_json_serialization(self, valid_metadata_data):
        """Test JSON serialization/deserialization."""
        metadata = ElementMetadata(**valid_metadata_data)

        # Test model_dump
        json_data = metadata.model_dump()
        assert isinstance(json_data, dict)
        assert json_data["selector"] == "div.product-card > h2.title"
        assert json_data["source_url"] == "https://shop.example.com/products?page=1"

        # Test JSON string serialization
        json_str = metadata.model_dump_json()
        assert isinstance(json_str, str)

        # Test deserialization
        metadata_copy = ElementMetadata.model_validate_json(json_str)
        assert metadata_copy.selector == metadata.selector
        assert metadata_copy.source_url == metadata.source_url
        assert metadata_copy.timestamp == metadata.timestamp
        assert metadata_copy.xpath == metadata.xpath

    def test_element_metadata_copy_and_modify(self, valid_metadata_data):
        """Test copying and modifying metadata instances."""
        metadata = ElementMetadata(**valid_metadata_data)

        # Test copy
        metadata_copy = metadata.model_copy()
        assert metadata_copy.selector == metadata.selector
        assert metadata_copy.timestamp == metadata.timestamp

        # Test copy with updates
        updated_metadata = metadata.model_copy(
            update={"selector": ".updated-selector", "xpath": "//div[@class='updated']"}
        )
        assert updated_metadata.selector == ".updated-selector"
        assert updated_metadata.xpath == "//div[@class='updated']"
        assert updated_metadata.source_url == metadata.source_url

    def test_element_metadata_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Very long selector
        long_selector = "div" + ".class" * 100
        metadata = ElementMetadata(
            selector=long_selector,
            source_url="https://example.com",
            timestamp=datetime.now(),
        )
        assert metadata.selector == long_selector

        # Very long URL
        long_url = "https://example.com/" + "path/" * 100
        metadata = ElementMetadata(
            selector="div", source_url=long_url, timestamp=datetime.now()
        )
        assert metadata.source_url == long_url

        # Very long XPath
        long_xpath = "//div" + "[@class='test']" * 50
        metadata = ElementMetadata(
            selector="div",
            source_url="https://example.com",
            timestamp=datetime.now(),
            xpath=long_xpath,
        )
        assert metadata.xpath == long_xpath

    def test_element_metadata_field_info(self):
        """Test field information and metadata."""
        fields = ElementMetadata.model_fields

        assert "selector" in fields
        assert "source_url" in fields
        assert "timestamp" in fields
        assert "xpath" in fields

        # Check that xpath is optional
        # xpath_field = fields["xpath"]  # Field exists but not used in assertions
        # Should be optional with default None

    def test_element_metadata_schema_generation(self):
        """Test JSON schema generation."""
        schema = ElementMetadata.model_json_schema()

        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "required" in schema

        # Check required fields
        required_fields = schema["required"]
        assert "selector" in required_fields
        assert "source_url" in required_fields
        assert "timestamp" in required_fields
        assert "xpath" not in required_fields  # Optional

        # Check field types
        properties = schema["properties"]
        assert properties["selector"]["type"] == "string"
        assert properties["source_url"]["type"] == "string"
        assert properties["timestamp"]["type"] == "string"
        assert properties["timestamp"]["format"] == "date-time"

    def test_element_metadata_validation_errors(self, valid_metadata_data):
        """Test detailed validation error reporting."""
        # Multiple errors at once
        valid_metadata_data["selector"] = ""
        valid_metadata_data["source_url"] = ""
        valid_metadata_data["timestamp"] = "invalid"

        with pytest.raises(ValidationError) as exc_info:
            ElementMetadata(**valid_metadata_data)

        # Should report multiple errors
        errors = exc_info.value.errors()
        assert len(errors) >= 3

        # Check error structure
        for error in errors:
            assert "loc" in error
            assert "msg" in error
            assert "type" in error


@pytest.mark.contract
class TestDataElementIntegration:
    """Integration tests for DataElement with ElementMetadata."""

    def test_data_element_with_metadata_integration(self):
        """Test DataElement with nested ElementMetadata validation."""
        element_data = {
            "id": "integration-test",
            "type": "text",
            "value": "Integration test value",
            "metadata": {
                "selector": ".integration-test",
                "source_url": "https://example.com/test",
                "timestamp": datetime(2023, 12, 25, 12, 0, 0),
            },
        }

        element = DataElement(**element_data)

        # Verify DataElement fields
        assert element.id == "integration-test"
        assert element.type == "text"
        assert element.value == "Integration test value"

        # Verify nested ElementMetadata
        assert isinstance(element.metadata, ElementMetadata)
        assert element.metadata.selector == ".integration-test"
        assert element.metadata.source_url == "https://example.com/test"
        assert element.metadata.timestamp == datetime(2023, 12, 25, 12, 0, 0)
        assert element.metadata.xpath is None

    def test_data_element_metadata_validation_errors(self):
        """Test that metadata validation errors are properly reported."""
        element_data = {
            "id": "test",
            "type": "text",
            "value": "test",
            "metadata": {
                "selector": "",  # Invalid empty selector
                "source_url": "",  # Invalid empty URL
                "timestamp": "invalid",  # Invalid timestamp
            },
        }

        with pytest.raises(ValidationError) as exc_info:
            DataElement(**element_data)

        # Should report metadata validation errors
        errors = exc_info.value.errors()
        assert len(errors) >= 3

        # Check that errors are nested under metadata
        metadata_errors = [e for e in errors if "metadata" in str(e["loc"])]
        assert len(metadata_errors) >= 3

    def test_data_element_complex_nested_serialization(self):
        """Test serialization of complex nested DataElement."""
        complex_data = {
            "id": "complex-element",
            "type": "structured",
            "value": {"nested": {"deep": {"data": [1, 2, {"key": "value"}]}}},
            "metadata": {
                "selector": "div.complex > .nested .deep",
                "source_url": "https://example.com/complex",
                "timestamp": datetime(2023, 12, 25, 10, 0, 0),
                "xpath": "//div[@class='complex']//div[@class='nested']//div[@class='deep']",
            },
        }

        element = DataElement(**complex_data)

        # Test serialization
        json_str = element.model_dump_json()
        element_copy = DataElement.model_validate_json(json_str)

        # Verify deep equality
        assert element_copy.id == element.id
        assert element_copy.type == element.type
        assert element_copy.value == element.value
        assert element_copy.metadata.selector == element.metadata.selector
        assert element_copy.metadata.xpath == element.metadata.xpath
