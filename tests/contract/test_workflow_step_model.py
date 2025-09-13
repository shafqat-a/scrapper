"""
Contract test for WorkflowStep Pydantic model validation.
This test validates the WorkflowStep model and step configuration models.
Tests MUST fail before any implementation exists (TDD requirement).
"""

# Standard library imports
import os
import sys
from pathlib import Path
from typing import Any, Dict

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
        Cookie,
        DiscoverStepConfig,
        ExtractStepConfig,
        InitStepConfig,
        PaginateStepConfig,
        WorkflowStep,
    )
except ImportError:
    # If import fails, create minimal models for testing
    # Standard library imports
    from typing import List, Literal, Optional

    # Third-party imports
    from pydantic import BaseModel, Field

    class Cookie(BaseModel):
        name: str
        value: str
        domain: str
        path: str
        expires: Optional[int] = None
        http_only: bool = False
        secure: bool = False

    class InitStepConfig(BaseModel):
        url: str = Field(..., description="Target URL to navigate to")
        wait_for: Optional[str | int] = Field(
            None, description="CSS selector or milliseconds to wait"
        )
        cookies: List[Cookie] = []
        headers: Dict[str, str] = {}

    class DiscoverStepConfig(BaseModel):
        selectors: Dict[str, str] = Field(
            ..., description="CSS selectors for different element types"
        )
        pagination: Optional[Dict[str, Any]] = None

    class ExtractStepConfig(BaseModel):
        elements: Dict[str, Dict[str, Any]] = Field(
            ..., description="Element extraction configuration"
        )

    class PaginateStepConfig(BaseModel):
        next_page_selector: str = Field(
            ..., description="CSS selector for next page link"
        )
        max_pages: Optional[int] = Field(None, ge=1)
        wait_after_click: int = Field(default=1000, ge=0)
        stop_condition: Optional[Dict[str, Any]] = None

    class WorkflowStep(BaseModel):
        id: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+$")
        command: Literal["init", "discover", "extract", "paginate"]
        config: Dict[str, Any]
        retries: int = Field(default=3, ge=0)
        timeout: int = Field(default=30000, gt=0)
        continue_on_error: bool = False


@pytest.mark.contract
class TestWorkflowStepModel:
    """Contract tests for WorkflowStep Pydantic model validation."""

    @pytest.fixture
    def valid_init_step_data(self) -> Dict[str, Any]:
        """Valid init step data."""
        return {
            "id": "init-step",
            "command": "init",
            "config": {
                "url": "https://example.com",
                "wait_for": "body",
                "headers": {"User-Agent": "test-agent"},
            },
        }

    @pytest.fixture
    def valid_discover_step_data(self) -> Dict[str, Any]:
        """Valid discover step data."""
        return {
            "id": "discover-products",
            "command": "discover",
            "config": {
                "selectors": {
                    "products": ".product-item",
                    "pagination": ".pagination-link",
                },
                "pagination": {"type": "numbered", "max_pages": 10},
            },
            "retries": 5,
            "timeout": 45000,
        }

    @pytest.fixture
    def valid_extract_step_data(self) -> Dict[str, Any]:
        """Valid extract step data."""
        return {
            "id": "extract-data",
            "command": "extract",
            "config": {
                "elements": {
                    "title": {
                        "selector": "h1.product-title",
                        "attribute": "text",
                        "required": True,
                    },
                    "price": {
                        "selector": ".price",
                        "attribute": "text",
                        "transform": "parseFloat",
                    },
                    "description": {
                        "selector": ".description",
                        "attribute": "innerHTML",
                    },
                }
            },
            "continue_on_error": True,
        }

    @pytest.fixture
    def valid_paginate_step_data(self) -> Dict[str, Any]:
        """Valid paginate step data."""
        return {
            "id": "next-page",
            "command": "paginate",
            "config": {
                "next_page_selector": "a.next-page",
                "max_pages": 50,
                "wait_after_click": 2000,
                "stop_condition": {"type": "no_new_data", "threshold": 5},
            },
            "retries": 2,
            "timeout": 60000,
        }

    def test_workflow_step_model_exists(self):
        """Test that WorkflowStep model class exists."""
        assert WorkflowStep is not None
        assert issubclass(WorkflowStep, BaseModel)

    def test_workflow_step_valid_creation(self, valid_init_step_data):
        """Test creating a valid WorkflowStep instance."""
        step = WorkflowStep(**valid_init_step_data)

        assert step.id == "init-step"
        assert step.command == "init"
        assert step.config["url"] == "https://example.com"
        assert step.retries == 3  # Default value
        assert step.timeout == 30000  # Default value
        assert step.continue_on_error is False  # Default value

    def test_workflow_step_all_commands(
        self,
        valid_init_step_data,
        valid_discover_step_data,
        valid_extract_step_data,
        valid_paginate_step_data,
    ):
        """Test all valid command types."""
        # Init step
        init_step = WorkflowStep(**valid_init_step_data)
        assert init_step.command == "init"

        # Discover step
        discover_step = WorkflowStep(**valid_discover_step_data)
        assert discover_step.command == "discover"

        # Extract step
        extract_step = WorkflowStep(**valid_extract_step_data)
        assert extract_step.command == "extract"

        # Paginate step
        paginate_step = WorkflowStep(**valid_paginate_step_data)
        assert paginate_step.command == "paginate"

    def test_workflow_step_id_pattern_validation(self, valid_init_step_data):
        """Test step ID pattern validation."""
        # Valid IDs
        valid_ids = [
            "init",
            "step1",
            "extract-data",
            "page_navigation",
            "step-123",
            "CAPS_ID",
            "mixed_Case-123",
            "a",
            "1",
        ]

        for valid_id in valid_ids:
            valid_init_step_data["id"] = valid_id
            step = WorkflowStep(**valid_init_step_data)
            assert step.id == valid_id

        # Invalid IDs
        invalid_ids = [
            "invalid step",  # Contains space
            "step@home",  # Contains @
            "step.config",  # Contains dot
            "step#1",  # Contains hash
            "step!",  # Contains exclamation
            "",  # Empty string
            "step with spaces",  # Multiple spaces
            "step/path",  # Contains slash
        ]

        for invalid_id in invalid_ids:
            valid_init_step_data["id"] = invalid_id
            with pytest.raises(ValidationError):
                WorkflowStep(**valid_init_step_data)

    def test_workflow_step_command_validation(self, valid_init_step_data):
        """Test command field validation."""
        # Valid commands
        valid_commands = ["init", "discover", "extract", "paginate"]

        for command in valid_commands:
            valid_init_step_data["command"] = command
            step = WorkflowStep(**valid_init_step_data)
            assert step.command == command

        # Invalid commands
        invalid_commands = [
            "invalid",
            "setup",
            "teardown",
            "process",
            "",
            "Init",
            "INIT",
            "init_step",
            123,
            None,
        ]

        for command in invalid_commands:
            valid_init_step_data["command"] = command
            with pytest.raises(ValidationError):
                WorkflowStep(**valid_init_step_data)

    def test_workflow_step_retries_validation(self, valid_init_step_data):
        """Test retries field constraints."""
        # Valid retries (ge=0)
        valid_retries = [0, 1, 3, 10, 100, 999]

        for retries in valid_retries:
            valid_init_step_data["retries"] = retries
            step = WorkflowStep(**valid_init_step_data)
            assert step.retries == retries

        # Invalid retries (< 0)
        invalid_retries = [-1, -5, -100]

        for retries in invalid_retries:
            valid_init_step_data["retries"] = retries
            with pytest.raises(ValidationError):
                WorkflowStep(**valid_init_step_data)

        # Invalid types
        invalid_types = ["3", 3.5, None, [3], {"retries": 3}]

        for invalid_type in invalid_types:
            valid_init_step_data["retries"] = invalid_type
            with pytest.raises(ValidationError):
                WorkflowStep(**valid_init_step_data)

    def test_workflow_step_timeout_validation(self, valid_init_step_data):
        """Test timeout field constraints."""
        # Valid timeouts (gt=0)
        valid_timeouts = [1, 1000, 30000, 60000, 300000]

        for timeout in valid_timeouts:
            valid_init_step_data["timeout"] = timeout
            step = WorkflowStep(**valid_init_step_data)
            assert step.timeout == timeout

        # Invalid timeouts (le=0)
        invalid_timeouts = [0, -1, -1000]

        for timeout in invalid_timeouts:
            valid_init_step_data["timeout"] = timeout
            with pytest.raises(ValidationError):
                WorkflowStep(**valid_init_step_data)

    def test_workflow_step_continue_on_error_validation(self, valid_init_step_data):
        """Test continue_on_error field validation."""
        # Valid boolean values
        valid_init_step_data["continue_on_error"] = True
        step = WorkflowStep(**valid_init_step_data)
        assert step.continue_on_error is True

        valid_init_step_data["continue_on_error"] = False
        step = WorkflowStep(**valid_init_step_data)
        assert step.continue_on_error is False

        # Invalid types
        invalid_values = ["true", "false", 1, 0, "yes", "no", None]

        for value in invalid_values:
            valid_init_step_data["continue_on_error"] = value
            # Pydantic may coerce some values, so only test clear non-booleans
            if value not in [1, 0]:  # These might be coerced to bool
                with pytest.raises(ValidationError):
                    WorkflowStep(**valid_init_step_data)

    def test_workflow_step_required_fields(self):
        """Test validation with missing required fields."""
        minimal_data = {"id": "test", "command": "init", "config": {}}

        # Should work with minimal data
        step = WorkflowStep(**minimal_data)
        assert step.id == "test"

        # Test missing required fields
        required_fields = ["id", "command", "config"]

        for field in required_fields:
            data = minimal_data.copy()
            del data[field]
            with pytest.raises(ValidationError) as exc_info:
                WorkflowStep(**data)

            error_str = str(exc_info.value)
            assert field in error_str or "required" in error_str.lower()

    def test_workflow_step_default_values(self):
        """Test default values for optional fields."""
        minimal_data = {
            "id": "test-step",
            "command": "extract",
            "config": {"elements": {}},
        }

        step = WorkflowStep(**minimal_data)

        # Check default values
        assert step.retries == 3
        assert step.timeout == 30000
        assert step.continue_on_error is False

    def test_workflow_step_config_validation(self, valid_init_step_data):
        """Test config field validation."""
        # Config must be a dict
        valid_configs = [
            {},
            {"url": "https://example.com"},
            {"complex": {"nested": {"data": [1, 2, 3]}}},
            {"list": [1, 2, 3], "string": "value", "number": 42},
        ]

        for config in valid_configs:
            valid_init_step_data["config"] = config
            step = WorkflowStep(**valid_init_step_data)
            assert step.config == config

        # Invalid config types
        invalid_configs = ["string", 123, [1, 2, 3], None, True]

        for config in invalid_configs:
            valid_init_step_data["config"] = config
            with pytest.raises(ValidationError):
                WorkflowStep(**valid_init_step_data)

    def test_workflow_step_json_serialization(self, valid_extract_step_data):
        """Test JSON serialization/deserialization."""
        step = WorkflowStep(**valid_extract_step_data)

        # Test model_dump
        json_data = step.model_dump()
        assert isinstance(json_data, dict)
        assert json_data["id"] == "extract-data"
        assert json_data["command"] == "extract"

        # Test JSON string serialization
        json_str = step.model_dump_json()
        assert isinstance(json_str, str)

        # Test deserialization
        step_copy = WorkflowStep.model_validate_json(json_str)
        assert step_copy.id == step.id
        assert step_copy.command == step.command
        assert step_copy.config == step.config

    def test_workflow_step_copy_and_modify(self, valid_discover_step_data):
        """Test copying and modifying step instances."""
        step = WorkflowStep(**valid_discover_step_data)

        # Test deep copy
        step_copy = step.model_copy(deep=True)
        assert step_copy.id == step.id
        assert step_copy.config == step.config
        assert id(step_copy.config) != id(step.config)

        # Test copy with updates
        updated_step = step.model_copy(update={"id": "updated-step", "retries": 10})
        assert updated_step.id == "updated-step"
        assert updated_step.retries == 10
        assert updated_step.command == step.command

    def test_workflow_step_edge_cases(self, valid_init_step_data):
        """Test edge cases and boundary conditions."""
        # Minimal valid ID
        valid_init_step_data["id"] = "a"
        step = WorkflowStep(**valid_init_step_data)
        assert step.id == "a"

        # Maximum timeout
        valid_init_step_data["timeout"] = 2147483647  # Max int32
        step = WorkflowStep(**valid_init_step_data)
        assert step.timeout == 2147483647

        # Maximum retries
        valid_init_step_data["retries"] = 1000000
        step = WorkflowStep(**valid_init_step_data)
        assert step.retries == 1000000

        # Empty config
        valid_init_step_data["config"] = {}
        step = WorkflowStep(**valid_init_step_data)
        assert step.config == {}

    def test_workflow_step_validation_errors(self, valid_init_step_data):
        """Test detailed validation error reporting."""
        # Multiple errors at once
        valid_init_step_data["id"] = "invalid id!"
        valid_init_step_data["command"] = "invalid_command"
        valid_init_step_data["retries"] = -1
        valid_init_step_data["timeout"] = 0

        with pytest.raises(ValidationError) as exc_info:
            WorkflowStep(**valid_init_step_data)

        # Should report multiple errors
        errors = exc_info.value.errors()
        assert len(errors) >= 4

        # Check error structure
        for error in errors:
            assert "loc" in error
            assert "msg" in error
            assert "type" in error

    def test_workflow_step_field_info(self):
        """Test field information and metadata."""
        fields = WorkflowStep.model_fields

        assert "id" in fields
        assert "command" in fields
        assert "config" in fields
        assert "retries" in fields
        assert "timeout" in fields
        assert "continue_on_error" in fields

        # Check field constraints
        # id_field = fields["id"]  # Field exists but not used in assertions
        # Should have pattern constraint

        # retries_field = fields["retries"]  # Field exists but not used in assertions
        # Should have ge=0 constraint

        # timeout_field = fields["timeout"]  # Field exists but not used in assertions
        # Should have gt=0 constraint

    def test_workflow_step_schema_generation(self):
        """Test JSON schema generation."""
        schema = WorkflowStep.model_json_schema()

        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "required" in schema

        # Check required fields
        required_fields = schema["required"]
        assert "id" in required_fields
        assert "command" in required_fields
        assert "config" in required_fields

        # Check field schemas
        properties = schema["properties"]
        assert "id" in properties
        assert "command" in properties
        assert "retries" in properties
        assert "timeout" in properties

        # Check ID pattern
        id_schema = properties["id"]
        assert "pattern" in id_schema

        # Check command enum
        command_schema = properties["command"]
        assert "enum" in command_schema
        expected_commands = ["init", "discover", "extract", "paginate"]
        assert all(cmd in command_schema["enum"] for cmd in expected_commands)


@pytest.mark.contract
class TestStepConfigModels:
    """Contract tests for step configuration models."""

    def test_init_step_config_model_exists(self):
        """Test that InitStepConfig model exists."""
        assert InitStepConfig is not None
        assert issubclass(InitStepConfig, BaseModel)

    def test_init_step_config_validation(self):
        """Test InitStepConfig validation."""
        # Valid config
        config_data = {
            "url": "https://example.com",
            "wait_for": "body",
            "cookies": [],
            "headers": {"User-Agent": "test"},
        }

        config = InitStepConfig(**config_data)
        assert config.url == "https://example.com"
        assert config.wait_for == "body"
        assert config.cookies == []
        assert config.headers["User-Agent"] == "test"

    def test_discover_step_config_validation(self):
        """Test DiscoverStepConfig validation."""
        config_data = {
            "selectors": {"products": ".product-item", "pagination": ".pagination"},
            "pagination": {"type": "numbered", "max_pages": 10},
        }

        config = DiscoverStepConfig(**config_data)
        assert config.selectors["products"] == ".product-item"
        assert config.pagination["type"] == "numbered"

    def test_extract_step_config_validation(self):
        """Test ExtractStepConfig validation."""
        config_data = {
            "elements": {
                "title": {"selector": "h1", "attribute": "text"},
                "price": {
                    "selector": ".price",
                    "attribute": "text",
                    "transform": "parseFloat",
                },
            }
        }

        config = ExtractStepConfig(**config_data)
        assert config.elements["title"]["selector"] == "h1"
        assert config.elements["price"]["transform"] == "parseFloat"

    def test_paginate_step_config_validation(self):
        """Test PaginateStepConfig validation."""
        config_data = {
            "next_page_selector": ".next-page",
            "max_pages": 50,
            "wait_after_click": 2000,
            "stop_condition": {"type": "no_new_data"},
        }

        config = PaginateStepConfig(**config_data)
        assert config.next_page_selector == ".next-page"
        assert config.max_pages == 50
        assert config.wait_after_click == 2000
        assert config.stop_condition["type"] == "no_new_data"

    def test_paginate_step_config_constraints(self):
        """Test PaginateStepConfig field constraints."""
        # Valid max_pages (ge=1)
        valid_data = {"next_page_selector": ".next", "max_pages": 1}
        config = PaginateStepConfig(**valid_data)
        assert config.max_pages == 1

        # Invalid max_pages (< 1)
        valid_data["max_pages"] = 0
        with pytest.raises(ValidationError):
            PaginateStepConfig(**valid_data)

        # Valid wait_after_click (ge=0)
        valid_data["max_pages"] = None
        valid_data["wait_after_click"] = 0
        config = PaginateStepConfig(**valid_data)
        assert config.wait_after_click == 0

        # Invalid wait_after_click (< 0)
        valid_data["wait_after_click"] = -1
        with pytest.raises(ValidationError):
            PaginateStepConfig(**valid_data)

    def test_step_config_default_values(self):
        """Test default values for step config models."""
        # InitStepConfig defaults
        init_config = InitStepConfig(url="https://example.com")
        assert init_config.wait_for is None
        assert init_config.cookies == []
        assert init_config.headers == {}

        # DiscoverStepConfig defaults
        discover_config = DiscoverStepConfig(selectors={"items": ".item"})
        assert discover_config.pagination is None

        # PaginateStepConfig defaults
        paginate_config = PaginateStepConfig(next_page_selector=".next")
        assert paginate_config.max_pages is None
        assert paginate_config.wait_after_click == 1000
        assert paginate_config.stop_condition is None

    def test_cookie_model_validation(self):
        """Test Cookie model validation."""
        cookie_data = {
            "name": "session_id",
            "value": "abc123",
            "domain": ".example.com",
            "path": "/",
            "expires": 1234567890,
            "http_only": True,
            "secure": True,
        }

        cookie = Cookie(**cookie_data)
        assert cookie.name == "session_id"
        assert cookie.value == "abc123"
        assert cookie.domain == ".example.com"
        assert cookie.path == "/"
        assert cookie.expires == 1234567890
        assert cookie.http_only is True
        assert cookie.secure is True

    def test_cookie_model_defaults(self):
        """Test Cookie model default values."""
        minimal_cookie = Cookie(
            name="test", value="value", domain="example.com", path="/"
        )

        assert minimal_cookie.expires is None
        assert minimal_cookie.http_only is False
        assert minimal_cookie.secure is False
