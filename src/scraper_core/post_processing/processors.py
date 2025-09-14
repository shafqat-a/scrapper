"""
Post-processing implementations for data transformation and cleanup.
"""

import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set
from ..models.data_element import DataElement


class PostProcessor(ABC):
    """Abstract base class for post-processors."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    def process(self, items: List[DataElement]) -> List[DataElement]:
        """Process a list of data elements."""
        pass


class FilterProcessor(PostProcessor):
    """Filter processor to remove unwanted items."""

    def process(self, items: List[DataElement]) -> List[DataElement]:
        """Filter items based on configuration."""
        filtered_items = []

        min_length = self.config.get("min_length", 0)
        excludes = self.config.get("excludes", "")
        required_fields = self.config.get("required_fields", [])
        exclude_empty = self.config.get("exclude_empty", True)
        exclude_headers = self.config.get("exclude_headers", False)

        for item in items:
            # Skip if item doesn't have required fields
            if required_fields:
                if not all(field in item.data for field in required_fields):
                    continue

            # Check minimum length for text fields
            if min_length > 0:
                text_fields = [str(v) for v in item.data.values() if isinstance(v, str)]
                if not any(len(field) >= min_length for field in text_fields):
                    continue

            # Exclude items containing specific text
            if excludes:
                item_text = " ".join(str(v) for v in item.data.values())
                if excludes.lower() in item_text.lower():
                    continue

            # Exclude empty items
            if exclude_empty:
                if not any(str(v).strip() for v in item.data.values()):
                    continue

            # Exclude header rows (simple heuristic)
            if exclude_headers:
                # Skip rows that look like headers
                text_values = [str(v).lower() for v in item.data.values()]
                header_indicators = ["date", "time", "generation", "demand", "mw", "column"]
                if any(indicator in " ".join(text_values) for indicator in header_indicators):
                    continue

            filtered_items.append(item)

        return filtered_items


class TransformProcessor(PostProcessor):
    """Transform processor for data cleanup and normalization."""

    def process(self, items: List[DataElement]) -> List[DataElement]:
        """Transform items based on configuration."""
        transformed_items = []

        strip = self.config.get("strip", True)
        replace_rules = self.config.get("replace", {})
        lowercase = self.config.get("lowercase", False)

        for item in items:
            transformed_data = {}

            for key, value in item.data.items():
                if isinstance(value, str):
                    # Strip whitespace
                    if strip:
                        value = value.strip()

                    # Apply replacement rules
                    for old, new in replace_rules.items():
                        value = value.replace(old, new)

                    # Convert to lowercase
                    if lowercase:
                        value = value.lower()

                transformed_data[key] = value

            # Create new item with transformed data
            transformed_item = DataElement(
                id=item.id,
                source_url=item.source_url,
                scraped_at=item.scraped_at,
                data=transformed_data,
                metadata=item.metadata
            )
            transformed_items.append(transformed_item)

        return transformed_items


class ValidateProcessor(PostProcessor):
    """Validate processor for data quality checks."""

    def process(self, items: List[DataElement]) -> List[DataElement]:
        """Validate items based on configuration."""
        validated_items = []

        required = self.config.get("required", False)
        min_length = self.config.get("min_length", 0)
        data_types = self.config.get("data_types", {})

        for item in items:
            is_valid = True

            # Check if required fields are present
            if required:
                if not item.data:
                    is_valid = False

            # Check minimum length
            if min_length > 0:
                text_content = " ".join(str(v) for v in item.data.values())
                if len(text_content.strip()) < min_length:
                    is_valid = False

            # Validate data types
            for field, expected_type in data_types.items():
                if field in item.data:
                    value = item.data[field]
                    if expected_type == "float":
                        try:
                            float(value)
                        except (ValueError, TypeError):
                            is_valid = False
                            break
                    elif expected_type == "int":
                        try:
                            int(value)
                        except (ValueError, TypeError):
                            is_valid = False
                            break

            if is_valid:
                validated_items.append(item)

        return validated_items


class DeduplicateProcessor(PostProcessor):
    """Deduplicate processor to remove duplicate items."""

    def process(self, items: List[DataElement]) -> List[DataElement]:
        """Remove duplicates based on configuration."""
        key_fields = self.config.get("key", [])

        if isinstance(key_fields, str):
            key_fields = [key_fields]

        seen_keys = set()
        deduplicated_items = []

        for item in items:
            # Create deduplication key
            if key_fields:
                key_values = tuple(str(item.data.get(field, "")) for field in key_fields)
            else:
                # Use all data as key if no specific fields specified
                key_values = tuple(sorted(f"{k}:{v}" for k, v in item.data.items()))

            if key_values not in seen_keys:
                seen_keys.add(key_values)
                deduplicated_items.append(item)

        return deduplicated_items


class AddColumnsProcessor(PostProcessor):
    """Add custom columns to data (e.g., date, source, etc.)"""

    def process(self, items: List[DataElement]) -> List[DataElement]:
        """Add configured columns to each data element"""
        columns_to_add = self.config.get("columns", {})

        if not columns_to_add:
            return items

        processed_items = []

        for item in items:
            # Create new data with additional columns
            new_data = item.data.copy()

            # Add each configured column
            for column_name, column_config in columns_to_add.items():
                if isinstance(column_config, dict):
                    # Complex column configuration
                    column_value = column_config.get("value", "")
                    column_type = column_config.get("type", "string")

                    # Support for dynamic values (e.g., current date)
                    if column_value == "{current_date}":
                        from datetime import datetime
                        column_value = datetime.now().strftime("%Y-%m-%d")
                    elif column_value == "{current_datetime}":
                        from datetime import datetime
                        column_value = datetime.now().isoformat()
                    elif column_value == "{source_url}":
                        column_value = item.source_url

                else:
                    # Simple string value
                    column_value = str(column_config)

                new_data[column_name] = column_value

            # Create new item with additional columns
            processed_item = DataElement(
                id=item.id,
                source_url=item.source_url,
                scraped_at=item.scraped_at,
                data=new_data,
                metadata=item.metadata
            )
            processed_items.append(processed_item)

        return processed_items


class RemoveHeadersProcessor(PostProcessor):
    """Remove header rows that appear after the first page."""

    def process(self, items: List[DataElement]) -> List[DataElement]:
        """Remove duplicate header rows."""
        if not items:
            return items

        # Configuration options
        header_indicators = self.config.get("header_indicators", [
            "date", "time", "generation", "demand", "mw", "column",
            "sl", "serial", "no.", "#", "header"
        ])
        keep_first = self.config.get("keep_first", True)
        case_sensitive = self.config.get("case_sensitive", False)
        exact_match = self.config.get("exact_match", False)

        # Convert header indicators to appropriate case
        if not case_sensitive:
            header_indicators = [h.lower() for h in header_indicators]

        # Find potential header rows
        header_indices = set()
        first_header_found = False

        for i, item in enumerate(items):
            is_header_row = False

            # Get all text values from the item
            text_values = [str(v) for v in item.data.values() if str(v).strip()]

            if not text_values:
                continue

            # Check if this looks like a header row
            combined_text = " ".join(text_values)
            if not case_sensitive:
                combined_text = combined_text.lower()

            # Check for header indicators
            for indicator in header_indicators:
                if exact_match:
                    # Exact match against individual values
                    if any(indicator == (val.lower() if not case_sensitive else val)
                           for val in text_values):
                        is_header_row = True
                        break
                else:
                    # Substring match
                    if indicator in combined_text:
                        is_header_row = True
                        break

            # Additional heuristics for header detection
            if not is_header_row:
                # Check if row contains mostly column-like names
                if len(text_values) >= 3:  # At least 3 columns
                    # Common patterns in headers
                    header_patterns = [
                        r'^(column|col)_?\d+$',  # column1, col_1, etc.
                        r'^[a-z_]+\([a-z]+\)$',  # generation(mw), demand(mw)
                        r'^\w+\s+\([^)]+\)$',    # Generation (MW)
                        r'^sl\.?$|^no\.?$|^#$',  # SL, No., #
                    ]

                    header_like_count = 0
                    for val in text_values:
                        val_check = val.lower() if not case_sensitive else val
                        for pattern in header_patterns:
                            if re.match(pattern, val_check, re.IGNORECASE if not case_sensitive else 0):
                                header_like_count += 1
                                break

                    # If most values look like headers
                    if header_like_count >= len(text_values) * 0.6:
                        is_header_row = True

            if is_header_row:
                if keep_first and not first_header_found:
                    first_header_found = True
                    # Keep the first header row
                else:
                    header_indices.add(i)

        # Remove identified header rows (except the first one if keep_first=True)
        filtered_items = [
            item for i, item in enumerate(items)
            if i not in header_indices
        ]

        removed_count = len(header_indices)
        if removed_count > 0:
            print(f"🗑️  Removed {removed_count} duplicate header rows")

        return filtered_items


def create_post_processor(processor_type: str, config: Dict[str, Any]) -> PostProcessor:
    """Factory function to create post-processors."""

    processor_map = {
        "filter": FilterProcessor,
        "transform": TransformProcessor,
        "validate": ValidateProcessor,
        "deduplicate": DeduplicateProcessor,
        "remove_headers": RemoveHeadersProcessor,
        "add_columns": AddColumnsProcessor,
    }

    processor_class = processor_map.get(processor_type)
    if not processor_class:
        raise ValueError(f"Unknown post-processor type: {processor_type}")

    return processor_class(config)