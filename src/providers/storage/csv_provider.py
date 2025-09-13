"""
CSV storage provider implementation.
This provider stores scraped data in CSV format using pandas for efficiency.
"""

# Standard library imports
import asyncio
import csv
import os
from pathlib import Path
from typing import Dict, List, Optional

# Third-party imports
import pandas as pd

# Local folder imports
# Local imports
from ...scraper_core.models.data_element import DataElement
from ...scraper_core.models.provider_config import ConnectionConfig, ProviderMetadata
from ...scraper_core.models.workflow import QueryCriteria, SchemaDefinition
from .base import BaseStorage


class CSVStorage(BaseStorage):
    """CSV-based storage provider using pandas for efficient data handling."""

    def __init__(self):
        super().__init__()
        self._config: Optional[ConnectionConfig] = None
        self._file_path: Optional[str] = None
        self._encoding: str = "utf-8"
        self._delimiter: str = ","
        self._include_headers: bool = True

    @property
    def metadata(self) -> ProviderMetadata:
        """Provider metadata."""
        return ProviderMetadata(
            name="csv",
            version="1.0.0",
            provider_type="storage",
            capabilities=[
                "file_storage",
                "append_mode",
                "header_management",
                "encoding_support",
                "delimiter_customization",
                "pandas_integration",
            ],
            description="CSV file storage with pandas for efficient data operations",
        )

    async def connect(self, config: ConnectionConfig) -> None:
        """Connect to CSV storage (validate file path and permissions)."""
        self._config = config

        # Extract CSV-specific configuration
        csv_config = config.get("csv", {})
        self._file_path = csv_config.get("file_path", "./scraped_data.csv")
        self._encoding = csv_config.get("encoding", "utf-8")
        self._delimiter = csv_config.get("delimiter", ",")
        self._include_headers = csv_config.get("headers", True)

        # Ensure directory exists
        file_path = Path(self._file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Test write permissions
        try:
            test_file = file_path.with_suffix(".test")
            test_file.write_text("test", encoding=self._encoding)
            test_file.unlink()
        except Exception as e:
            raise RuntimeError(f"Cannot write to CSV file path: {e}")

    async def disconnect(self) -> None:
        """Disconnect from CSV storage (cleanup)."""
        self._config = None
        self._file_path = None

    async def health_check(self) -> bool:
        """Check storage health (file accessibility)."""
        if not self._file_path:
            return False

        try:
            file_path = Path(self._file_path)
            # Check if parent directory exists and is writable
            if not file_path.parent.exists():
                return False

            # Test write access
            test_file = file_path.with_suffix(".health_check")
            test_file.write_text("health_check", encoding=self._encoding)
            test_file.unlink()
            return True
        except Exception:
            return False

    async def store(self, data: List[DataElement], schema: SchemaDefinition) -> None:
        """Store data elements to CSV file."""
        if not self._file_path:
            raise RuntimeError("CSV storage not connected")

        if not data:
            return  # Nothing to store

        # Convert DataElements to DataFrame
        records = []
        for element in data:
            record = {
                "type": element.type,
                "selector": element.selector,
                "value": element.value,
            }

            # Add attributes as separate columns with prefix
            for attr_name, attr_value in element.attributes.items():
                record[f"attr_{attr_name}"] = attr_value

            # Add metadata as separate columns with prefix
            for meta_name, meta_value in element.metadata.items():
                # Convert complex metadata to string
                if isinstance(meta_value, (dict, list)):
                    meta_value = str(meta_value)
                record[f"meta_{meta_name}"] = meta_value

            records.append(record)

        df = pd.DataFrame(records)

        # Apply schema transformations if provided
        if schema:
            df = await self._apply_schema_transformations(df, schema)

        # Write to CSV
        file_path = Path(self._file_path)
        file_exists = file_path.exists()

        try:
            if file_exists and not self._include_headers:
                # Append without headers
                df.to_csv(
                    file_path,
                    mode="a",
                    header=False,
                    index=False,
                    encoding=self._encoding,
                    sep=self._delimiter,
                    escapechar="\\",
                    quoting=csv.QUOTE_NONNUMERIC,
                )
            else:
                # Write with headers (new file or headers requested)
                df.to_csv(
                    file_path,
                    mode="w" if not file_exists else "a",
                    header=self._include_headers,
                    index=False,
                    encoding=self._encoding,
                    sep=self._delimiter,
                    escapechar="\\",
                    quoting=csv.QUOTE_NONNUMERIC,
                )
        except Exception as e:
            raise RuntimeError(f"Failed to write CSV file: {e}")

    async def query(
        self, criteria: QueryCriteria, schema: SchemaDefinition
    ) -> List[DataElement]:
        """Query data from CSV file."""
        if not self._file_path:
            raise RuntimeError("CSV storage not connected")

        file_path = Path(self._file_path)
        if not file_path.exists():
            return []  # No data file exists

        try:
            # Read CSV file
            df = pd.read_csv(
                file_path,
                encoding=self._encoding,
                sep=self._delimiter,
            )

            # Apply filters from criteria
            if criteria.filters:
                for field, value in criteria.filters.items():
                    if field in df.columns:
                        df = df[df[field] == value]

            # Apply limit
            if criteria.limit:
                df = df.head(criteria.limit)

            # Apply offset
            if criteria.offset:
                df = df.iloc[criteria.offset :]

            # Apply sorting
            if criteria.sort_by:
                ascending = criteria.sort_order != "desc"
                if criteria.sort_by in df.columns:
                    df = df.sort_values(by=criteria.sort_by, ascending=ascending)

            # Convert back to DataElements
            data_elements = []
            for _, row in df.iterrows():
                # Extract base fields
                element_type = row.get("type", "unknown")
                selector = row.get("selector", "")
                value = row.get("value", "")

                # Extract attributes (columns starting with attr_)
                attributes = {}
                for col in df.columns:
                    if col.startswith("attr_"):
                        attr_name = col[5:]  # Remove 'attr_' prefix
                        attr_value = row[col]
                        if pd.notna(attr_value):
                            attributes[attr_name] = attr_value

                # Extract metadata (columns starting with meta_)
                metadata = {}
                for col in df.columns:
                    if col.startswith("meta_"):
                        meta_name = col[5:]  # Remove 'meta_' prefix
                        meta_value = row[col]
                        if pd.notna(meta_value):
                            metadata[meta_name] = meta_value

                data_elements.append(
                    DataElement(
                        type=element_type,
                        selector=selector,
                        value=value,
                        attributes=attributes,
                        metadata=metadata,
                    )
                )

            return data_elements

        except Exception as e:
            raise RuntimeError(f"Failed to query CSV file: {e}")

    async def _apply_schema_transformations(
        self, df: pd.DataFrame, schema: SchemaDefinition
    ) -> pd.DataFrame:
        """Apply schema-based transformations to DataFrame."""
        # Create a copy to avoid modifying original
        df_transformed = df.copy()

        for field_name, field_def in schema.fields.items():
            if field_name not in df_transformed.columns:
                continue

            field_type = field_def.type

            try:
                if field_type == "string":
                    df_transformed[field_name] = df_transformed[field_name].astype(str)
                    # Apply max_length if specified
                    if field_def.max_length:
                        df_transformed[field_name] = df_transformed[field_name].str[
                            : field_def.max_length
                        ]

                elif field_type == "number":
                    df_transformed[field_name] = pd.to_numeric(
                        df_transformed[field_name], errors="coerce"
                    )

                elif field_type == "boolean":
                    # Convert to boolean
                    df_transformed[field_name] = df_transformed[field_name].astype(bool)

                elif field_type == "date":
                    # Convert to datetime
                    df_transformed[field_name] = pd.to_datetime(
                        df_transformed[field_name], errors="coerce"
                    )

                elif field_type == "json":
                    # Keep as string (JSON serialized)
                    df_transformed[field_name] = df_transformed[field_name].astype(str)

            except Exception:
                # If transformation fails, keep original values
                continue

        return df_transformed

    async def create_schema(self, schema: SchemaDefinition) -> None:
        """Create schema (for CSV, this is a no-op but validates the schema)."""
        # CSV doesn't have explicit schemas, but we validate the schema definition
        if not schema.name:
            raise ValueError("Schema name is required")

        if not schema.fields:
            raise ValueError("Schema must have at least one field")

        # Validate field definitions
        valid_types = {"string", "number", "boolean", "date", "json"}
        for field_name, field_def in schema.fields.items():
            if field_def.type not in valid_types:
                raise ValueError(
                    f"Invalid field type for {field_name}: {field_def.type}"
                )

    async def drop_schema(self, schema_name: str) -> None:
        """Drop schema (for CSV, this removes the file)."""
        if self._file_path:
            file_path = Path(self._file_path)
            if file_path.exists():
                file_path.unlink()

    async def list_schemas(self) -> List[str]:
        """List available schemas (for CSV, return file name if exists)."""
        if self._file_path:
            file_path = Path(self._file_path)
            if file_path.exists():
                return [file_path.stem]
        return []
