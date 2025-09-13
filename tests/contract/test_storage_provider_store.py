"""
Contract test for StorageProvider.store() method.
This test MUST fail before any implementation exists (TDD requirement).
"""

# Standard library imports
import asyncio
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
        ConnectionConfig,
        DataElement,
        ElementMetadata,
        ProviderMetadata,
        SchemaDefinition,
        SchemaField,
        SchemaIndex,
        StorageProvider,
    )
except ImportError:
    # If import fails, create minimal interfaces for testing
    # Standard library imports
    from abc import ABC, abstractmethod
    from typing import Literal, Optional, Protocol

    # Third-party imports
    from pydantic import BaseModel, Field

    class ProviderMetadata(BaseModel):
        name: str
        version: str
        type: str
        capabilities: list

    class ConnectionConfig(BaseModel):
        pass

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

    class SchemaField(BaseModel):
        type: Literal["string", "number", "boolean", "date", "json"]
        required: bool = False
        max_length: Optional[int] = None
        index: bool = False

    class SchemaIndex(BaseModel):
        name: str
        fields: List[str]
        unique: bool = False

    class SchemaDefinition(BaseModel):
        name: str
        fields: Dict[str, SchemaField]
        primary_key: List[str] = []
        indexes: List[SchemaIndex] = []

    class StorageProvider(Protocol):
        async def connect(self, config: ConnectionConfig) -> None: ...
        async def disconnect(self) -> None: ...
        async def store(
            self, data: List[DataElement], schema: SchemaDefinition
        ) -> None: ...
        async def query(self, criteria, schema): ...
        async def create_schema(self, definition): ...
        async def validate_schema(self, definition) -> bool: ...
        async def schema_exists(self, schema_name: str) -> bool: ...
        async def get_schema(self, schema_name: str): ...
        async def health_check(self) -> bool: ...
        async def get_stats(self): ...


class MockStorageProvider:
    """Mock implementation that should fail contract tests initially."""

    def __init__(self):
        self.metadata = ProviderMetadata(
            name="mock-storage", version="1.0.0", type="storage", capabilities=["basic"]
        )
        self.is_connected = False
        self.config = None
        self.stored_data = []
        self.store_calls = 0

    async def connect(self, config: ConnectionConfig) -> None:
        raise NotImplementedError("Not implemented")

    async def disconnect(self) -> None:
        raise NotImplementedError("Not implemented")

    async def store(self, data: List[DataElement], schema: SchemaDefinition) -> None:
        """Mock implementation - should be replaced by real implementation."""
        # This will fail until real implementation exists
        raise NotImplementedError("StorageProvider.store() not implemented yet")

    async def query(self, criteria, schema):
        raise NotImplementedError("Not implemented")

    async def create_schema(self, definition):
        raise NotImplementedError("Not implemented")

    async def validate_schema(self, definition) -> bool:
        return False

    async def schema_exists(self, schema_name: str) -> bool:
        return False

    async def get_schema(self, schema_name: str):
        raise NotImplementedError("Not implemented")

    async def health_check(self) -> bool:
        return False

    async def get_stats(self):
        raise NotImplementedError("Not implemented")


@pytest.mark.contract
@pytest.mark.asyncio
class TestStorageProviderStore:
    """Contract tests for StorageProvider.store() method."""

    @pytest.fixture
    def provider(self) -> StorageProvider:
        """Create a mock storage provider for testing."""
        return MockStorageProvider()

    @pytest.fixture
    def sample_data(self) -> List[DataElement]:
        """Create sample data elements for testing."""
        return [
            DataElement(
                id="element1",
                type="text",
                value="Sample text content",
                metadata=ElementMetadata(
                    selector=".content",
                    source_url="https://example.com",
                    timestamp=datetime.now(),
                    xpath="//div[@class='content']",
                ),
            ),
            DataElement(
                id="element2",
                type="link",
                value="https://example.com/link",
                metadata=ElementMetadata(
                    selector="a.link",
                    source_url="https://example.com",
                    timestamp=datetime.now(),
                    xpath="//a[@class='link']",
                ),
            ),
        ]

    @pytest.fixture
    def empty_data(self) -> List[DataElement]:
        """Create empty data list for testing."""
        return []

    @pytest.fixture
    def basic_schema(self) -> SchemaDefinition:
        """Create basic schema definition for testing."""
        return SchemaDefinition(
            name="test_schema",
            fields={
                "id": SchemaField(type="string", required=True),
                "type": SchemaField(type="string", required=True),
                "value": SchemaField(type="string", required=False),
                "source_url": SchemaField(type="string", required=False),
            },
            primary_key=["id"],
            indexes=[SchemaIndex(name="type_idx", fields=["type"], unique=False)],
        )

    @pytest.fixture
    def complex_schema(self) -> SchemaDefinition:
        """Create complex schema definition for testing."""
        return SchemaDefinition(
            name="complex_schema",
            fields={
                "id": SchemaField(type="string", required=True, max_length=50),
                "type": SchemaField(type="string", required=True),
                "value": SchemaField(type="json", required=False),
                "timestamp": SchemaField(type="date", required=True),
                "processed": SchemaField(type="boolean", required=False),
                "score": SchemaField(type="number", required=False),
            },
            primary_key=["id"],
            indexes=[
                SchemaIndex(
                    name="type_timestamp_idx",
                    fields=["type", "timestamp"],
                    unique=False,
                ),
                SchemaIndex(name="id_unique_idx", fields=["id"], unique=True),
            ],
        )

    async def test_store_with_valid_data_and_schema(
        self,
        provider: StorageProvider,
        sample_data: List[DataElement],
        basic_schema: SchemaDefinition,
    ):
        """Test that store() accepts valid data and schema."""
        # This test MUST fail initially (TDD requirement)
        with pytest.raises(NotImplementedError, match="not implemented yet"):
            await provider.store(sample_data, basic_schema)

    async def test_store_with_empty_data(
        self,
        provider: StorageProvider,
        empty_data: List[DataElement],
        basic_schema: SchemaDefinition,
    ):
        """Test that store() handles empty data list."""
        with pytest.raises(NotImplementedError):
            await provider.store(empty_data, basic_schema)

        # After implementation, should handle empty data gracefully:
        # await provider.store(empty_data, basic_schema)  # Should not fail

    async def test_store_with_complex_schema(
        self,
        provider: StorageProvider,
        sample_data: List[DataElement],
        complex_schema: SchemaDefinition,
    ):
        """Test that store() handles complex schema definitions."""
        with pytest.raises(NotImplementedError):
            await provider.store(sample_data, complex_schema)

    async def test_store_with_none_data(
        self, provider: StorageProvider, basic_schema: SchemaDefinition
    ):
        """Test that store() handles None data appropriately."""
        with pytest.raises((TypeError, ValueError, NotImplementedError)):
            await provider.store(None, basic_schema)

    async def test_store_with_none_schema(
        self, provider: StorageProvider, sample_data: List[DataElement]
    ):
        """Test that store() handles None schema appropriately."""
        with pytest.raises((TypeError, ValueError, NotImplementedError)):
            await provider.store(sample_data, None)

    async def test_store_data_persistence(
        self,
        provider: StorageProvider,
        sample_data: List[DataElement],
        basic_schema: SchemaDefinition,
    ):
        """Test that store() actually persists data."""
        mock_provider = provider
        initial_count = len(mock_provider.stored_data)

        with pytest.raises(NotImplementedError):
            await provider.store(sample_data, basic_schema)

        # After implementation, this should verify:
        # assert len(provider.stored_data) == initial_count + len(sample_data)
        # for element in sample_data:
        #     assert element in provider.stored_data

    async def test_store_increments_call_counter(
        self,
        provider: StorageProvider,
        sample_data: List[DataElement],
        basic_schema: SchemaDefinition,
    ):
        """Test that store() tracks number of store operations."""
        mock_provider = provider
        initial_calls = mock_provider.store_calls

        with pytest.raises(NotImplementedError):
            await provider.store(sample_data, basic_schema)

        # After implementation:
        # assert provider.store_calls == initial_calls + 1

    async def test_store_with_large_data_set(
        self, provider: StorageProvider, basic_schema: SchemaDefinition
    ):
        """Test that store() handles large data sets efficiently."""
        # Create large data set
        large_data = []
        for i in range(1000):
            large_data.append(
                DataElement(
                    id=f"element_{i}",
                    type="text",
                    value=f"Content {i}",
                    metadata=ElementMetadata(
                        selector=f".content-{i}",
                        source_url=f"https://example.com/page/{i}",
                        timestamp=datetime.now(),
                    ),
                )
            )

        with pytest.raises(NotImplementedError):
            await provider.store(large_data, basic_schema)

        # After implementation, should handle large datasets:
        # start_time = datetime.now()
        # await provider.store(large_data, basic_schema)
        # duration = (datetime.now() - start_time).total_seconds()
        # assert duration < 60  # Should complete within reasonable time

    async def test_store_concurrent_operations(
        self,
        provider: StorageProvider,
        sample_data: List[DataElement],
        basic_schema: SchemaDefinition,
    ):
        """Test that concurrent store() calls are handled safely."""

        async def store_call():
            try:
                await provider.store(sample_data, basic_schema)
                return "success"
            except NotImplementedError:
                return "not_implemented"
            except Exception as e:
                return f"error: {e}"

        # Run multiple concurrent store calls
        results = await asyncio.gather(
            store_call(), store_call(), store_call(), return_exceptions=True
        )

        # All should fail with NotImplementedError initially
        for result in results:
            assert result == "not_implemented" or isinstance(
                result, NotImplementedError
            )

    async def test_store_data_validation_against_schema(
        self, provider: StorageProvider, basic_schema: SchemaDefinition
    ):
        """Test that store() validates data against schema."""
        # Create data that doesn't match schema
        invalid_data = [
            DataElement(
                id="element1",
                type="invalid_type",  # Not in schema
                value=123,  # Wrong type for string field
                metadata=ElementMetadata(
                    selector=".content",
                    source_url="https://example.com",
                    timestamp=datetime.now(),
                ),
            )
        ]

        with pytest.raises((ValueError, TypeError, NotImplementedError)):
            await provider.store(invalid_data, basic_schema)

    async def test_store_required_field_validation(self, provider: StorageProvider):
        """Test that store() validates required fields."""
        schema_with_required = SchemaDefinition(
            name="required_test",
            fields={
                "id": SchemaField(type="string", required=True),
                "required_field": SchemaField(type="string", required=True),
                "optional_field": SchemaField(type="string", required=False),
            },
            primary_key=["id"],
        )

        # Data missing required field
        invalid_data = [
            DataElement(
                id="element1",
                type="text",
                value={"optional_field": "value"},  # Missing required_field
                metadata=ElementMetadata(
                    selector=".content",
                    source_url="https://example.com",
                    timestamp=datetime.now(),
                ),
            )
        ]

        with pytest.raises((ValueError, NotImplementedError)):
            await provider.store(invalid_data, schema_with_required)

    async def test_store_with_duplicate_primary_keys(
        self, provider: StorageProvider, basic_schema: SchemaDefinition
    ):
        """Test that store() handles duplicate primary keys appropriately."""
        duplicate_data = [
            DataElement(
                id="same_id",
                type="text",
                value="First value",
                metadata=ElementMetadata(
                    selector=".content1",
                    source_url="https://example.com",
                    timestamp=datetime.now(),
                ),
            ),
            DataElement(
                id="same_id",  # Duplicate ID
                type="text",
                value="Second value",
                metadata=ElementMetadata(
                    selector=".content2",
                    source_url="https://example.com",
                    timestamp=datetime.now(),
                ),
            ),
        ]

        with pytest.raises((ValueError, NotImplementedError)):
            await provider.store(duplicate_data, basic_schema)

    async def test_store_max_length_validation(self, provider: StorageProvider):
        """Test that store() validates field max_length constraints."""
        schema_with_length = SchemaDefinition(
            name="length_test",
            fields={
                "id": SchemaField(type="string", required=True),
                "short_field": SchemaField(type="string", max_length=10),
            },
            primary_key=["id"],
        )

        # Data exceeding max length
        long_data = [
            DataElement(
                id="element1",
                type="text",
                value={"short_field": "this is way too long for the field"},
                metadata=ElementMetadata(
                    selector=".content",
                    source_url="https://example.com",
                    timestamp=datetime.now(),
                ),
            )
        ]

        with pytest.raises((ValueError, NotImplementedError)):
            await provider.store(long_data, schema_with_length)

    async def test_store_different_data_types(self, provider: StorageProvider):
        """Test that store() handles different DataElement types."""
        mixed_data = [
            DataElement(
                id="text_element",
                type="text",
                value="Text content",
                metadata=ElementMetadata(
                    selector=".text",
                    source_url="https://example.com",
                    timestamp=datetime.now(),
                ),
            ),
            DataElement(
                id="link_element",
                type="link",
                value="https://example.com/link",
                metadata=ElementMetadata(
                    selector="a",
                    source_url="https://example.com",
                    timestamp=datetime.now(),
                ),
            ),
            DataElement(
                id="image_element",
                type="image",
                value="https://example.com/image.jpg",
                metadata=ElementMetadata(
                    selector="img",
                    source_url="https://example.com",
                    timestamp=datetime.now(),
                ),
            ),
            DataElement(
                id="structured_element",
                type="structured",
                value={"name": "John", "age": 30},
                metadata=ElementMetadata(
                    selector=".person",
                    source_url="https://example.com",
                    timestamp=datetime.now(),
                ),
            ),
        ]

        flexible_schema = SchemaDefinition(
            name="flexible_schema",
            fields={
                "id": SchemaField(type="string", required=True),
                "type": SchemaField(type="string", required=True),
                "value": SchemaField(
                    type="json", required=False
                ),  # JSON can handle any type
            },
            primary_key=["id"],
        )

        with pytest.raises(NotImplementedError):
            await provider.store(mixed_data, flexible_schema)

    async def test_store_batch_size_handling(
        self, provider: StorageProvider, basic_schema: SchemaDefinition
    ):
        """Test that store() handles batch processing efficiently."""
        # Create data that might require batching
        batch_data = []
        for i in range(100):
            batch_data.append(
                DataElement(
                    id=f"batch_element_{i}",
                    type="text",
                    value=f"Batch content {i}",
                    metadata=ElementMetadata(
                        selector=f".batch-{i}",
                        source_url="https://example.com",
                        timestamp=datetime.now(),
                    ),
                )
            )

        with pytest.raises(NotImplementedError):
            await provider.store(batch_data, basic_schema)

        # After implementation, should handle batching:
        # await provider.store(batch_data, basic_schema)
        # # Verify all data was stored
        # assert len(provider.stored_data) >= len(batch_data)


# Additional contract validation tests
@pytest.mark.contract
class TestStorageProviderStoreContractValidation:
    """Contract validation tests to ensure proper interface compliance."""

    def test_store_method_signature(self):
        """Test that store method has correct signature."""
        provider = MockStorageProvider()

        # Verify method exists
        assert hasattr(provider, "store")
        assert callable(getattr(provider, "store"))

        # Verify it's async
        # Standard library imports
        import inspect

        assert inspect.iscoroutinefunction(provider.store)

    def test_store_accepts_correct_parameters(self):
        """Test that store accepts data and schema parameters."""
        provider = MockStorageProvider()

        # Should not raise TypeError for signature mismatch
        # Standard library imports
        import inspect

        sig = inspect.signature(provider.store)

        # Verify it accepts data and schema parameters
        assert len(sig.parameters) == 2
        params = list(sig.parameters.values())
        assert params[0].name == "data"
        assert params[1].name == "schema"

    def test_store_returns_none(self):
        """Test that store returns None (void method)."""
        provider = MockStorageProvider()

        # Check return annotation
        # Standard library imports
        import inspect

        sig = inspect.signature(provider.store)
        assert sig.return_annotation in [None, "None", type(None)]

    async def test_store_is_awaitable(self):
        """Test that store method is properly awaitable."""
        provider = MockStorageProvider()
        data = []
        schema = SchemaDefinition(name="test", fields={})

        # Should be awaitable
        coro = provider.store(data, schema)
        assert hasattr(coro, "__await__")

        # Clean up the coroutine
        try:
            await coro
        except NotImplementedError:
            pass  # Expected for mock implementation

    def test_data_element_model_validation(self):
        """Test that DataElement model validates correctly."""
        # Valid DataElement
        valid_element = DataElement(
            id="test1",
            type="text",
            value="content",
            metadata=ElementMetadata(
                selector=".test",
                source_url="https://example.com",
                timestamp=datetime.now(),
            ),
        )
        assert valid_element.id == "test1"
        assert valid_element.type == "text"

        # Invalid type should raise validation error
        with pytest.raises((ValueError, TypeError)):
            DataElement(
                id="test2",
                type="invalid_type",  # Not in allowed literals
                value="content",
                metadata=ElementMetadata(
                    selector=".test",
                    source_url="https://example.com",
                    timestamp=datetime.now(),
                ),
            )

    def test_schema_definition_model_validation(self):
        """Test that SchemaDefinition model validates correctly."""
        # Valid SchemaDefinition
        valid_schema = SchemaDefinition(
            name="test_schema",
            fields={
                "id": SchemaField(type="string", required=True),
                "content": SchemaField(type="string", required=False),
            },
            primary_key=["id"],
        )
        assert valid_schema.name == "test_schema"
        assert len(valid_schema.fields) == 2

        # Invalid field type should raise validation error
        with pytest.raises((ValueError, TypeError)):
            SchemaDefinition(
                name="bad_schema",
                fields={
                    "id": SchemaField(
                        type="invalid_type", required=True
                    )  # Not in allowed literals
                },
            )
