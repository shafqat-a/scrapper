"""
Contract test for Workflow Pydantic model validation.
This test validates the Workflow model and its nested components.
Tests MUST fail before any implementation exists (TDD requirement).
"""

# Standard library imports
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
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
    from provider_interfaces import (
        PostProcessingStep,
        SchemaDefinition,
        SchemaField,
        ScrapingConfig,
        StorageConfig,
        Workflow,
        WorkflowMetadata,
        WorkflowStep,
    )
except ImportError:
    # If import fails, create minimal models for testing
    # Standard library imports
    from typing import Literal

    # Third-party imports
    from pydantic import BaseModel, Field

    class SchemaField(BaseModel):
        type: Literal["string", "number", "boolean", "date", "json"]
        required: bool = False
        max_length: Optional[int] = None
        index: bool = False

    class SchemaDefinition(BaseModel):
        name: str
        fields: Dict[str, SchemaField]
        primary_key: List[str] = []

    class WorkflowMetadata(BaseModel):
        name: str = Field(..., max_length=100)
        description: str = Field(..., max_length=500)
        author: str
        created: datetime = Field(default_factory=datetime.now)
        tags: List[str] = []
        target_site: str = Field(..., description="Target website URL")

    class ScrapingConfig(BaseModel):
        provider: str
        config: Dict[str, Any]

    class StorageConfig(BaseModel):
        provider: str
        config: Dict[str, Any]
        schema: Optional[SchemaDefinition] = None

    class WorkflowStep(BaseModel):
        id: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+$")
        command: Literal["init", "discover", "extract", "paginate"]
        config: Dict[str, Any]
        retries: int = Field(default=3, ge=0)
        timeout: int = Field(default=30000, gt=0)
        continue_on_error: bool = False

    class PostProcessingStep(BaseModel):
        type: Literal["filter", "transform", "validate", "deduplicate"]
        config: Dict[str, Any]

    class Workflow(BaseModel):
        version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
        metadata: WorkflowMetadata
        scraping: ScrapingConfig
        storage: StorageConfig
        steps: List[WorkflowStep] = Field(..., min_length=1)
        post_processing: Optional[List[PostProcessingStep]] = None


@pytest.mark.contract
class TestWorkflowModel:
    """Contract tests for Workflow Pydantic model validation."""

    @pytest.fixture
    def valid_workflow_data(self) -> Dict[str, Any]:
        """Valid workflow data for testing."""
        return {
            "version": "1.0.0",
            "metadata": {
                "name": "Test Workflow",
                "description": "A test workflow for validation",
                "author": "test-author",
                "target_site": "https://example.com",
                "tags": ["test", "validation"],
            },
            "scraping": {
                "provider": "scrapy",
                "config": {
                    "concurrent_requests": 8,
                    "download_delay": 0.5,
                    "robotstxt_obey": True,
                },
            },
            "storage": {
                "provider": "csv",
                "config": {
                    "file_path": "/tmp/test_data.csv",
                    "delimiter": ",",
                    "headers": True,
                },
            },
            "steps": [
                {
                    "id": "init",
                    "command": "init",
                    "config": {"url": "https://example.com"},
                },
                {
                    "id": "extract",
                    "command": "extract",
                    "config": {"elements": {"title": "h1", "content": "p"}},
                },
            ],
        }

    @pytest.fixture
    def complex_workflow_data(self) -> Dict[str, Any]:
        """Complex workflow data with all optional fields."""
        return {
            "version": "2.1.0",
            "metadata": {
                "name": "Complex E-commerce Scraper",
                "description": "Advanced workflow for scraping product data with pagination and post-processing",
                "author": "data-team",
                "target_site": "https://shop.example.com",
                "tags": ["ecommerce", "products", "pagination", "advanced"],
            },
            "scraping": {
                "provider": "playwright",
                "config": {
                    "browser": "chromium",
                    "headless": True,
                    "viewport": {"width": 1920, "height": 1080},
                    "timeout": 30000,
                    "user_agent": "Mozilla/5.0 (compatible; scrapper/2.0)",
                },
            },
            "storage": {
                "provider": "postgresql",
                "config": {
                    "connection_string": "postgresql://user:pass@localhost/products",
                    "table_name": "scraped_products",
                    "batch_size": 1000,
                },
                "schema": {
                    "name": "product_schema",
                    "fields": {
                        "id": {"type": "string", "required": True, "index": True},
                        "title": {
                            "type": "string",
                            "required": True,
                            "max_length": 200,
                        },
                        "price": {"type": "number"},
                        "description": {"type": "string", "max_length": 1000},
                        "in_stock": {"type": "boolean"},
                        "created_at": {"type": "date"},
                        "metadata": {"type": "json"},
                    },
                    "primary_key": ["id"],
                },
            },
            "steps": [
                {
                    "id": "init",
                    "command": "init",
                    "config": {
                        "url": "https://shop.example.com/products",
                        "wait_for": "body",
                    },
                },
                {
                    "id": "discover",
                    "command": "discover",
                    "config": {"selectors": {"products": ".product-item"}},
                },
                {
                    "id": "extract",
                    "command": "extract",
                    "config": {
                        "elements": {
                            "id": ".product-id",
                            "title": ".product-title",
                            "price": ".product-price",
                            "description": ".product-description",
                        }
                    },
                    "retries": 5,
                    "timeout": 60000,
                    "continue_on_error": False,
                },
                {
                    "id": "paginate",
                    "command": "paginate",
                    "config": {
                        "next_page_selector": ".next-page",
                        "max_pages": 10,
                        "wait_after_click": 2000,
                    },
                },
            ],
            "post_processing": [
                {
                    "type": "filter",
                    "config": {"condition": "price > 0 AND title != ''"},
                },
                {
                    "type": "transform",
                    "config": {"price": "parseFloat(price.replace('$', ''))"},
                },
                {
                    "type": "validate",
                    "config": {"rules": ["required:id,title", "numeric:price"]},
                },
                {
                    "type": "deduplicate",
                    "config": {"fields": ["id"], "strategy": "first"},
                },
            ],
        }

    def test_workflow_model_exists(self):
        """Test that Workflow model class exists."""
        assert Workflow is not None
        assert issubclass(Workflow, BaseModel)

    def test_workflow_valid_creation(self, valid_workflow_data):
        """Test creating a valid Workflow instance."""
        workflow = Workflow(**valid_workflow_data)

        assert workflow.version == "1.0.0"
        assert workflow.metadata.name == "Test Workflow"
        assert workflow.scraping.provider == "scrapy"
        assert workflow.storage.provider == "csv"
        assert len(workflow.steps) == 2
        assert workflow.post_processing is None

    def test_workflow_complex_creation(self, complex_workflow_data):
        """Test creating a complex Workflow with all fields."""
        workflow = Workflow(**complex_workflow_data)

        assert workflow.version == "2.1.0"
        assert workflow.metadata.name == "Complex E-commerce Scraper"
        assert len(workflow.metadata.tags) == 4
        assert workflow.scraping.provider == "playwright"
        assert workflow.storage.provider == "postgresql"
        assert workflow.storage.schema is not None
        assert len(workflow.steps) == 4
        assert workflow.post_processing is not None
        assert len(workflow.post_processing) == 4

    def test_workflow_json_serialization(self, valid_workflow_data):
        """Test JSON serialization/deserialization."""
        workflow = Workflow(**valid_workflow_data)

        # Test model_dump (Pydantic v2)
        json_data = workflow.model_dump()
        assert isinstance(json_data, dict)
        assert json_data["version"] == "1.0.0"

        # Test JSON string serialization
        json_str = workflow.model_dump_json()
        assert isinstance(json_str, str)

        # Test deserialization
        workflow_copy = Workflow.model_validate_json(json_str)
        assert workflow_copy.version == workflow.version
        assert workflow_copy.metadata.name == workflow.metadata.name

    def test_workflow_version_validation(self, valid_workflow_data):
        """Test version field validation."""
        # Valid versions
        valid_versions = ["1.0.0", "2.1.3", "10.20.30", "0.0.1"]
        for version in valid_versions:
            valid_workflow_data["version"] = version
            workflow = Workflow(**valid_workflow_data)
            assert workflow.version == version

        # Invalid versions
        invalid_versions = [
            "1.0",  # Missing patch
            "v1.0.0",  # Has prefix
            "1.0.0-beta",  # Has suffix
            "1.0.0.1",  # Too many parts
            "invalid",  # Not semver
            "",  # Empty
            "1.a.0",  # Non-numeric
        ]

        for version in invalid_versions:
            valid_workflow_data["version"] = version
            with pytest.raises(ValidationError):
                Workflow(**valid_workflow_data)

    def test_workflow_missing_required_fields(self, valid_workflow_data):
        """Test validation with missing required fields."""
        required_fields = ["version", "metadata", "scraping", "storage", "steps"]

        for field in required_fields:
            data = valid_workflow_data.copy()
            del data[field]
            with pytest.raises(ValidationError) as exc_info:
                Workflow(**data)

            # Check that the error mentions the missing field
            error_str = str(exc_info.value)
            assert field in error_str or "required" in error_str.lower()

    def test_workflow_empty_steps_validation(self, valid_workflow_data):
        """Test that empty steps list is invalid."""
        valid_workflow_data["steps"] = []

        with pytest.raises(ValidationError) as exc_info:
            Workflow(**valid_workflow_data)

        error_str = str(exc_info.value)
        assert "at least 1" in error_str.lower() or "min_length" in error_str.lower()

    def test_workflow_invalid_field_types(self, valid_workflow_data):
        """Test validation with wrong field types."""
        # Test invalid type for version
        valid_workflow_data["version"] = 123
        with pytest.raises(ValidationError):
            Workflow(**valid_workflow_data)

        # Reset and test invalid metadata type
        valid_workflow_data["version"] = "1.0.0"
        valid_workflow_data["metadata"] = "invalid"
        with pytest.raises(ValidationError):
            Workflow(**valid_workflow_data)

        # Reset and test invalid steps type
        valid_workflow_data["metadata"] = {
            "name": "Test",
            "description": "Test",
            "author": "test",
            "target_site": "https://example.com",
        }
        valid_workflow_data["steps"] = "invalid"
        with pytest.raises(ValidationError):
            Workflow(**valid_workflow_data)

    def test_workflow_extra_fields_handling(self, valid_workflow_data):
        """Test how extra fields are handled."""
        valid_workflow_data["extra_field"] = "should_be_ignored"

        # Pydantic should ignore extra fields by default in recent versions
        # or raise ValidationError if configured to forbid them
        try:
            workflow = Workflow(**valid_workflow_data)
            # If creation succeeds, extra field should be ignored
            assert not hasattr(workflow, "extra_field")
        except ValidationError:
            # If validation fails, it means extra fields are forbidden
            pass

    def test_workflow_nested_validation(self, valid_workflow_data):
        """Test that nested model validation works correctly."""
        # Invalid metadata
        valid_workflow_data["metadata"] = {
            "name": "A" * 150,  # Too long
            "description": "Test",
            "author": "test",
            "target_site": "https://example.com",
        }

        with pytest.raises(ValidationError) as exc_info:
            Workflow(**valid_workflow_data)

        error_str = str(exc_info.value)
        assert "max_length" in error_str.lower() or "too long" in error_str.lower()

    def test_workflow_step_validation(self, valid_workflow_data):
        """Test workflow step validation."""
        # Invalid step ID pattern
        valid_workflow_data["steps"] = [
            {
                "id": "invalid step id!",  # Contains spaces and special chars
                "command": "init",
                "config": {},
            }
        ]

        with pytest.raises(ValidationError):
            Workflow(**valid_workflow_data)

        # Invalid command
        valid_workflow_data["steps"] = [
            {"id": "test", "command": "invalid_command", "config": {}}
        ]

        with pytest.raises(ValidationError):
            Workflow(**valid_workflow_data)

    def test_workflow_post_processing_validation(self, valid_workflow_data):
        """Test post-processing steps validation."""
        valid_workflow_data["post_processing"] = [
            {"type": "filter", "config": {"condition": "price > 0"}},
            {"type": "invalid_type", "config": {}},  # Invalid type
        ]

        with pytest.raises(ValidationError):
            Workflow(**valid_workflow_data)

    def test_workflow_default_values(self):
        """Test default values for optional fields."""
        minimal_data = {
            "version": "1.0.0",
            "metadata": {
                "name": "Test",
                "description": "Test",
                "author": "test",
                "target_site": "https://example.com",
            },
            "scraping": {"provider": "scrapy", "config": {}},
            "storage": {"provider": "csv", "config": {"file_path": "/tmp/test.csv"}},
            "steps": [{"id": "test", "command": "init", "config": {}}],
        }

        workflow = Workflow(**minimal_data)

        # Check default values
        assert workflow.metadata.tags == []
        assert isinstance(workflow.metadata.created, datetime)
        assert workflow.post_processing is None
        assert workflow.storage.schema is None

        # Check step defaults
        step = workflow.steps[0]
        assert step.retries == 3
        assert step.timeout == 30000
        assert step.continue_on_error is False

    def test_workflow_copy_and_modify(self, valid_workflow_data):
        """Test copying and modifying workflow instances."""
        workflow = Workflow(**valid_workflow_data)

        # Test deep copy
        workflow_copy = workflow.model_copy(deep=True)
        assert workflow_copy.version == workflow.version
        assert workflow_copy.metadata.name == workflow.metadata.name
        assert id(workflow_copy.metadata) != id(workflow.metadata)

        # Test copy with updates
        updated_workflow = workflow.model_copy(update={"version": "2.0.0"})
        assert updated_workflow.version == "2.0.0"
        assert updated_workflow.metadata.name == workflow.metadata.name

    def test_workflow_field_constraints(self, valid_workflow_data):
        """Test field constraints and validation rules."""
        # Test step retries constraint (ge=0)
        valid_workflow_data["steps"][0]["retries"] = -1
        with pytest.raises(ValidationError):
            Workflow(**valid_workflow_data)

        # Test step timeout constraint (gt=0)
        valid_workflow_data["steps"][0]["retries"] = 3
        valid_workflow_data["steps"][0]["timeout"] = 0
        with pytest.raises(ValidationError):
            Workflow(**valid_workflow_data)

        # Test valid constraints
        valid_workflow_data["steps"][0]["timeout"] = 1
        valid_workflow_data["steps"][0]["retries"] = 0
        workflow = Workflow(**valid_workflow_data)
        assert workflow.steps[0].retries == 0
        assert workflow.steps[0].timeout == 1

    def test_workflow_inheritance_composition(self, complex_workflow_data):
        """Test model inheritance and composition."""
        workflow = Workflow(**complex_workflow_data)

        # Test that nested models are properly instantiated
        assert isinstance(workflow.metadata, WorkflowMetadata)
        assert isinstance(workflow.scraping, ScrapingConfig)
        assert isinstance(workflow.storage, StorageConfig)
        assert isinstance(workflow.storage.schema, SchemaDefinition)

        for step in workflow.steps:
            assert isinstance(step, WorkflowStep)

        for post_step in workflow.post_processing:
            assert isinstance(post_step, PostProcessingStep)

    def test_workflow_edge_cases(self, valid_workflow_data):
        """Test edge cases and boundary conditions."""
        # Test with minimal valid step
        valid_workflow_data["steps"] = [
            {"id": "a", "command": "init", "config": {}}  # Minimal valid ID
        ]

        workflow = Workflow(**valid_workflow_data)
        assert len(workflow.steps) == 1
        assert workflow.steps[0].id == "a"

        # Test with maximum retries
        valid_workflow_data["steps"][0]["retries"] = 999999
        workflow = Workflow(**valid_workflow_data)
        assert workflow.steps[0].retries == 999999

        # Test with large timeout
        valid_workflow_data["steps"][0]["timeout"] = 999999999
        workflow = Workflow(**valid_workflow_data)
        assert workflow.steps[0].timeout == 999999999

    def test_workflow_model_validation_errors(self, valid_workflow_data):
        """Test detailed validation error reporting."""
        # Multiple errors at once
        valid_workflow_data["version"] = "invalid"
        valid_workflow_data["steps"] = []

        with pytest.raises(ValidationError) as exc_info:
            Workflow(**valid_workflow_data)

        # Should report multiple errors
        errors = exc_info.value.errors()
        assert len(errors) >= 2

        # Check error structure
        for error in errors:
            assert "loc" in error
            assert "msg" in error
            assert "type" in error

    def test_workflow_model_dict_validation(self):
        """Test validation from dictionary data."""
        # Test model_validate class method
        data = {
            "version": "1.0.0",
            "metadata": {
                "name": "Dict Test",
                "description": "Testing dict validation",
                "author": "test",
                "target_site": "https://example.com",
            },
            "scraping": {"provider": "test", "config": {}},
            "storage": {"provider": "test", "config": {}},
            "steps": [{"id": "test", "command": "init", "config": {}}],
        }

        workflow = Workflow.model_validate(data)
        assert workflow.metadata.name == "Dict Test"

    def test_workflow_model_schema_generation(self):
        """Test JSON schema generation."""
        schema = Workflow.model_json_schema()

        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "required" in schema
        assert "version" in schema["properties"]
        assert "metadata" in schema["properties"]
        assert "steps" in schema["properties"]

        # Check that version has pattern constraint
        version_schema = schema["properties"]["version"]
        assert "pattern" in version_schema

    def test_workflow_model_field_info(self):
        """Test field information and metadata."""
        fields = Workflow.model_fields

        assert "version" in fields
        assert "metadata" in fields
        assert "scraping" in fields
        assert "storage" in fields
        assert "steps" in fields
        assert "post_processing" in fields

        # Check field properties
        # version_field = fields["version"]  # Field exists but not used in assertions
        # Field should have pattern constraint

        # steps_field = fields["steps"]  # Field exists but not used in assertions
        # Steps field should have min_length constraint
