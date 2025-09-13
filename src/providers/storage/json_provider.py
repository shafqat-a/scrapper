"""
JSON storage provider implementation.
This provider stores scraped data in JSON and JSONL formats with streaming support.
"""

# Standard library imports
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Local folder imports
# Local imports
from ...scraper_core.models.data_element import DataElement
from ...scraper_core.models.provider_config import ConnectionConfig, ProviderMetadata
from ...scraper_core.models.workflow import QueryCriteria, SchemaDefinition
from .base import BaseStorage


class JSONStorage(BaseStorage):
    """JSON-based storage provider supporting both JSON and JSONL formats."""

    def __init__(self):
        super().__init__()
        self._config: Optional[ConnectionConfig] = None
        self._file_path: Optional[str] = None
        self._format: str = "jsonl"  # "json" or "jsonl"
        self._encoding: str = "utf-8"
        self._pretty_print: bool = False
        self._append_mode: bool = True

    @property
    def metadata(self) -> ProviderMetadata:
        """Provider metadata."""
        return ProviderMetadata(
            name="json",
            version="1.0.0",
            provider_type="storage",
            capabilities=[
                "json_storage",
                "jsonl_streaming",
                "append_mode",
                "pretty_printing",
                "nested_data",
                "schema_validation",
                "filtering",
                "sorting",
            ],
            description="JSON and JSONL file storage with streaming support for large datasets",
        )

    async def connect(self, config: ConnectionConfig) -> None:
        """Connect to JSON storage (validate file path and configuration)."""
        self._config = config

        # Extract JSON-specific configuration
        json_config = config.get("json", {})
        self._file_path = json_config.get("file_path", "./scraped_data.jsonl")
        self._format = json_config.get("format", "jsonl").lower()
        self._encoding = json_config.get("encoding", "utf-8")
        self._pretty_print = json_config.get("pretty_print", False)
        self._append_mode = json_config.get("append_mode", True)

        # Validate format
        if self._format not in ["json", "jsonl"]:
            raise ValueError(
                f"Unsupported JSON format: {self._format}. Use 'json' or 'jsonl'"
            )

        # Ensure directory exists
        file_path = Path(self._file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Test write permissions
        try:
            test_file = file_path.with_suffix(".test")
            test_file.write_text('{"test": true}', encoding=self._encoding)
            test_file.unlink()
        except Exception as e:
            raise RuntimeError(f"Cannot write to JSON file path: {e}")

    async def disconnect(self) -> None:
        """Disconnect from JSON storage (cleanup)."""
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
            test_file.write_text('{"health_check": true}', encoding=self._encoding)
            test_file.unlink()
            return True
        except Exception:
            return False

    async def store(self, data: List[DataElement], schema: SchemaDefinition) -> None:
        """Store data elements to JSON file."""
        if not self._file_path:
            raise RuntimeError("JSON storage not connected")

        if not data:
            return  # Nothing to store

        # Convert DataElements to dictionaries
        records = []
        for element in data:
            record = {
                "type": element.type,
                "selector": element.selector,
                "value": element.value,
                "attributes": element.attributes,
                "metadata": element.metadata,
                "stored_at": datetime.utcnow().isoformat(),
            }

            # Apply schema transformations if provided
            if schema:
                record = await self._apply_schema_transformations(record, schema)

            records.append(record)

        file_path = Path(self._file_path)

        try:
            if self._format == "jsonl":
                await self._store_jsonl(file_path, records)
            else:
                await self._store_json(file_path, records)
        except Exception as e:
            raise RuntimeError(f"Failed to write JSON file: {e}")

    async def query(
        self, criteria: QueryCriteria, schema: SchemaDefinition
    ) -> List[DataElement]:
        """Query data from JSON file."""
        if not self._file_path:
            raise RuntimeError("JSON storage not connected")

        file_path = Path(self._file_path)
        if not file_path.exists():
            return []  # No data file exists

        try:
            # Load data based on format
            if self._format == "jsonl":
                records = await self._load_jsonl(file_path)
            else:
                records = await self._load_json(file_path)

            # Apply filters
            if criteria.filters:
                filtered_records = []
                for record in records:
                    match = True
                    for field, value in criteria.filters.items():
                        record_value = self._get_nested_value(record, field)
                        if record_value != value:
                            match = False
                            break
                    if match:
                        filtered_records.append(record)
                records = filtered_records

            # Apply sorting
            if criteria.sort_by:

                def sort_key(record):
                    return self._get_nested_value(record, criteria.sort_by)

                records.sort(key=sort_key, reverse=(criteria.sort_order == "desc"))

            # Apply offset and limit
            if criteria.offset:
                records = records[criteria.offset :]
            if criteria.limit:
                records = records[: criteria.limit]

            # Convert records back to DataElements
            data_elements = []
            for record in records:
                data_elements.append(
                    DataElement(
                        type=record.get("type", "unknown"),
                        selector=record.get("selector", ""),
                        value=record.get("value", ""),
                        attributes=record.get("attributes", {}),
                        metadata=record.get("metadata", {}),
                    )
                )

            return data_elements

        except Exception as e:
            raise RuntimeError(f"Failed to query JSON file: {e}")

    async def create_schema(self, schema: SchemaDefinition) -> None:
        """Create schema (for JSON, this validates and stores schema metadata)."""
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

        # Store schema metadata in companion file
        if self._file_path:
            schema_file = Path(self._file_path).with_suffix(".schema.json")
            schema_data = {
                "name": schema.name,
                "fields": {
                    field_name: {
                        "type": field_def.type,
                        "required": field_def.required,
                        "max_length": field_def.max_length,
                        "index": field_def.index,
                    }
                    for field_name, field_def in schema.fields.items()
                },
                "primary_key": schema.primary_key,
                "created_at": datetime.utcnow().isoformat(),
            }

            with open(schema_file, "w", encoding=self._encoding) as f:
                json.dump(schema_data, f, indent=2 if self._pretty_print else None)

    async def drop_schema(self, schema_name: str) -> None:
        """Drop schema (remove data and schema files)."""
        if self._file_path:
            # Remove data file
            data_file = Path(self._file_path)
            if data_file.exists():
                data_file.unlink()

            # Remove schema file
            schema_file = data_file.with_suffix(".schema.json")
            if schema_file.exists():
                schema_file.unlink()

    async def list_schemas(self) -> List[str]:
        """List available schemas (check for schema files)."""
        if not self._file_path:
            return []

        base_path = Path(self._file_path).parent
        schema_files = base_path.glob("*.schema.json")

        schemas = []
        for schema_file in schema_files:
            try:
                with open(schema_file, "r", encoding=self._encoding) as f:
                    schema_data = json.load(f)
                    schemas.append(schema_data.get("name", schema_file.stem))
            except Exception:
                continue

        return schemas

    async def _store_jsonl(
        self, file_path: Path, records: List[Dict[str, Any]]
    ) -> None:
        """Store records in JSONL format."""
        mode = "a" if self._append_mode and file_path.exists() else "w"

        with open(file_path, mode, encoding=self._encoding) as f:
            for record in records:
                json_line = json.dumps(record, ensure_ascii=False, default=str)
                f.write(json_line + "\n")

    async def _store_json(self, file_path: Path, records: List[Dict[str, Any]]) -> None:
        """Store records in JSON format."""
        existing_records = []

        # Load existing data if in append mode
        if self._append_mode and file_path.exists():
            try:
                with open(file_path, "r", encoding=self._encoding) as f:
                    existing_data = json.load(f)
                    if isinstance(existing_data, list):
                        existing_records = existing_data
            except (json.JSONDecodeError, TypeError):
                existing_records = []

        # Combine existing and new records
        all_records = existing_records + records

        # Write all records
        with open(file_path, "w", encoding=self._encoding) as f:
            json.dump(
                all_records,
                f,
                ensure_ascii=False,
                indent=2 if self._pretty_print else None,
                default=str,
            )

    async def _load_jsonl(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load records from JSONL format."""
        records = []

        with open(file_path, "r", encoding=self._encoding) as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    record = json.loads(line)
                    records.append(record)
                except json.JSONDecodeError as e:
                    # Log warning but continue processing
                    print(f"Warning: Invalid JSON on line {line_num}: {e}")
                    continue

        return records

    async def _load_json(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load records from JSON format."""
        with open(file_path, "r", encoding=self._encoding) as f:
            data = json.load(f)

        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # Single record
            return [data]
        else:
            return []

    async def _apply_schema_transformations(
        self, record: Dict[str, Any], schema: SchemaDefinition
    ) -> Dict[str, Any]:
        """Apply schema-based transformations to record."""
        transformed_record = record.copy()

        for field_name, field_def in schema.fields.items():
            if field_name not in transformed_record:
                if field_def.required:
                    transformed_record[field_name] = self._get_default_value(
                        field_def.type
                    )
                continue

            value = transformed_record[field_name]
            if value is None:
                continue

            try:
                if field_def.type == "string":
                    value = str(value)
                    if field_def.max_length:
                        value = value[: field_def.max_length]

                elif field_def.type == "number":
                    if isinstance(value, str):
                        value = float(value.replace(",", ""))
                    value = float(value)

                elif field_def.type == "boolean":
                    if isinstance(value, str):
                        value = value.lower() in ["true", "1", "yes", "on"]
                    else:
                        value = bool(value)

                elif field_def.type == "date":
                    if isinstance(value, str):
                        # Keep as ISO string
                        pass
                    elif isinstance(value, datetime):
                        value = value.isoformat()
                    else:
                        value = str(value)

                elif field_def.type == "json":
                    # Ensure it's valid JSON
                    if isinstance(value, str):
                        try:
                            value = json.loads(value)
                        except json.JSONDecodeError:
                            value = value  # Keep as string

                transformed_record[field_name] = value

            except (ValueError, TypeError):
                # Keep original value if transformation fails
                continue

        return transformed_record

    def _get_default_value(self, field_type: str) -> Any:
        """Get default value for a field type."""
        defaults = {
            "string": "",
            "number": 0,
            "boolean": False,
            "date": datetime.utcnow().isoformat(),
            "json": {},
        }
        return defaults.get(field_type, None)

    def _get_nested_value(self, record: Dict[str, Any], field_path: str) -> Any:
        """Get nested value from record using dot notation (e.g., 'metadata.tag')."""
        keys = field_path.split(".")
        value = record

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None

        return value
