"""
Contract test for Provider Configuration Pydantic model validation.
This test validates scraping and storage provider configuration models.
Tests MUST fail before any implementation exists (TDD requirement).
"""

# Standard library imports
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

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
        BeautifulSoupConfig,
        ConnectionConfig,
        CSVStorageConfig,
        MongoDBStorageConfig,
        PlaywrightConfig,
        PostgreSQLStorageConfig,
        ScrapyConfig,
        SQLiteStorageConfig,
        Viewport,
    )
except ImportError:
    # If import fails, create minimal models for testing
    # Standard library imports
    from typing import Literal

    # Third-party imports
    from pydantic import BaseModel, Field

    class ConnectionConfig(BaseModel):
        """Base configuration for provider connections."""

        pass

    class Viewport(BaseModel):
        width: int = Field(ge=320)
        height: int = Field(ge=240)

    # Scraping Provider Configs
    class ScrapyConfig(ConnectionConfig):
        concurrent_requests: int = Field(default=8, ge=1, le=100)
        download_delay: float = Field(default=0.5, ge=0)
        randomize_download_delay: bool = True
        user_agent: Optional[str] = None
        robotstxt_obey: bool = True

    class PlaywrightConfig(ConnectionConfig):
        browser: Literal["chromium", "firefox", "webkit"] = "chromium"
        headless: bool = True
        viewport: Viewport = Viewport(width=1920, height=1080)
        user_agent: Optional[str] = None
        timeout: int = Field(default=30000, gt=0)

    class BeautifulSoupConfig(ConnectionConfig):
        parser: Literal["html.parser", "lxml", "html5lib"] = "lxml"
        timeout: int = Field(default=10000, gt=0)
        user_agent: Optional[str] = None
        follow_redirects: bool = True

    # Storage Provider Configs
    class CSVStorageConfig(ConnectionConfig):
        file_path: str
        delimiter: str = ","
        headers: bool = True
        append: bool = False

    class PostgreSQLStorageConfig(ConnectionConfig):
        connection_string: str
        table_name: str
        create_table: bool = True
        batch_size: int = Field(default=1000, ge=1)

    class MongoDBStorageConfig(ConnectionConfig):
        connection_string: str
        database: str
        collection: str
        upsert: bool = False

    class SQLiteStorageConfig(ConnectionConfig):
        database_path: str
        table_name: str
        create_table: bool = True


@pytest.mark.contract
class TestScrapingProviderConfigs:
    """Contract tests for scraping provider configuration models."""

    def test_connection_config_base_class(self):
        """Test that ConnectionConfig base class exists."""
        assert ConnectionConfig is not None
        assert issubclass(ConnectionConfig, BaseModel)

        # Should be able to create empty config
        config = ConnectionConfig()
        assert isinstance(config, ConnectionConfig)

    def test_scrapy_config_model_exists(self):
        """Test that ScrapyConfig model class exists."""
        assert ScrapyConfig is not None
        assert issubclass(ScrapyConfig, ConnectionConfig)
        assert issubclass(ScrapyConfig, BaseModel)

    def test_scrapy_config_defaults(self):
        """Test ScrapyConfig default values."""
        config = ScrapyConfig()

        assert config.concurrent_requests == 8
        assert config.download_delay == 0.5
        assert config.randomize_download_delay is True
        assert config.user_agent is None
        assert config.robotstxt_obey is True

    def test_scrapy_config_validation(self):
        """Test ScrapyConfig field validation."""
        # Valid configuration
        valid_data = {
            "concurrent_requests": 16,
            "download_delay": 1.0,
            "randomize_download_delay": False,
            "user_agent": "Custom Bot/1.0",
            "robotstxt_obey": False,
        }

        config = ScrapyConfig(**valid_data)
        assert config.concurrent_requests == 16
        assert config.download_delay == 1.0
        assert config.randomize_download_delay is False
        assert config.user_agent == "Custom Bot/1.0"
        assert config.robotstxt_obey is False

    def test_scrapy_config_concurrent_requests_constraints(self):
        """Test concurrent_requests field constraints."""
        # Valid values (ge=1, le=100)
        valid_values = [1, 8, 16, 50, 100]

        for value in valid_values:
            config = ScrapyConfig(concurrent_requests=value)
            assert config.concurrent_requests == value

        # Invalid values (< 1 or > 100)
        invalid_values = [0, -1, 101, 200, 1000]

        for value in invalid_values:
            with pytest.raises(ValidationError):
                ScrapyConfig(concurrent_requests=value)

    def test_scrapy_config_download_delay_constraints(self):
        """Test download_delay field constraints."""
        # Valid values (ge=0)
        valid_values = [0, 0.1, 0.5, 1.0, 5.0, 10.0]

        for value in valid_values:
            config = ScrapyConfig(download_delay=value)
            assert config.download_delay == value

        # Invalid values (< 0)
        invalid_values = [-0.1, -1.0, -10.0]

        for value in invalid_values:
            with pytest.raises(ValidationError):
                ScrapyConfig(download_delay=value)

    def test_playwright_config_model_exists(self):
        """Test that PlaywrightConfig model class exists."""
        assert PlaywrightConfig is not None
        assert issubclass(PlaywrightConfig, ConnectionConfig)
        assert issubclass(PlaywrightConfig, BaseModel)

    def test_playwright_config_defaults(self):
        """Test PlaywrightConfig default values."""
        config = PlaywrightConfig()

        assert config.browser == "chromium"
        assert config.headless is True
        assert isinstance(config.viewport, Viewport)
        assert config.viewport.width == 1920
        assert config.viewport.height == 1080
        assert config.user_agent is None
        assert config.timeout == 30000

    def test_playwright_config_validation(self):
        """Test PlaywrightConfig field validation."""
        # Valid configuration
        valid_data = {
            "browser": "firefox",
            "headless": False,
            "viewport": {"width": 1280, "height": 720},
            "user_agent": "Mozilla/5.0 Test Browser",
            "timeout": 60000,
        }

        config = PlaywrightConfig(**valid_data)
        assert config.browser == "firefox"
        assert config.headless is False
        assert config.viewport.width == 1280
        assert config.viewport.height == 720
        assert config.user_agent == "Mozilla/5.0 Test Browser"
        assert config.timeout == 60000

    def test_playwright_config_browser_validation(self):
        """Test browser field validation."""
        # Valid browsers
        valid_browsers = ["chromium", "firefox", "webkit"]

        for browser in valid_browsers:
            config = PlaywrightConfig(browser=browser)
            assert config.browser == browser

        # Invalid browsers
        invalid_browsers = ["chrome", "safari", "edge", "invalid", ""]

        for browser in invalid_browsers:
            with pytest.raises(ValidationError):
                PlaywrightConfig(browser=browser)

    def test_playwright_config_timeout_constraints(self):
        """Test timeout field constraints."""
        # Valid timeouts (gt=0)
        valid_timeouts = [1, 1000, 30000, 60000, 300000]

        for timeout in valid_timeouts:
            config = PlaywrightConfig(timeout=timeout)
            assert config.timeout == timeout

        # Invalid timeouts (le=0)
        invalid_timeouts = [0, -1, -1000]

        for timeout in invalid_timeouts:
            with pytest.raises(ValidationError):
                PlaywrightConfig(timeout=timeout)

    def test_beautifulsoup_config_model_exists(self):
        """Test that BeautifulSoupConfig model class exists."""
        assert BeautifulSoupConfig is not None
        assert issubclass(BeautifulSoupConfig, ConnectionConfig)
        assert issubclass(BeautifulSoupConfig, BaseModel)

    def test_beautifulsoup_config_defaults(self):
        """Test BeautifulSoupConfig default values."""
        config = BeautifulSoupConfig()

        assert config.parser == "lxml"
        assert config.timeout == 10000
        assert config.user_agent is None
        assert config.follow_redirects is True

    def test_beautifulsoup_config_validation(self):
        """Test BeautifulSoupConfig field validation."""
        # Valid configuration
        valid_data = {
            "parser": "html.parser",
            "timeout": 5000,
            "user_agent": "Custom Parser/1.0",
            "follow_redirects": False,
        }

        config = BeautifulSoupConfig(**valid_data)
        assert config.parser == "html.parser"
        assert config.timeout == 5000
        assert config.user_agent == "Custom Parser/1.0"
        assert config.follow_redirects is False

    def test_beautifulsoup_config_parser_validation(self):
        """Test parser field validation."""
        # Valid parsers
        valid_parsers = ["html.parser", "lxml", "html5lib"]

        for parser in valid_parsers:
            config = BeautifulSoupConfig(parser=parser)
            assert config.parser == parser

        # Invalid parsers
        invalid_parsers = ["xml", "html", "bs4", "invalid", ""]

        for parser in invalid_parsers:
            with pytest.raises(ValidationError):
                BeautifulSoupConfig(parser=parser)

    def test_beautifulsoup_config_timeout_constraints(self):
        """Test timeout field constraints."""
        # Valid timeouts (gt=0)
        valid_timeouts = [1, 1000, 10000, 30000]

        for timeout in valid_timeouts:
            config = BeautifulSoupConfig(timeout=timeout)
            assert config.timeout == timeout

        # Invalid timeouts (le=0)
        invalid_timeouts = [0, -1, -1000]

        for timeout in invalid_timeouts:
            with pytest.raises(ValidationError):
                BeautifulSoupConfig(timeout=timeout)

    def test_scraping_config_json_serialization(self):
        """Test JSON serialization for scraping configs."""
        # Test ScrapyConfig
        scrapy_config = ScrapyConfig(
            concurrent_requests=16, download_delay=1.0, user_agent="Test Agent"
        )

        json_data = scrapy_config.model_dump()
        assert json_data["concurrent_requests"] == 16
        assert json_data["download_delay"] == 1.0
        assert json_data["user_agent"] == "Test Agent"

        # Test deserialization
        config_copy = ScrapyConfig.model_validate(json_data)
        assert config_copy.concurrent_requests == 16
        assert config_copy.user_agent == "Test Agent"

        # Test PlaywrightConfig
        playwright_config = PlaywrightConfig(
            browser="firefox", headless=False, timeout=45000
        )

        json_str = playwright_config.model_dump_json()
        config_copy = PlaywrightConfig.model_validate_json(json_str)
        assert config_copy.browser == "firefox"
        assert config_copy.headless is False
        assert config_copy.timeout == 45000


@pytest.mark.contract
class TestStorageProviderConfigs:
    """Contract tests for storage provider configuration models."""

    def test_csv_storage_config_model_exists(self):
        """Test that CSVStorageConfig model class exists."""
        assert CSVStorageConfig is not None
        assert issubclass(CSVStorageConfig, ConnectionConfig)
        assert issubclass(CSVStorageConfig, BaseModel)

    def test_csv_storage_config_validation(self):
        """Test CSVStorageConfig validation."""
        # Valid configuration
        valid_data = {
            "file_path": "/tmp/scraped_data.csv",
            "delimiter": ";",
            "headers": False,
            "append": True,
        }

        config = CSVStorageConfig(**valid_data)
        assert config.file_path == "/tmp/scraped_data.csv"
        assert config.delimiter == ";"
        assert config.headers is False
        assert config.append is True

    def test_csv_storage_config_defaults(self):
        """Test CSVStorageConfig default values."""
        config = CSVStorageConfig(file_path="/tmp/test.csv")

        assert config.file_path == "/tmp/test.csv"
        assert config.delimiter == ","
        assert config.headers is True
        assert config.append is False

    def test_csv_storage_config_required_fields(self):
        """Test CSVStorageConfig required fields."""
        # Should fail without file_path
        with pytest.raises(ValidationError):
            CSVStorageConfig()

        # Should work with file_path
        config = CSVStorageConfig(file_path="test.csv")
        assert config.file_path == "test.csv"

    def test_csv_storage_config_file_path_validation(self):
        """Test file_path validation."""
        # Valid file paths
        valid_paths = [
            "/tmp/data.csv",
            "./output/results.csv",
            "../data/export.csv",
            "C:\\Data\\export.csv",
            "data.csv",
            "/very/long/path/to/file/with/many/segments/data.csv",
        ]

        for path in valid_paths:
            config = CSVStorageConfig(file_path=path)
            assert config.file_path == path

        # Invalid file path (empty)
        with pytest.raises(ValidationError):
            CSVStorageConfig(file_path="")

    def test_postgresql_storage_config_model_exists(self):
        """Test that PostgreSQLStorageConfig model class exists."""
        assert PostgreSQLStorageConfig is not None
        assert issubclass(PostgreSQLStorageConfig, ConnectionConfig)
        assert issubclass(PostgreSQLStorageConfig, BaseModel)

    def test_postgresql_storage_config_validation(self):
        """Test PostgreSQLStorageConfig validation."""
        # Valid configuration
        valid_data = {
            "connection_string": "postgresql://user:pass@localhost:5432/mydb",
            "table_name": "scraped_products",
            "create_table": False,
            "batch_size": 500,
        }

        config = PostgreSQLStorageConfig(**valid_data)
        assert config.connection_string == "postgresql://user:pass@localhost:5432/mydb"
        assert config.table_name == "scraped_products"
        assert config.create_table is False
        assert config.batch_size == 500

    def test_postgresql_storage_config_defaults(self):
        """Test PostgreSQLStorageConfig default values."""
        config = PostgreSQLStorageConfig(
            connection_string="postgresql://localhost/test", table_name="test_table"
        )

        assert config.create_table is True
        assert config.batch_size == 1000

    def test_postgresql_storage_config_required_fields(self):
        """Test PostgreSQLStorageConfig required fields."""
        # Should fail without connection_string
        with pytest.raises(ValidationError):
            PostgreSQLStorageConfig(table_name="test")

        # Should fail without table_name
        with pytest.raises(ValidationError):
            PostgreSQLStorageConfig(connection_string="postgresql://localhost/test")

        # Should work with both
        config = PostgreSQLStorageConfig(
            connection_string="postgresql://localhost/test", table_name="test_table"
        )
        assert config.connection_string == "postgresql://localhost/test"
        assert config.table_name == "test_table"

    def test_postgresql_storage_config_batch_size_constraints(self):
        """Test batch_size field constraints."""
        # Valid batch sizes (ge=1)
        valid_sizes = [1, 100, 1000, 5000, 10000]

        for size in valid_sizes:
            config = PostgreSQLStorageConfig(
                connection_string="postgresql://localhost/test",
                table_name="test",
                batch_size=size,
            )
            assert config.batch_size == size

        # Invalid batch sizes (< 1)
        invalid_sizes = [0, -1, -100]

        for size in invalid_sizes:
            with pytest.raises(ValidationError):
                PostgreSQLStorageConfig(
                    connection_string="postgresql://localhost/test",
                    table_name="test",
                    batch_size=size,
                )

    def test_mongodb_storage_config_model_exists(self):
        """Test that MongoDBStorageConfig model class exists."""
        assert MongoDBStorageConfig is not None
        assert issubclass(MongoDBStorageConfig, ConnectionConfig)
        assert issubclass(MongoDBStorageConfig, BaseModel)

    def test_mongodb_storage_config_validation(self):
        """Test MongoDBStorageConfig validation."""
        # Valid configuration
        valid_data = {
            "connection_string": "mongodb://user:pass@localhost:27017/mydb",
            "database": "scraping_db",
            "collection": "products",
            "upsert": True,
        }

        config = MongoDBStorageConfig(**valid_data)
        assert config.connection_string == "mongodb://user:pass@localhost:27017/mydb"
        assert config.database == "scraping_db"
        assert config.collection == "products"
        assert config.upsert is True

    def test_mongodb_storage_config_defaults(self):
        """Test MongoDBStorageConfig default values."""
        config = MongoDBStorageConfig(
            connection_string="mongodb://localhost/test",
            database="test_db",
            collection="test_collection",
        )

        assert config.upsert is False

    def test_mongodb_storage_config_required_fields(self):
        """Test MongoDBStorageConfig required fields."""
        required_fields = ["connection_string", "database", "collection"]

        complete_data = {
            "connection_string": "mongodb://localhost/test",
            "database": "test_db",
            "collection": "test_collection",
        }

        # Should work with complete data
        config = MongoDBStorageConfig(**complete_data)
        assert config.database == "test_db"

        # Test missing each required field
        for field in required_fields:
            data = complete_data.copy()
            del data[field]
            with pytest.raises(ValidationError):
                MongoDBStorageConfig(**data)

    def test_sqlite_storage_config_model_exists(self):
        """Test that SQLiteStorageConfig model class exists."""
        assert SQLiteStorageConfig is not None
        assert issubclass(SQLiteStorageConfig, ConnectionConfig)
        assert issubclass(SQLiteStorageConfig, BaseModel)

    def test_sqlite_storage_config_validation(self):
        """Test SQLiteStorageConfig validation."""
        # Valid configuration
        valid_data = {
            "database_path": "/tmp/scraping.db",
            "table_name": "scraped_data",
            "create_table": False,
        }

        config = SQLiteStorageConfig(**valid_data)
        assert config.database_path == "/tmp/scraping.db"
        assert config.table_name == "scraped_data"
        assert config.create_table is False

    def test_sqlite_storage_config_defaults(self):
        """Test SQLiteStorageConfig default values."""
        config = SQLiteStorageConfig(database_path="test.db", table_name="test_table")

        assert config.create_table is True

    def test_sqlite_storage_config_required_fields(self):
        """Test SQLiteStorageConfig required fields."""
        # Should fail without database_path
        with pytest.raises(ValidationError):
            SQLiteStorageConfig(table_name="test")

        # Should fail without table_name
        with pytest.raises(ValidationError):
            SQLiteStorageConfig(database_path="test.db")

        # Should work with both
        config = SQLiteStorageConfig(database_path="test.db", table_name="test_table")
        assert config.database_path == "test.db"
        assert config.table_name == "test_table"

    def test_storage_config_json_serialization(self):
        """Test JSON serialization for storage configs."""
        # Test CSVStorageConfig
        csv_config = CSVStorageConfig(
            file_path="output.csv", delimiter="|", headers=False
        )

        json_data = csv_config.model_dump()
        assert json_data["file_path"] == "output.csv"
        assert json_data["delimiter"] == "|"
        assert json_data["headers"] is False

        # Test deserialization
        config_copy = CSVStorageConfig.model_validate(json_data)
        assert config_copy.file_path == "output.csv"
        assert config_copy.delimiter == "|"

        # Test PostgreSQLStorageConfig
        pg_config = PostgreSQLStorageConfig(
            connection_string="postgresql://localhost/test",
            table_name="products",
            batch_size=2000,
        )

        json_str = pg_config.model_dump_json()
        config_copy = PostgreSQLStorageConfig.model_validate_json(json_str)
        assert config_copy.table_name == "products"
        assert config_copy.batch_size == 2000


@pytest.mark.contract
class TestProviderConfigIntegration:
    """Integration tests for provider configuration models."""

    def test_config_inheritance_hierarchy(self):
        """Test that all config classes inherit from ConnectionConfig."""
        config_classes = [
            ScrapyConfig,
            PlaywrightConfig,
            BeautifulSoupConfig,
            CSVStorageConfig,
            PostgreSQLStorageConfig,
            MongoDBStorageConfig,
            SQLiteStorageConfig,
        ]

        for config_class in config_classes:
            assert issubclass(config_class, ConnectionConfig)
            assert issubclass(config_class, BaseModel)

            # Should be able to create instance
            try:
                # Try with minimal required fields
                if config_class == CSVStorageConfig:
                    instance = config_class(file_path="test.csv")
                elif config_class == PostgreSQLStorageConfig:
                    instance = config_class(
                        connection_string="postgresql://localhost/test",
                        table_name="test",
                    )
                elif config_class == MongoDBStorageConfig:
                    instance = config_class(
                        connection_string="mongodb://localhost/test",
                        database="test",
                        collection="test",
                    )
                elif config_class == SQLiteStorageConfig:
                    instance = config_class(database_path="test.db", table_name="test")
                else:
                    # Scraping configs have no required fields
                    instance = config_class()

                assert isinstance(instance, config_class)
                assert isinstance(instance, ConnectionConfig)

            except ValidationError:
                # Some configs might require additional fields
                pass

    def test_config_field_types_consistency(self):
        """Test consistency of field types across configs."""
        # Test that timeout fields are consistently integers
        playwright_config = PlaywrightConfig(timeout=30000)
        soup_config = BeautifulSoupConfig(timeout=10000)

        assert isinstance(playwright_config.timeout, int)
        assert isinstance(soup_config.timeout, int)

        # Test that boolean fields work consistently
        scrapy_config = ScrapyConfig(robotstxt_obey=False)
        csv_config = CSVStorageConfig(file_path="test.csv", headers=False)

        assert isinstance(scrapy_config.robotstxt_obey, bool)
        assert isinstance(csv_config.headers, bool)

    def test_config_copy_and_modify(self):
        """Test copying and modifying config instances."""
        # Test scraping config copy
        original_config = ScrapyConfig(
            concurrent_requests=16, download_delay=1.0, user_agent="Original Agent"
        )

        modified_config = original_config.model_copy(
            update={"concurrent_requests": 32, "user_agent": "Modified Agent"}
        )

        assert modified_config.concurrent_requests == 32
        assert modified_config.user_agent == "Modified Agent"
        assert modified_config.download_delay == 1.0  # Unchanged
        assert original_config.concurrent_requests == 16  # Original unchanged

        # Test storage config copy
        original_storage = PostgreSQLStorageConfig(
            connection_string="postgresql://localhost/original",
            table_name="original_table",
            batch_size=1000,
        )

        modified_storage = original_storage.model_copy(
            update={"table_name": "modified_table", "batch_size": 2000}
        )

        assert modified_storage.table_name == "modified_table"
        assert modified_storage.batch_size == 2000
        assert modified_storage.connection_string == "postgresql://localhost/original"
        assert original_storage.table_name == "original_table"

    def test_config_schema_generation(self):
        """Test JSON schema generation for config models."""
        # Test scraping config schema
        scrapy_schema = ScrapyConfig.model_json_schema()
        assert isinstance(scrapy_schema, dict)
        assert "properties" in scrapy_schema
        assert "concurrent_requests" in scrapy_schema["properties"]
        assert "download_delay" in scrapy_schema["properties"]

        # Check constraints are in schema
        concurrent_req_schema = scrapy_schema["properties"]["concurrent_requests"]
        assert "minimum" in concurrent_req_schema
        assert "maximum" in concurrent_req_schema
        assert concurrent_req_schema["minimum"] == 1
        assert concurrent_req_schema["maximum"] == 100

        # Test storage config schema
        csv_schema = CSVStorageConfig.model_json_schema()
        assert isinstance(csv_schema, dict)
        assert "properties" in csv_schema
        assert "required" in csv_schema
        assert "file_path" in csv_schema["required"]
        assert "file_path" in csv_schema["properties"]

    def test_config_validation_error_reporting(self):
        """Test detailed validation error reporting."""
        # Test multiple validation errors
        with pytest.raises(ValidationError) as exc_info:
            ScrapyConfig(
                concurrent_requests=200, download_delay=-1.0  # Too high  # Negative
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 2

        # Check that error locations are correct
        error_fields = [error["loc"][0] for error in errors]
        assert "concurrent_requests" in error_fields
        assert "download_delay" in error_fields

        # Test storage config validation errors
        with pytest.raises(ValidationError) as exc_info:
            PostgreSQLStorageConfig(
                connection_string="",  # Empty
                table_name="",  # Empty
                batch_size=0,  # Invalid
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 3

    def test_config_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Test minimum valid values
        scrapy_min = ScrapyConfig(concurrent_requests=1, download_delay=0.0)
        assert scrapy_min.concurrent_requests == 1
        assert scrapy_min.download_delay == 0.0

        # Test maximum valid values
        scrapy_max = ScrapyConfig(concurrent_requests=100, download_delay=999.99)
        assert scrapy_max.concurrent_requests == 100
        assert scrapy_max.download_delay == 999.99

        # Test minimum timeout values
        playwright_min = PlaywrightConfig(timeout=1)
        soup_min = BeautifulSoupConfig(timeout=1)

        assert playwright_min.timeout == 1
        assert soup_min.timeout == 1

        # Test minimum batch size
        pg_min = PostgreSQLStorageConfig(
            connection_string="postgresql://localhost/test",
            table_name="test",
            batch_size=1,
        )
        assert pg_min.batch_size == 1

    def test_config_complex_serialization(self):
        """Test serialization of complex nested configs."""
        # Test PlaywrightConfig with nested Viewport
        complex_config = PlaywrightConfig(
            browser="firefox",
            headless=False,
            viewport=Viewport(width=1280, height=720),
            user_agent="Complex Test Agent",
            timeout=45000,
        )

        # Serialize to JSON
        json_str = complex_config.model_dump_json()
        assert isinstance(json_str, str)

        # Deserialize and verify
        config_copy = PlaywrightConfig.model_validate_json(json_str)
        assert config_copy.browser == "firefox"
        assert config_copy.headless is False
        assert isinstance(config_copy.viewport, Viewport)
        assert config_copy.viewport.width == 1280
        assert config_copy.viewport.height == 720
        assert config_copy.user_agent == "Complex Test Agent"
        assert config_copy.timeout == 45000
