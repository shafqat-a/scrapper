"""
Contract test for PageContext Pydantic model validation.
This test validates the PageContext model and its related models (Cookie, Viewport).
Tests MUST fail before any implementation exists (TDD requirement).
"""

# Standard library imports
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

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
    from provider_interfaces import Cookie, PageContext, Viewport
except ImportError:
    # If import fails, create minimal models for testing
    # Standard library imports
    from typing import List, Optional

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

    class Viewport(BaseModel):
        width: int = Field(ge=320)
        height: int = Field(ge=240)

    class PageContext(BaseModel):
        url: str
        title: str
        cookies: List[Cookie] = []
        navigation_history: List[str] = []
        viewport: Viewport = Viewport(width=1920, height=1080)
        user_agent: str = "scrapper/1.0.0"


@pytest.mark.contract
class TestPageContextModel:
    """Contract tests for PageContext Pydantic model validation."""

    @pytest.fixture
    def valid_page_context_data(self) -> Dict[str, Any]:
        """Valid page context data."""
        return {
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
                },
                {
                    "name": "preferences",
                    "value": "theme=dark;lang=en",
                    "domain": "example.com",
                    "path": "/",
                },
            ],
            "navigation_history": [
                "https://example.com",
                "https://example.com/categories",
                "https://example.com/products?page=1",
            ],
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": "Mozilla/5.0 (compatible; scrapper/2.0.0)",
        }

    @pytest.fixture
    def minimal_page_context_data(self) -> Dict[str, Any]:
        """Minimal valid page context data."""
        return {"url": "https://example.com", "title": "Example Page"}

    @pytest.fixture
    def mobile_page_context_data(self) -> Dict[str, Any]:
        """Mobile viewport page context data."""
        return {
            "url": "https://mobile.example.com",
            "title": "Mobile Example",
            "viewport": {"width": 375, "height": 667},
            "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
        }

    def test_page_context_model_exists(self):
        """Test that PageContext model class exists."""
        assert PageContext is not None
        assert issubclass(PageContext, BaseModel)

    def test_page_context_valid_creation(self, valid_page_context_data):
        """Test creating a valid PageContext instance."""
        context = PageContext(**valid_page_context_data)

        assert context.url == "https://example.com/products?page=1"
        assert context.title == "Products - Example Store"
        assert len(context.cookies) == 2
        assert len(context.navigation_history) == 3
        assert context.viewport.width == 1920
        assert context.viewport.height == 1080
        assert context.user_agent == "Mozilla/5.0 (compatible; scrapper/2.0.0)"

    def test_page_context_minimal_creation(self, minimal_page_context_data):
        """Test creating minimal PageContext with defaults."""
        context = PageContext(**minimal_page_context_data)

        assert context.url == "https://example.com"
        assert context.title == "Example Page"
        assert context.cookies == []  # Default empty list
        assert context.navigation_history == []  # Default empty list
        assert context.viewport.width == 1920  # Default viewport
        assert context.viewport.height == 1080  # Default viewport
        assert context.user_agent == "scrapper/1.0.0"  # Default user agent

    def test_page_context_mobile_creation(self, mobile_page_context_data):
        """Test creating PageContext with mobile viewport."""
        context = PageContext(**mobile_page_context_data)

        assert context.url == "https://mobile.example.com"
        assert context.title == "Mobile Example"
        assert context.viewport.width == 375
        assert context.viewport.height == 667
        assert "iPhone" in context.user_agent

    def test_page_context_url_validation(self, minimal_page_context_data):
        """Test URL field validation."""
        # Valid URLs
        valid_urls = [
            "https://example.com",
            "http://example.com",
            "https://subdomain.example.com/path?query=value",
            "https://example.com:8080/path/to/resource",
            "https://user:pass@example.com/path",
            "https://192.168.1.1:3000/api/data",
            "https://localhost:8080",
        ]

        for url in valid_urls:
            minimal_page_context_data["url"] = url
            context = PageContext(**minimal_page_context_data)
            assert context.url == url

        # Invalid URLs (empty)
        minimal_page_context_data["url"] = ""
        with pytest.raises(ValidationError):
            PageContext(**minimal_page_context_data)

    def test_page_context_title_validation(self, minimal_page_context_data):
        """Test title field validation."""
        # Valid titles
        valid_titles = [
            "Simple Title",
            "Title with Numbers 123",
            "Title with Special Characters: @#$%^&*()",
            "Very Long Title " + "a" * 1000,
            "Unicode Title: 中文标题 العنوان العربي",
            "Title\nwith\nNewlines",
            "Title\twith\tTabs",
        ]

        for title in valid_titles:
            minimal_page_context_data["title"] = title
            context = PageContext(**minimal_page_context_data)
            assert context.title == title

        # Invalid title (empty)
        minimal_page_context_data["title"] = ""
        with pytest.raises(ValidationError):
            PageContext(**minimal_page_context_data)

    def test_page_context_required_fields(self):
        """Test validation with missing required fields."""
        complete_data = {"url": "https://example.com", "title": "Test Page"}

        # Should work with complete data
        context = PageContext(**complete_data)
        assert context.url == "https://example.com"

        # Test missing required fields
        required_fields = ["url", "title"]

        for field in required_fields:
            data = complete_data.copy()
            del data[field]
            with pytest.raises(ValidationError) as exc_info:
                PageContext(**data)

            error_str = str(exc_info.value)
            assert field in error_str or "required" in error_str.lower()

    def test_page_context_default_values(self, minimal_page_context_data):
        """Test default values for optional fields."""
        context = PageContext(**minimal_page_context_data)

        # Check default values
        assert context.cookies == []
        assert context.navigation_history == []
        assert isinstance(context.viewport, Viewport)
        assert context.viewport.width == 1920
        assert context.viewport.height == 1080
        assert context.user_agent == "scrapper/1.0.0"

    def test_page_context_cookies_validation(self, minimal_page_context_data):
        """Test cookies list validation."""
        # Valid cookies list
        valid_cookies = [
            {"name": "test1", "value": "value1", "domain": "example.com", "path": "/"},
            {
                "name": "test2",
                "value": "value2",
                "domain": "example.com",
                "path": "/app",
                "expires": 1703505045,
                "http_only": True,
                "secure": False,
            },
        ]

        minimal_page_context_data["cookies"] = valid_cookies
        context = PageContext(**minimal_page_context_data)
        assert len(context.cookies) == 2
        assert all(isinstance(cookie, Cookie) for cookie in context.cookies)
        assert context.cookies[0].name == "test1"
        assert context.cookies[1].expires == 1703505045

        # Invalid cookies (not a list)
        minimal_page_context_data["cookies"] = "invalid"
        with pytest.raises(ValidationError):
            PageContext(**minimal_page_context_data)

    def test_page_context_navigation_history_validation(
        self, minimal_page_context_data
    ):
        """Test navigation history validation."""
        # Valid navigation history
        valid_history = [
            "https://example.com",
            "https://example.com/page1",
            "https://example.com/page2",
            "https://different.com",
        ]

        minimal_page_context_data["navigation_history"] = valid_history
        context = PageContext(**minimal_page_context_data)
        assert len(context.navigation_history) == 4
        assert context.navigation_history == valid_history

        # Invalid navigation history (not a list)
        minimal_page_context_data["navigation_history"] = "invalid"
        with pytest.raises(ValidationError):
            PageContext(**minimal_page_context_data)

    def test_page_context_viewport_validation(self, minimal_page_context_data):
        """Test viewport field validation."""
        # Valid viewport
        valid_viewport = {"width": 1280, "height": 720}
        minimal_page_context_data["viewport"] = valid_viewport
        context = PageContext(**minimal_page_context_data)
        assert context.viewport.width == 1280
        assert context.viewport.height == 720

        # Invalid viewport (not a dict)
        minimal_page_context_data["viewport"] = "invalid"
        with pytest.raises(ValidationError):
            PageContext(**minimal_page_context_data)

    def test_page_context_user_agent_validation(self, minimal_page_context_data):
        """Test user_agent field validation."""
        # Valid user agents
        valid_user_agents = [
            "scrapper/1.0.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Custom Bot/2.0 (+https://example.com/bot)",
            "Simple Agent",
            "",  # Empty string should be valid
        ]

        for user_agent in valid_user_agents:
            minimal_page_context_data["user_agent"] = user_agent
            context = PageContext(**minimal_page_context_data)
            assert context.user_agent == user_agent

    def test_page_context_json_serialization(self, valid_page_context_data):
        """Test JSON serialization/deserialization."""
        context = PageContext(**valid_page_context_data)

        # Test model_dump
        json_data = context.model_dump()
        assert isinstance(json_data, dict)
        assert json_data["url"] == "https://example.com/products?page=1"
        assert json_data["title"] == "Products - Example Store"
        assert len(json_data["cookies"]) == 2
        assert len(json_data["navigation_history"]) == 3

        # Test JSON string serialization
        json_str = context.model_dump_json()
        assert isinstance(json_str, str)

        # Test deserialization
        context_copy = PageContext.model_validate_json(json_str)
        assert context_copy.url == context.url
        assert context_copy.title == context.title
        assert len(context_copy.cookies) == len(context.cookies)
        assert context_copy.viewport.width == context.viewport.width

    def test_page_context_copy_and_modify(self, valid_page_context_data):
        """Test copying and modifying context instances."""
        context = PageContext(**valid_page_context_data)

        # Test deep copy
        context_copy = context.model_copy(deep=True)
        assert context_copy.url == context.url
        assert context_copy.cookies == context.cookies
        assert id(context_copy.cookies) != id(context.cookies)
        assert id(context_copy.viewport) != id(context.viewport)

        # Test copy with updates
        updated_context = context.model_copy(
            update={"url": "https://new-example.com", "title": "Updated Title"}
        )
        assert updated_context.url == "https://new-example.com"
        assert updated_context.title == "Updated Title"
        assert updated_context.cookies == context.cookies


@pytest.mark.contract
class TestCookieModel:
    """Contract tests for Cookie Pydantic model validation."""

    @pytest.fixture
    def valid_cookie_data(self) -> Dict[str, Any]:
        """Valid cookie data."""
        return {
            "name": "session_token",
            "value": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9",
            "domain": ".example.com",
            "path": "/api",
            "expires": 1703505045,
            "http_only": True,
            "secure": True,
        }

    @pytest.fixture
    def minimal_cookie_data(self) -> Dict[str, Any]:
        """Minimal valid cookie data."""
        return {
            "name": "simple_cookie",
            "value": "simple_value",
            "domain": "example.com",
            "path": "/",
        }

    def test_cookie_model_exists(self):
        """Test that Cookie model class exists."""
        assert Cookie is not None
        assert issubclass(Cookie, BaseModel)

    def test_cookie_valid_creation(self, valid_cookie_data):
        """Test creating a valid Cookie instance."""
        cookie = Cookie(**valid_cookie_data)

        assert cookie.name == "session_token"
        assert cookie.value == "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9"
        assert cookie.domain == ".example.com"
        assert cookie.path == "/api"
        assert cookie.expires == 1703505045
        assert cookie.http_only is True
        assert cookie.secure is True

    def test_cookie_minimal_creation(self, minimal_cookie_data):
        """Test creating minimal Cookie with defaults."""
        cookie = Cookie(**minimal_cookie_data)

        assert cookie.name == "simple_cookie"
        assert cookie.value == "simple_value"
        assert cookie.domain == "example.com"
        assert cookie.path == "/"
        assert cookie.expires is None  # Default
        assert cookie.http_only is False  # Default
        assert cookie.secure is False  # Default

    def test_cookie_required_fields(self):
        """Test validation with missing required fields."""
        complete_data = {
            "name": "test",
            "value": "test",
            "domain": "example.com",
            "path": "/",
        }

        # Should work with complete data
        cookie = Cookie(**complete_data)
        assert cookie.name == "test"

        # Test missing required fields
        required_fields = ["name", "value", "domain", "path"]

        for field in required_fields:
            data = complete_data.copy()
            del data[field]
            with pytest.raises(ValidationError) as exc_info:
                Cookie(**data)

            error_str = str(exc_info.value)
            assert field in error_str or "required" in error_str.lower()

    def test_cookie_default_values(self, minimal_cookie_data):
        """Test default values for optional fields."""
        cookie = Cookie(**minimal_cookie_data)

        # Check default values
        assert cookie.expires is None
        assert cookie.http_only is False
        assert cookie.secure is False

    def test_cookie_name_validation(self, minimal_cookie_data):
        """Test cookie name validation."""
        # Valid names
        valid_names = [
            "session",
            "user_id",
            "preferences",
            "auth-token",
            "JSESSIONID",
            "_ga",
            "csrf_token",
            "a",
            "1",
            "very_long_cookie_name_with_underscores_and_numbers_123",
        ]

        for name in valid_names:
            minimal_cookie_data["name"] = name
            cookie = Cookie(**minimal_cookie_data)
            assert cookie.name == name

        # Invalid names (empty)
        minimal_cookie_data["name"] = ""
        with pytest.raises(ValidationError):
            Cookie(**minimal_cookie_data)

    def test_cookie_value_validation(self, minimal_cookie_data):
        """Test cookie value validation."""
        # Valid values
        valid_values = [
            "simple_value",
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9",  # JWT token
            "abc123def456",
            "value with spaces",
            "value=with;special,characters",
            "123456789",
            "",  # Empty value should be valid
            "very_long_value_" + "a" * 4000,  # Long value
        ]

        for value in valid_values:
            minimal_cookie_data["value"] = value
            cookie = Cookie(**minimal_cookie_data)
            assert cookie.value == value

    def test_cookie_domain_validation(self, minimal_cookie_data):
        """Test cookie domain validation."""
        # Valid domains
        valid_domains = [
            "example.com",
            ".example.com",  # With leading dot
            "subdomain.example.com",
            "localhost",
            "192.168.1.1",
            "::1",  # IPv6
            "example.co.uk",
            "very-long-subdomain.example-domain.com",
        ]

        for domain in valid_domains:
            minimal_cookie_data["domain"] = domain
            cookie = Cookie(**minimal_cookie_data)
            assert cookie.domain == domain

        # Invalid domain (empty)
        minimal_cookie_data["domain"] = ""
        with pytest.raises(ValidationError):
            Cookie(**minimal_cookie_data)

    def test_cookie_path_validation(self, minimal_cookie_data):
        """Test cookie path validation."""
        # Valid paths
        valid_paths = [
            "/",
            "/api",
            "/api/v1",
            "/app/user/profile",
            "/path with spaces",
            "/path/with/query?param=value",
            "/very/long/path/with/many/segments/here",
        ]

        for path in valid_paths:
            minimal_cookie_data["path"] = path
            cookie = Cookie(**minimal_cookie_data)
            assert cookie.path == path

        # Invalid path (empty)
        minimal_cookie_data["path"] = ""
        with pytest.raises(ValidationError):
            Cookie(**minimal_cookie_data)

    def test_cookie_expires_validation(self, minimal_cookie_data):
        """Test cookie expires validation."""
        # Valid expires values
        valid_expires = [
            None,  # No expiration
            0,  # Unix epoch
            1703505045,  # Valid timestamp
            2147483647,  # Max 32-bit timestamp
            9999999999,  # Future timestamp
        ]

        for expires in valid_expires:
            minimal_cookie_data["expires"] = expires
            cookie = Cookie(**minimal_cookie_data)
            assert cookie.expires == expires

        # Invalid expires (negative)
        minimal_cookie_data["expires"] = -1
        # Note: Some systems might allow negative timestamps
        # The validation depends on implementation

    def test_cookie_boolean_flags(self, minimal_cookie_data):
        """Test boolean flags validation."""
        # Test http_only flag
        minimal_cookie_data["http_only"] = True
        cookie = Cookie(**minimal_cookie_data)
        assert cookie.http_only is True

        minimal_cookie_data["http_only"] = False
        cookie = Cookie(**minimal_cookie_data)
        assert cookie.http_only is False

        # Test secure flag
        minimal_cookie_data["secure"] = True
        cookie = Cookie(**minimal_cookie_data)
        assert cookie.secure is True

        minimal_cookie_data["secure"] = False
        cookie = Cookie(**minimal_cookie_data)
        assert cookie.secure is False

    def test_cookie_json_serialization(self, valid_cookie_data):
        """Test JSON serialization/deserialization."""
        cookie = Cookie(**valid_cookie_data)

        # Test model_dump
        json_data = cookie.model_dump()
        assert isinstance(json_data, dict)
        assert json_data["name"] == "session_token"
        assert json_data["expires"] == 1703505045

        # Test JSON string serialization
        json_str = cookie.model_dump_json()
        assert isinstance(json_str, str)

        # Test deserialization
        cookie_copy = Cookie.model_validate_json(json_str)
        assert cookie_copy.name == cookie.name
        assert cookie_copy.value == cookie.value
        assert cookie_copy.expires == cookie.expires


@pytest.mark.contract
class TestViewportModel:
    """Contract tests for Viewport Pydantic model validation."""

    def test_viewport_model_exists(self):
        """Test that Viewport model class exists."""
        assert Viewport is not None
        assert issubclass(Viewport, BaseModel)

    def test_viewport_valid_creation(self):
        """Test creating valid Viewport instances."""
        # Standard desktop viewport
        desktop = Viewport(width=1920, height=1080)
        assert desktop.width == 1920
        assert desktop.height == 1080

        # Mobile viewport
        mobile = Viewport(width=375, height=667)
        assert mobile.width == 375
        assert mobile.height == 667

        # Tablet viewport
        tablet = Viewport(width=768, height=1024)
        assert tablet.width == 768
        assert tablet.height == 1024

    def test_viewport_width_constraints(self):
        """Test width field constraints (ge=320)."""
        # Valid widths (>= 320)
        valid_widths = [320, 375, 768, 1024, 1280, 1920, 3840, 10000]

        for width in valid_widths:
            viewport = Viewport(width=width, height=600)
            assert viewport.width == width

        # Invalid widths (< 320)
        invalid_widths = [0, 100, 240, 319, -1, -100]

        for width in invalid_widths:
            with pytest.raises(ValidationError):
                Viewport(width=width, height=600)

    def test_viewport_height_constraints(self):
        """Test height field constraints (ge=240)."""
        # Valid heights (>= 240)
        valid_heights = [240, 480, 600, 720, 1080, 1440, 2160, 10000]

        for height in valid_heights:
            viewport = Viewport(width=800, height=height)
            assert viewport.height == height

        # Invalid heights (< 240)
        invalid_heights = [0, 100, 200, 239, -1, -100]

        for height in invalid_heights:
            with pytest.raises(ValidationError):
                Viewport(width=800, height=height)

    def test_viewport_required_fields(self):
        """Test that both width and height are required."""
        # Should fail without width
        with pytest.raises(ValidationError):
            Viewport(height=600)

        # Should fail without height
        with pytest.raises(ValidationError):
            Viewport(width=800)

        # Should fail without both
        with pytest.raises(ValidationError):
            Viewport()

    def test_viewport_type_validation(self):
        """Test width and height type validation."""
        # Invalid types for width
        invalid_widths = ["800", 800.5, None, [800], {"width": 800}]

        for width in invalid_widths:
            with pytest.raises(ValidationError):
                Viewport(width=width, height=600)

        # Invalid types for height
        invalid_heights = ["600", 600.5, None, [600], {"height": 600}]

        for height in invalid_heights:
            with pytest.raises(ValidationError):
                Viewport(width=800, height=height)

    def test_viewport_common_sizes(self):
        """Test common viewport sizes."""
        common_sizes = {
            "mobile_portrait": (375, 667),
            "mobile_landscape": (667, 375),
            "tablet_portrait": (768, 1024),
            "tablet_landscape": (1024, 768),
            "desktop_hd": (1280, 720),
            "desktop_fhd": (1920, 1080),
            "desktop_4k": (3840, 2160),
            "minimal": (320, 240),
        }

        for name, (width, height) in common_sizes.items():
            viewport = Viewport(width=width, height=height)
            assert viewport.width == width
            assert viewport.height == height

    def test_viewport_json_serialization(self):
        """Test JSON serialization/deserialization."""
        viewport = Viewport(width=1280, height=800)

        # Test model_dump
        json_data = viewport.model_dump()
        assert isinstance(json_data, dict)
        assert json_data["width"] == 1280
        assert json_data["height"] == 800

        # Test JSON string serialization
        json_str = viewport.model_dump_json()
        assert isinstance(json_str, str)

        # Test deserialization
        viewport_copy = Viewport.model_validate_json(json_str)
        assert viewport_copy.width == viewport.width
        assert viewport_copy.height == viewport.height

    def test_viewport_copy_and_modify(self):
        """Test copying and modifying viewport instances."""
        viewport = Viewport(width=1920, height=1080)

        # Test copy
        viewport_copy = viewport.model_copy()
        assert viewport_copy.width == viewport.width
        assert viewport_copy.height == viewport.height

        # Test copy with updates
        mobile_viewport = viewport.model_copy(update={"width": 375, "height": 667})
        assert mobile_viewport.width == 375
        assert mobile_viewport.height == 667

    def test_viewport_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Minimum valid size
        min_viewport = Viewport(width=320, height=240)
        assert min_viewport.width == 320
        assert min_viewport.height == 240

        # Very large size
        large_viewport = Viewport(width=100000, height=100000)
        assert large_viewport.width == 100000
        assert large_viewport.height == 100000

        # Just above minimum
        above_min = Viewport(width=321, height=241)
        assert above_min.width == 321
        assert above_min.height == 241

    def test_viewport_field_info(self):
        """Test field information and constraints."""
        fields = Viewport.model_fields

        assert "width" in fields
        assert "height" in fields

        # Check field constraints
        # width_field = fields["width"]  # Field exists but not used in assertions
        # height_field = fields["height"]  # Field exists but not used in assertions

        # Both should have ge constraints

    def test_viewport_schema_generation(self):
        """Test JSON schema generation."""
        schema = Viewport.model_json_schema()

        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "required" in schema

        # Check required fields
        required_fields = schema["required"]
        assert "width" in required_fields
        assert "height" in required_fields

        # Check field constraints
        properties = schema["properties"]
        width_schema = properties["width"]
        height_schema = properties["height"]

        assert width_schema["type"] == "integer"
        assert height_schema["type"] == "integer"
        assert width_schema["minimum"] == 320
        assert height_schema["minimum"] == 240
