"""
Unit tests for model imports and basic validation.
These tests ensure all Pydantic models can be imported and instantiated.
"""

import pytest
from datetime import datetime
from src.scraper_core.models import (
    Workflow,
    WorkflowMetadata,
    WorkflowStep,
    DataElement,
    ElementMetadata,
    PageContext,
    Viewport,
    ScrapedItem,
    BatchInsertResult,
    StorageStats,
    StorageHealthCheck,
    ScrapyConfig,
    PlaywrightConfig,
    BeautifulSoupConfig,
    CSVStorageConfig,
    PostgreSQLStorageConfig,
    MongoDBStorageConfig,
    SQLiteStorageConfig,
)


class TestModelImports:
    """Test that all models can be imported and basic instances created."""

    def test_workflow_model_import(self):
        """Test Workflow model can be imported and basic validation works."""
        assert Workflow is not None

        # Test basic model instantiation works
        metadata = WorkflowMetadata(
            name="Test Workflow",
            description="Test description",
            author="test-author",
            target_site="https://example.com"
        )
        assert metadata.name == "Test Workflow"

    def test_data_element_model_import(self):
        """Test DataElement model can be imported and basic validation works."""
        assert DataElement is not None

        # Test basic model instantiation works
        metadata = ElementMetadata(
            selector="h1",
            source_url="https://example.com",
            timestamp=datetime.now()
        )
        element = DataElement(
            id="test-1",
            type="text",
            value="Sample text",
            metadata=metadata
        )
        assert element.id == "test-1"

    def test_page_context_model_import(self):
        """Test PageContext model can be imported and basic validation works."""
        assert PageContext is not None

        # Test basic model instantiation works
        viewport = Viewport(width=1920, height=1080)
        context = PageContext(
            url="https://example.com",
            title="Test Page",
            viewport=viewport
        )
        assert context.url == "https://example.com"

    def test_storage_models_import(self):
        """Test storage models can be imported and basic validation works."""
        assert ScrapedItem is not None
        assert BatchInsertResult is not None
        assert StorageStats is not None
        assert StorageHealthCheck is not None

        # Test basic model instantiation works
        item = ScrapedItem(
            id="test-item",
            source_url="https://example.com",
            data={"title": "Test Title", "price": 99.99}
        )
        assert item.id == "test-item"

    def test_provider_config_models_import(self):
        """Test provider config models can be imported and basic validation works."""
        assert ScrapyConfig is not None
        assert PlaywrightConfig is not None
        assert BeautifulSoupConfig is not None
        assert CSVStorageConfig is not None
        assert PostgreSQLStorageConfig is not None
        assert MongoDBStorageConfig is not None
        assert SQLiteStorageConfig is not None

        # Test basic model instantiation works
        scrapy_config = ScrapyConfig(concurrent_requests=8)
        assert scrapy_config.concurrent_requests == 8

    @pytest.mark.slow
    def test_workflow_step_model_import(self):
        """Test WorkflowStep model can be imported and basic validation works."""
        assert WorkflowStep is not None

        # Test basic model instantiation works
        step = WorkflowStep(
            id="test-step",
            command="init",
            config={"url": "https://example.com"}
        )
        assert step.id == "test-step"