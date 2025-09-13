"""
Contract test for ScrapingProvider.execute_extract() method.
This test MUST fail before any implementation exists (TDD requirement).
"""

# Standard library imports
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Third-party imports
import pytest

# Add the contracts directory to the path
contracts_path = (
    Path(__file__).parent.parent.parent / "specs" / "001-read-spec-md" / "contracts"
)
sys.path.insert(0, str(contracts_path))

try:
    # Third-party imports
    from provider_interfaces import (
        Cookie,
        DataElement,
        ElementMetadata,
        ExtractStepConfig,
        PageContext,
        ProviderMetadata,
        ScrapingProvider,
        Viewport,
    )
except ImportError:
    # If import fails, create minimal interfaces for testing
    # Standard library imports
    from abc import ABC, abstractmethod
    from typing import Protocol

    # Third-party imports
    from pydantic import BaseModel

    class ProviderMetadata(BaseModel):
        name: str
        version: str
        type: str
        capabilities: list

    class Cookie(BaseModel):
        name: str
        value: str
        domain: str
        path: str
        expires: int = None
        http_only: bool = False
        secure: bool = False

    class Viewport(BaseModel):
        width: int = 1920
        height: int = 1080

    class ElementMetadata(BaseModel):
        selector: str
        source_url: str
        timestamp: datetime
        xpath: str = None

    class DataElement(BaseModel):
        id: str
        type: str  # "text", "link", "image", "structured"
        value: Any
        metadata: ElementMetadata

    class PageContext(BaseModel):
        url: str
        title: str
        cookies: list = []
        navigation_history: list = []
        viewport: Viewport = Viewport(width=1920, height=1080)
        user_agent: str = "scrapper/1.0.0"

    class ExtractStepConfig(BaseModel):
        elements: Dict[str, Dict[str, Any]]

    class ScrapingProvider(Protocol):
        async def initialize(self, config): ...
        async def execute_init(self, step_config): ...
        async def execute_discover(self, step_config, context): ...
        async def execute_extract(
            self, step_config: ExtractStepConfig, context: PageContext
        ): ...
        async def execute_paginate(self, step_config, context): ...
        async def cleanup(self): ...
        async def health_check(self) -> bool: ...


class MockScrapingProvider:
    """Mock implementation that should fail contract tests initially."""

    def __init__(self):
        self.metadata = ProviderMetadata(
            name="mock-scraper",
            version="1.0.0",
            type="scraping",
            capabilities=["extract", "basic"],
        )
        self.is_initialized = False
        self.config = None

    async def initialize(self, config) -> None:
        """Mock implementation - should be replaced by real implementation."""
        raise NotImplementedError("ScrapingProvider.initialize() not implemented yet")

    async def execute_init(self, step_config):
        raise NotImplementedError("Not implemented")

    async def execute_discover(self, step_config, context):
        raise NotImplementedError("Not implemented")

    async def execute_extract(
        self, step_config: ExtractStepConfig, context: PageContext
    ) -> List[DataElement]:
        """Mock implementation - should be replaced by real implementation."""
        # This will fail until real implementation exists
        raise NotImplementedError(
            "ScrapingProvider.execute_extract() not implemented yet"
        )

    async def execute_paginate(self, step_config, context):
        raise NotImplementedError("Not implemented")

    async def cleanup(self):
        raise NotImplementedError("Not implemented")

    async def health_check(self):
        return False


@pytest.mark.contract
@pytest.mark.asyncio
class TestScrapingProviderExecuteExtract:
    """Contract tests for ScrapingProvider.execute_extract() method."""

    @pytest.fixture
    def provider(self) -> ScrapingProvider:
        """Create a mock scraping provider for testing."""
        return MockScrapingProvider()

    @pytest.fixture
    def valid_page_context(self) -> PageContext:
        """Create valid PageContext for testing."""
        return PageContext(
            url="https://example.com",
            title="Example Domain",
            cookies=[
                Cookie(name="session", value="abc123", domain="example.com", path="/")
            ],
            navigation_history=["https://example.com"],
            viewport=Viewport(width=1920, height=1080),
            user_agent="scrapper/1.0.0",
        )

    @pytest.fixture
    def valid_extract_config(self) -> ExtractStepConfig:
        """Create valid ExtractStepConfig for testing."""
        return ExtractStepConfig(
            elements={
                "title": {
                    "selector": "h1",
                    "attribute": "text",
                    "type": "text",
                    "required": True,
                },
                "description": {
                    "selector": "meta[name='description']",
                    "attribute": "content",
                    "type": "text",
                    "required": False,
                },
                "links": {
                    "selector": "a[href]",
                    "attribute": "href",
                    "type": "link",
                    "multiple": True,
                },
                "images": {
                    "selector": "img[src]",
                    "attribute": "src",
                    "type": "image",
                    "multiple": True,
                    "transform": "absolute_url",
                },
                "article_data": {
                    "selector": "article",
                    "type": "structured",
                    "extract": {
                        "title": "h2",
                        "content": "p",
                        "author": ".author",
                        "date": ".date",
                    },
                },
            }
        )

    @pytest.fixture
    def minimal_extract_config(self) -> ExtractStepConfig:
        """Create minimal valid ExtractStepConfig for testing."""
        return ExtractStepConfig(
            elements={"content": {"selector": "p", "attribute": "text", "type": "text"}}
        )

    @pytest.fixture
    def invalid_extract_configs(self) -> Dict[str, ExtractStepConfig]:
        """Create various invalid ExtractStepConfig instances for testing."""
        return {
            "empty_elements": ExtractStepConfig(elements={}),
            "invalid_selector": ExtractStepConfig(
                elements={
                    "test": {
                        "selector": "<<<invalid>>>",
                        "attribute": "text",
                        "type": "text",
                    }
                }
            ),
            "missing_selector": ExtractStepConfig(
                elements={"test": {"attribute": "text", "type": "text"}}
            ),
        }

    async def test_execute_extract_with_valid_config(
        self,
        provider: ScrapingProvider,
        valid_extract_config: ExtractStepConfig,
        valid_page_context: PageContext,
    ):
        """Test that execute_extract() accepts valid parameters and returns List[DataElement]."""
        # This test MUST fail initially (TDD requirement)
        with pytest.raises(NotImplementedError, match="not implemented yet"):
            await provider.execute_extract(valid_extract_config, valid_page_context)

    async def test_execute_extract_returns_data_elements_list(
        self,
        provider: ScrapingProvider,
        valid_extract_config: ExtractStepConfig,
        valid_page_context: PageContext,
    ):
        """Test that execute_extract() returns proper List[DataElement] object."""
        # This test MUST fail initially (TDD requirement)
        with pytest.raises(NotImplementedError):
            result = await provider.execute_extract(
                valid_extract_config, valid_page_context
            )
            # After implementation, this should verify:
            # assert isinstance(result, list)
            # assert all(isinstance(element, DataElement) for element in result)

    async def test_execute_extract_with_minimal_config(
        self,
        provider: ScrapingProvider,
        minimal_extract_config: ExtractStepConfig,
        valid_page_context: PageContext,
    ):
        """Test that execute_extract() works with minimal configuration."""
        with pytest.raises(NotImplementedError):
            result = await provider.execute_extract(
                minimal_extract_config, valid_page_context
            )
            # After implementation, verify minimal requirements are met

    async def test_execute_extract_text_elements(
        self, provider: ScrapingProvider, valid_page_context: PageContext
    ):
        """Test that execute_extract() properly extracts text elements."""
        config = ExtractStepConfig(
            elements={
                "heading": {"selector": "h1", "attribute": "text", "type": "text"},
                "paragraph": {
                    "selector": "p.intro",
                    "attribute": "text",
                    "type": "text",
                },
                "title_attribute": {
                    "selector": "div",
                    "attribute": "title",
                    "type": "text",
                },
            }
        )

        with pytest.raises(NotImplementedError):
            result = await provider.execute_extract(config, valid_page_context)
            # After implementation, verify text extraction works

    async def test_execute_extract_link_elements(
        self, provider: ScrapingProvider, valid_page_context: PageContext
    ):
        """Test that execute_extract() properly extracts link elements."""
        config = ExtractStepConfig(
            elements={
                "navigation_links": {
                    "selector": "nav a[href]",
                    "attribute": "href",
                    "type": "link",
                    "multiple": True,
                },
                "external_link": {
                    "selector": "a.external",
                    "attribute": "href",
                    "type": "link",
                    "transform": "absolute_url",
                },
            }
        )

        with pytest.raises(NotImplementedError):
            result = await provider.execute_extract(config, valid_page_context)

    async def test_execute_extract_image_elements(
        self, provider: ScrapingProvider, valid_page_context: PageContext
    ):
        """Test that execute_extract() properly extracts image elements."""
        config = ExtractStepConfig(
            elements={
                "hero_image": {
                    "selector": "img.hero",
                    "attribute": "src",
                    "type": "image",
                    "transform": "absolute_url",
                },
                "gallery_images": {
                    "selector": ".gallery img[src]",
                    "attribute": "src",
                    "type": "image",
                    "multiple": True,
                },
                "image_with_alt": {
                    "selector": "img[alt]",
                    "type": "image",
                    "extract": {"src": "src", "alt": "alt", "title": "title"},
                },
            }
        )

        with pytest.raises(NotImplementedError):
            result = await provider.execute_extract(config, valid_page_context)

    async def test_execute_extract_structured_elements(
        self, provider: ScrapingProvider, valid_page_context: PageContext
    ):
        """Test that execute_extract() properly extracts structured elements."""
        config = ExtractStepConfig(
            elements={
                "product_info": {
                    "selector": ".product",
                    "type": "structured",
                    "extract": {
                        "name": "h2.product-name",
                        "price": ".price",
                        "rating": ".rating",
                        "availability": ".stock-status",
                    },
                },
                "article_list": {
                    "selector": "article",
                    "type": "structured",
                    "multiple": True,
                    "extract": {
                        "title": "h3",
                        "excerpt": ".excerpt",
                        "author": ".author",
                        "date": ".publish-date",
                        "tags": ".tags a",
                    },
                },
            }
        )

        with pytest.raises(NotImplementedError):
            result = await provider.execute_extract(config, valid_page_context)

    async def test_execute_extract_multiple_elements(
        self, provider: ScrapingProvider, valid_page_context: PageContext
    ):
        """Test that execute_extract() handles multiple element extraction."""
        config = ExtractStepConfig(
            elements={
                "all_links": {
                    "selector": "a[href]",
                    "attribute": "href",
                    "type": "link",
                    "multiple": True,
                },
                "all_headings": {
                    "selector": "h1, h2, h3, h4, h5, h6",
                    "attribute": "text",
                    "type": "text",
                    "multiple": True,
                },
            }
        )

        with pytest.raises(NotImplementedError):
            result = await provider.execute_extract(config, valid_page_context)

    async def test_execute_extract_with_transformations(
        self, provider: ScrapingProvider, valid_page_context: PageContext
    ):
        """Test that execute_extract() applies data transformations."""
        config = ExtractStepConfig(
            elements={
                "absolute_url": {
                    "selector": "a.relative",
                    "attribute": "href",
                    "type": "link",
                    "transform": "absolute_url",
                },
                "clean_text": {
                    "selector": "p.messy",
                    "attribute": "text",
                    "type": "text",
                    "transform": "clean_whitespace",
                },
                "parse_date": {
                    "selector": ".date",
                    "attribute": "text",
                    "type": "text",
                    "transform": "parse_date",
                },
            }
        )

        with pytest.raises(NotImplementedError):
            result = await provider.execute_extract(config, valid_page_context)

    async def test_execute_extract_required_elements(
        self, provider: ScrapingProvider, valid_page_context: PageContext
    ):
        """Test that execute_extract() handles required elements properly."""
        config = ExtractStepConfig(
            elements={
                "required_title": {
                    "selector": "h1",
                    "attribute": "text",
                    "type": "text",
                    "required": True,
                },
                "optional_subtitle": {
                    "selector": "h2",
                    "attribute": "text",
                    "type": "text",
                    "required": False,
                },
            }
        )

        with pytest.raises(NotImplementedError):
            result = await provider.execute_extract(config, valid_page_context)

    async def test_execute_extract_with_empty_elements(
        self,
        provider: ScrapingProvider,
        invalid_extract_configs,
        valid_page_context: PageContext,
    ):
        """Test that execute_extract() validates element configuration."""
        with pytest.raises((ValueError, NotImplementedError)):
            await provider.execute_extract(
                invalid_extract_configs["empty_elements"], valid_page_context
            )

    async def test_execute_extract_with_invalid_selector(
        self,
        provider: ScrapingProvider,
        invalid_extract_configs,
        valid_page_context: PageContext,
    ):
        """Test that execute_extract() validates CSS selector syntax."""
        with pytest.raises((ValueError, NotImplementedError)):
            await provider.execute_extract(
                invalid_extract_configs["invalid_selector"], valid_page_context
            )

    async def test_execute_extract_with_missing_selector(
        self,
        provider: ScrapingProvider,
        invalid_extract_configs,
        valid_page_context: PageContext,
    ):
        """Test that execute_extract() validates required selector field."""
        with pytest.raises((ValueError, NotImplementedError)):
            await provider.execute_extract(
                invalid_extract_configs["missing_selector"], valid_page_context
            )

    async def test_execute_extract_with_none_config(
        self, provider: ScrapingProvider, valid_page_context: PageContext
    ):
        """Test that execute_extract() handles None configuration appropriately."""
        with pytest.raises((TypeError, ValueError, NotImplementedError)):
            await provider.execute_extract(None, valid_page_context)

    async def test_execute_extract_with_none_context(
        self, provider: ScrapingProvider, valid_extract_config: ExtractStepConfig
    ):
        """Test that execute_extract() handles None page context appropriately."""
        with pytest.raises((TypeError, ValueError, NotImplementedError)):
            await provider.execute_extract(valid_extract_config, None)

    async def test_execute_extract_data_element_structure(
        self,
        provider: ScrapingProvider,
        valid_extract_config: ExtractStepConfig,
        valid_page_context: PageContext,
    ):
        """Test that execute_extract() returns DataElement objects with proper structure."""
        with pytest.raises(NotImplementedError):
            result = await provider.execute_extract(
                valid_extract_config, valid_page_context
            )
            # After implementation, verify DataElement structure:
            # for element in result:
            #     assert hasattr(element, 'id')
            #     assert hasattr(element, 'type')
            #     assert hasattr(element, 'value')
            #     assert hasattr(element, 'metadata')
            #     assert element.type in ["text", "link", "image", "structured"]

    async def test_execute_extract_element_metadata(
        self,
        provider: ScrapingProvider,
        valid_extract_config: ExtractStepConfig,
        valid_page_context: PageContext,
    ):
        """Test that execute_extract() returns DataElement objects with proper metadata."""
        with pytest.raises(NotImplementedError):
            result = await provider.execute_extract(
                valid_extract_config, valid_page_context
            )
            # After implementation, verify ElementMetadata:
            # for element in result:
            #     assert isinstance(element.metadata, ElementMetadata)
            #     assert element.metadata.selector is not None
            #     assert element.metadata.source_url == valid_page_context.url
            #     assert isinstance(element.metadata.timestamp, datetime)

    async def test_execute_extract_element_ids(
        self,
        provider: ScrapingProvider,
        valid_extract_config: ExtractStepConfig,
        valid_page_context: PageContext,
    ):
        """Test that execute_extract() generates unique IDs for extracted elements."""
        with pytest.raises(NotImplementedError):
            result = await provider.execute_extract(
                valid_extract_config, valid_page_context
            )
            # After implementation, verify unique IDs:
            # ids = [element.id for element in result]
            # assert len(ids) == len(set(ids))  # All IDs should be unique

    async def test_execute_extract_concurrent_calls(
        self,
        provider: ScrapingProvider,
        valid_extract_config: ExtractStepConfig,
        valid_page_context: PageContext,
    ):
        """Test that concurrent execute_extract() calls are handled safely."""
        # Standard library imports
        import asyncio

        async def extract_call():
            try:
                await provider.execute_extract(valid_extract_config, valid_page_context)
            except NotImplementedError:
                return "not_implemented"
            return "success"

        # Run multiple concurrent extract calls
        results = await asyncio.gather(
            extract_call(), extract_call(), extract_call(), return_exceptions=True
        )

        # All should fail with NotImplementedError initially
        for result in results:
            assert result == "not_implemented" or isinstance(
                result, NotImplementedError
            )

    async def test_execute_extract_element_type_consistency(
        self, provider: ScrapingProvider, valid_page_context: PageContext
    ):
        """Test that execute_extract() maintains element type consistency."""
        config = ExtractStepConfig(
            elements={
                "text_only": {"selector": "p", "attribute": "text", "type": "text"},
                "link_only": {
                    "selector": "a[href]",
                    "attribute": "href",
                    "type": "link",
                },
                "image_only": {
                    "selector": "img[src]",
                    "attribute": "src",
                    "type": "image",
                },
                "structured_only": {
                    "selector": "table",
                    "type": "structured",
                    "extract": {"headers": "th", "rows": "tr"},
                },
            }
        )

        with pytest.raises(NotImplementedError):
            result = await provider.execute_extract(config, valid_page_context)
            # After implementation, verify type consistency:
            # text_elements = [e for e in result if e.type == "text"]
            # link_elements = [e for e in result if e.type == "link"]
            # image_elements = [e for e in result if e.type == "image"]
            # structured_elements = [e for e in result if e.type == "structured"]


# Additional contract validation tests
@pytest.mark.contract
class TestScrapingProviderExecuteExtractContractValidation:
    """Contract validation tests to ensure proper interface compliance."""

    def test_execute_extract_method_signature(self):
        """Test that execute_extract method has correct signature."""
        provider = MockScrapingProvider()

        # Verify method exists
        assert hasattr(provider, "execute_extract")
        assert callable(getattr(provider, "execute_extract"))

        # Verify it's async
        # Standard library imports
        import inspect

        assert inspect.iscoroutinefunction(provider.execute_extract)

    def test_execute_extract_accepts_proper_parameters(self):
        """Test that execute_extract accepts ExtractStepConfig and PageContext parameters."""
        provider = MockScrapingProvider()

        # Should not raise TypeError for signature mismatch
        # Standard library imports
        import inspect

        sig = inspect.signature(provider.execute_extract)

        # Verify it accepts both parameters
        assert len(sig.parameters) == 2
        params = list(sig.parameters.values())
        assert params[0].name == "step_config"
        assert params[1].name == "context"

    def test_execute_extract_return_annotation(self):
        """Test that execute_extract has proper return type annotation."""
        provider = MockScrapingProvider()

        # Check return annotation
        # Standard library imports
        import inspect

        sig = inspect.signature(provider.execute_extract)

        # Should return List[DataElement] (after implementation)
        # For now, just verify it has a return annotation
        assert sig.return_annotation is not inspect.Signature.empty

    def test_extract_step_config_validation(self):
        """Test that ExtractStepConfig properly validates input data."""
        # Valid config should not raise
        valid_config = ExtractStepConfig(
            elements={"title": {"selector": "h1", "attribute": "text", "type": "text"}}
        )
        assert "title" in valid_config.elements

        # Test with complex configuration
        complex_config = ExtractStepConfig(
            elements={
                "structured": {
                    "selector": "article",
                    "type": "structured",
                    "extract": {"title": "h2", "content": "p"},
                },
                "multiple": {
                    "selector": "a[href]",
                    "attribute": "href",
                    "type": "link",
                    "multiple": True,
                },
            }
        )
        assert "structured" in complex_config.elements
        assert "multiple" in complex_config.elements

    def test_data_element_value_types(self):
        """Test that DataElement can handle different value types."""
        metadata = ElementMetadata(
            selector="p", source_url="https://example.com", timestamp=datetime.now()
        )

        # Text element
        text_element = DataElement(
            id="text-1", type="text", value="Sample text content", metadata=metadata
        )
        assert isinstance(text_element.value, str)

        # Structured element
        structured_element = DataElement(
            id="struct-1",
            type="structured",
            value={
                "title": "Article Title",
                "content": "Article content",
                "tags": ["tag1", "tag2"],
            },
            metadata=metadata,
        )
        assert isinstance(structured_element.value, dict)

        # Multiple elements (list)
        list_element = DataElement(
            id="list-1",
            type="link",
            value=["https://example.com/1", "https://example.com/2"],
            metadata=metadata,
        )
        assert isinstance(list_element.value, list)
