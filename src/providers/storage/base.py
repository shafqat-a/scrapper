"""
StorageProvider protocol and base class implementation.
This module defines the interface and abstract base class for all storage providers.
"""

# Standard library imports
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Protocol

# Local imports
from ...scraper_core.models import (
    DataElement,
    SchemaDefinition,
    ConnectionConfig,
)


class QueryCriteria:
    """Query criteria for storage operations."""

    def __init__(
        self,
        where: Optional[Dict] = None,
        order_by: Optional[List[Dict[str, str]]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ):
        self.where = where or {}
        self.order_by = order_by or []
        self.limit = limit
        self.offset = offset


class StorageStats:
    """Storage statistics and metrics."""

    def __init__(self, total_records: int, last_updated: datetime, storage_size: Optional[int] = None):
        self.total_records = total_records
        self.last_updated = last_updated
        self.storage_size = storage_size


class ProviderMetadata:
    """Metadata for provider instances."""

    def __init__(self, name: str, version: str, provider_type: str, capabilities: List[str]):
        self.name = name
        self.version = version
        self.type = provider_type
        self.capabilities = capabilities


class StorageProvider(Protocol):
    """Protocol defining the interface for storage providers."""

    metadata: ProviderMetadata

    async def connect(self, config: ConnectionConfig) -> None:
        """Establish connection to storage backend."""
        ...

    async def disconnect(self) -> None:
        """Disconnect from storage backend."""
        ...

    async def store(self, data: List[DataElement], schema: SchemaDefinition) -> None:
        """Store data elements according to schema."""
        ...

    async def query(
        self, criteria: QueryCriteria, schema: SchemaDefinition
    ) -> List[DataElement]:
        """Query stored data."""
        ...

    async def create_schema(self, definition: SchemaDefinition) -> None:
        """Create schema/table structure."""
        ...

    async def validate_schema(self, definition: SchemaDefinition) -> bool:
        """Validate schema definition."""
        ...

    async def schema_exists(self, schema_name: str) -> bool:
        """Check if schema exists."""
        ...

    async def get_schema(self, schema_name: str) -> SchemaDefinition:
        """Get schema information."""
        ...

    async def health_check(self) -> bool:
        """Health check for storage connectivity."""
        ...

    async def get_stats(self) -> StorageStats:
        """Get storage statistics."""
        ...


class BaseStorage(ABC):
    """Abstract base class for storage providers."""

    def __init__(self):
        self.metadata = ProviderMetadata(
            name="base-storage",
            version="1.0.0",
            provider_type="storage",
            capabilities=[]
        )

    @abstractmethod
    async def connect(self, config: ConnectionConfig) -> None:
        """Establish connection to storage backend."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from storage backend."""
        pass

    @abstractmethod
    async def store(self, data: List[DataElement], schema: SchemaDefinition) -> None:
        """Store data elements according to schema."""
        pass

    @abstractmethod
    async def query(
        self, criteria: QueryCriteria, schema: SchemaDefinition
    ) -> List[DataElement]:
        """Query stored data."""
        pass

    @abstractmethod
    async def create_schema(self, definition: SchemaDefinition) -> None:
        """Create schema/table structure."""
        pass

    async def validate_schema(self, definition: SchemaDefinition) -> bool:
        """Default schema validation."""
        return True

    async def schema_exists(self, schema_name: str) -> bool:
        """Default schema existence check."""
        return False

    async def get_schema(self, schema_name: str) -> SchemaDefinition:
        """Default get schema implementation."""
        raise NotImplementedError("Schema retrieval not implemented")

    async def health_check(self) -> bool:
        """Default health check."""
        return True

    async def get_stats(self) -> StorageStats:
        """Default stats implementation."""
        return StorageStats(total_records=0, last_updated=datetime.now())