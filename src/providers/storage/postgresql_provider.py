"""
PostgreSQL storage provider implementation.
This provider stores scraped data in PostgreSQL database using asyncpg and SQLAlchemy.
"""

# Standard library imports
import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

# Third-party imports
import asyncpg
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.sql import delete, insert, select

# Local folder imports
# Local imports
from ...scraper_core.models.data_element import DataElement
from ...scraper_core.models.provider_config import ConnectionConfig, ProviderMetadata
from ...scraper_core.models.workflow import QueryCriteria, SchemaDefinition, SchemaField
from .base import BaseStorage


class PostgreSQLStorage(BaseStorage):
    """PostgreSQL-based storage provider with async support."""

    def __init__(self):
        super().__init__()
        self._config: Optional[ConnectionConfig] = None
        self._engine: Optional[AsyncEngine] = None
        self._connection: Optional[asyncpg.Connection] = None
        self._metadata: MetaData = MetaData()
        self._tables: Dict[str, Table] = {}

    @property
    def metadata(self) -> ProviderMetadata:
        """Provider metadata."""
        return ProviderMetadata(
            name="postgresql",
            version="1.0.0",
            provider_type="storage",
            capabilities=[
                "relational_storage",
                "transactions",
                "indexes",
                "json_support",
                "concurrent_access",
                "schema_management",
                "complex_queries",
                "foreign_keys",
            ],
            description="PostgreSQL database storage with async support and JSON capabilities",
        )

    async def connect(self, config: ConnectionConfig) -> None:
        """Connect to PostgreSQL database."""
        self._config = config

        # Extract PostgreSQL-specific configuration
        pg_config = config.get("postgresql", {})

        # Build connection string
        host = pg_config.get("host", "localhost")
        port = pg_config.get("port", 5432)
        database = pg_config.get("database", "scrapper")
        username = pg_config.get("username", "postgres")
        password = pg_config.get("password", "")

        if "connection_string" in pg_config:
            connection_string = pg_config["connection_string"]
        else:
            connection_string = (
                f"postgresql://{username}:{password}@{host}:{port}/{database}"
            )

        # Create async engine
        async_connection_string = connection_string.replace(
            "postgresql://", "postgresql+asyncpg://"
        )

        self._engine = create_async_engine(
            async_connection_string,
            pool_size=pg_config.get("pool_size", 10),
            max_overflow=pg_config.get("max_overflow", 20),
            pool_timeout=pg_config.get("pool_timeout", 30),
            echo=pg_config.get("echo", False),
        )

        # Test connection
        try:
            async with self._engine.begin() as conn:
                await conn.execute("SELECT 1")
        except Exception as e:
            raise RuntimeError(f"Failed to connect to PostgreSQL: {e}")

    async def disconnect(self) -> None:
        """Disconnect from PostgreSQL database."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None

        if self._connection:
            await self._connection.close()
            self._connection = None

        self._config = None
        self._tables.clear()

    async def health_check(self) -> bool:
        """Check database health."""
        if not self._engine:
            return False

        try:
            async with self._engine.begin() as conn:
                result = await conn.execute("SELECT 1")
                return result.fetchone() is not None
        except Exception:
            return False

    async def store(self, data: List[DataElement], schema: SchemaDefinition) -> None:
        """Store data elements in PostgreSQL table."""
        if not self._engine:
            raise RuntimeError("PostgreSQL storage not connected")

        if not data:
            return  # Nothing to store

        # Ensure schema/table exists
        await self._ensure_schema_exists(schema)

        # Get the table
        table = self._tables[schema.name]

        # Prepare records for insertion
        records = []
        for element in data:
            record = {
                "element_type": element.type,
                "selector": element.selector,
                "value": str(element.value) if element.value is not None else None,
                "attributes": (
                    json.dumps(element.attributes) if element.attributes else "{}"
                ),
                "metadata": json.dumps(element.metadata) if element.metadata else "{}",
                "created_at": datetime.utcnow(),
            }

            # Add schema-defined fields if they exist in the data
            for field_name, field_def in schema.fields.items():
                if field_name in [
                    "element_type",
                    "selector",
                    "value",
                    "attributes",
                    "metadata",
                    "created_at",
                ]:
                    continue  # Skip reserved fields

                # Try to extract value from element data
                value = self._extract_field_value(element, field_name)
                if value is not None:
                    # Apply type conversion based on schema
                    converted_value = self._convert_value(value, field_def)
                    record[field_name] = converted_value

            records.append(record)

        # Insert records
        async with self._engine.begin() as conn:
            try:
                await conn.execute(insert(table), records)
            except Exception as e:
                raise RuntimeError(f"Failed to insert data into PostgreSQL: {e}")

    async def query(
        self, criteria: QueryCriteria, schema: SchemaDefinition
    ) -> List[DataElement]:
        """Query data from PostgreSQL table."""
        if not self._engine:
            raise RuntimeError("PostgreSQL storage not connected")

        # Ensure schema/table exists
        await self._ensure_schema_exists(schema)

        # Get the table
        table = self._tables[schema.name]

        # Build query
        query = select(table)

        # Apply filters
        if criteria.filters:
            for field, value in criteria.filters.items():
                if hasattr(table.c, field):
                    query = query.where(table.c[field] == value)

        # Apply sorting
        if criteria.sort_by and hasattr(table.c, criteria.sort_by):
            if criteria.sort_order == "desc":
                query = query.order_by(table.c[criteria.sort_by].desc())
            else:
                query = query.order_by(table.c[criteria.sort_by])

        # Apply offset and limit
        if criteria.offset:
            query = query.offset(criteria.offset)
        if criteria.limit:
            query = query.limit(criteria.limit)

        # Execute query
        async with self._engine.begin() as conn:
            try:
                result = await conn.execute(query)
                rows = result.fetchall()

                # Convert rows to DataElements
                data_elements = []
                for row in rows:
                    # Parse JSON fields
                    attributes = json.loads(row.attributes) if row.attributes else {}
                    metadata = json.loads(row.metadata) if row.metadata else {}

                    # Add database metadata
                    metadata.update(
                        {
                            "stored_at": (
                                row.created_at.isoformat()
                                if hasattr(row, "created_at")
                                else None
                            ),
                            "table_name": schema.name,
                        }
                    )

                    data_elements.append(
                        DataElement(
                            type=row.element_type,
                            selector=row.selector,
                            value=row.value,
                            attributes=attributes,
                            metadata=metadata,
                        )
                    )

                return data_elements

            except Exception as e:
                raise RuntimeError(f"Failed to query PostgreSQL: {e}")

    async def create_schema(self, schema: SchemaDefinition) -> None:
        """Create table based on schema definition."""
        if not self._engine:
            raise RuntimeError("PostgreSQL storage not connected")

        # Build table definition
        columns = [
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("element_type", String(100), nullable=False),
            Column("selector", Text, nullable=False),
            Column("value", Text),
            Column("attributes", JSONB, default="{}"),
            Column("metadata", JSONB, default="{}"),
            Column("created_at", DateTime, default=datetime.utcnow, nullable=False),
        ]

        # Add schema-defined columns
        for field_name, field_def in schema.fields.items():
            if field_name in [
                "id",
                "element_type",
                "selector",
                "value",
                "attributes",
                "metadata",
                "created_at",
            ]:
                continue  # Skip reserved column names

            column = self._create_column(field_name, field_def)
            if column:
                columns.append(column)

        # Create table
        table = Table(schema.name, self._metadata, *columns)

        # Store table reference
        self._tables[schema.name] = table

        # Create table in database
        async with self._engine.begin() as conn:
            try:
                await conn.run_sync(self._metadata.create_all, bind=conn.engine)

                # Create indexes if specified
                for field_name, field_def in schema.fields.items():
                    if field_def.index and field_name not in ["id"]:
                        index_name = f"idx_{schema.name}_{field_name}"
                        await conn.execute(
                            f"CREATE INDEX IF NOT EXISTS {index_name} ON {schema.name} ({field_name})"
                        )

            except Exception as e:
                raise RuntimeError(f"Failed to create PostgreSQL schema: {e}")

    async def drop_schema(self, schema_name: str) -> None:
        """Drop table from database."""
        if not self._engine:
            raise RuntimeError("PostgreSQL storage not connected")

        async with self._engine.begin() as conn:
            try:
                await conn.execute(f"DROP TABLE IF EXISTS {schema_name} CASCADE")
                if schema_name in self._tables:
                    del self._tables[schema_name]
            except Exception as e:
                raise RuntimeError(f"Failed to drop PostgreSQL schema: {e}")

    async def list_schemas(self) -> List[str]:
        """List available tables in database."""
        if not self._engine:
            raise RuntimeError("PostgreSQL storage not connected")

        async with self._engine.begin() as conn:
            try:
                result = await conn.execute(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_type = 'BASE TABLE'
                """
                )
                tables = [row[0] for row in result.fetchall()]
                return tables
            except Exception as e:
                raise RuntimeError(f"Failed to list PostgreSQL schemas: {e}")

    async def _ensure_schema_exists(self, schema: SchemaDefinition) -> None:
        """Ensure the schema/table exists in the database."""
        if schema.name not in self._tables:
            # Check if table exists in database
            async with self._engine.begin() as conn:
                result = await conn.execute(
                    f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_name = '{schema.name}'
                    )
                """
                )
                table_exists = result.fetchone()[0]

                if not table_exists:
                    # Create the schema/table
                    await self.create_schema(schema)
                else:
                    # Load existing table definition
                    table = Table(
                        schema.name,
                        self._metadata,
                        autoload=True,
                        autoload_with=conn.engine,
                    )
                    self._tables[schema.name] = table

    def _create_column(
        self, field_name: str, field_def: SchemaField
    ) -> Optional[Column]:
        """Create SQLAlchemy column from schema field definition."""
        column_type = None
        column_args = {}

        if field_def.type == "string":
            if field_def.max_length:
                column_type = String(field_def.max_length)
            else:
                column_type = Text()
        elif field_def.type == "number":
            column_type = Integer()
        elif field_def.type == "boolean":
            column_type = String(10)  # Store as 'true'/'false'
        elif field_def.type == "date":
            column_type = DateTime()
        elif field_def.type == "json":
            column_type = JSONB()

        if not column_type:
            return None

        column_args["nullable"] = not field_def.required

        return Column(field_name, column_type, **column_args)

    def _extract_field_value(self, element: DataElement, field_name: str) -> Any:
        """Extract field value from DataElement."""
        # Try to get value from attributes first
        if field_name in element.attributes:
            return element.attributes[field_name]

        # Try to get value from metadata
        if field_name in element.metadata:
            return element.metadata[field_name]

        # Check if it's the main value field
        if field_name in ["value", "text", "content"]:
            return element.value

        return None

    def _convert_value(self, value: Any, field_def: SchemaField) -> Any:
        """Convert value to the appropriate type based on schema field definition."""
        if value is None:
            return None

        try:
            if field_def.type == "string":
                return str(value)
            elif field_def.type == "number":
                return int(float(str(value).replace(",", "")))
            elif field_def.type == "boolean":
                if isinstance(value, bool):
                    return "true" if value else "false"
                return (
                    "true"
                    if str(value).lower() in ["true", "1", "yes", "on"]
                    else "false"
                )
            elif field_def.type == "date":
                if isinstance(value, datetime):
                    return value
                # Try to parse as ISO date string
                return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            elif field_def.type == "json":
                if isinstance(value, (dict, list)):
                    return value
                return json.loads(str(value))
            else:
                return str(value)
        except (ValueError, TypeError, json.JSONDecodeError):
            # Return None for invalid conversions if field is not required
            return None if not field_def.required else str(value)
