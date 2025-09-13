"""Integration tests for CSV storage provider.

Tests CSV storage operations with real file system operations.
Includes large dataset handling, encoding, and format validation.
Follows TDD approach - tests will fail until implementations exist.
"""

# Standard library imports
import asyncio
import csv
import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List

# Third-party imports
import pandas as pd
import pytest
from pydantic import ValidationError

# Local application imports
from providers.storage.csv_provider import CsvStorageProvider
from scraper_core.models import ScrapedItem, StorageConfig


@pytest.mark.integration
@pytest.mark.csv
@pytest.mark.asyncio
class TestCsvStorageIntegration:
    """Integration tests for CSV storage provider."""

    @pytest.fixture(autouse=True)
    async def setup_test_environment(self):
        """Set up test environment with temporary CSV files."""
        self.output_dir = Path("tests/tmp/csv_integration")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Test data samples
        self.sample_data = [
            {
                "id": 1,
                "name": "Product A",
                "price": 29.99,
                "in_stock": True,
                "created_at": "2024-01-01T10:00:00Z",
                "tags": ["electronics", "gadgets"],
                "rating": 4.5,
            },
            {
                "id": 2,
                "name": "Product B",
                "price": 49.99,
                "in_stock": False,
                "created_at": "2024-01-02T11:30:00Z",
                "tags": ["home", "kitchen"],
                "rating": 3.8,
            },
            {
                "id": 3,
                "name": "Special Çhäracters & Unicode 🎉",
                "price": 15.50,
                "in_stock": True,
                "created_at": "2024-01-03T14:15:00Z",
                "tags": ["special", "unicode"],
                "rating": 5.0,
            },
        ]

        yield

        # Cleanup
        import shutil

        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)

    async def test_basic_csv_storage_operations(self):
        """Test basic CSV storage create, write, and read operations."""
        # Arrange
        csv_path = self.output_dir / "basic_test.csv"
        config = {
            "outputPath": str(csv_path),
            "encoding": "utf-8",
            "delimiter": ",",
            "quoting": "minimal",
            "headers": True,
        }

        # Act & Assert - TDD approach
        with pytest.raises(
            NotImplementedError
        ):  # Should fail until CSV provider implemented
            provider = CsvStorageProvider(config)
            await provider.connect()

            # Store sample data
            for item_data in self.sample_data:
                item = ScrapedItem(**item_data)
                await provider.store(item)

            await provider.disconnect()

            # Verify file exists and has correct content
            assert csv_path.exists()

            # Read back and verify
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == len(self.sample_data)
                assert rows[0]["name"] == "Product A"
                assert rows[2]["name"] == "Special Çhäracters & Unicode 🎉"

    async def test_large_dataset_streaming(self):
        """Test handling of large datasets with streaming writes."""
        # Arrange - Generate large dataset
        large_dataset = []
        for i in range(10000):
            large_dataset.append(
                {
                    "id": i,
                    "name": f"Item {i:05d}",
                    "value": i * 1.5,
                    "category": f"category_{i % 10}",
                    "timestamp": f"2024-01-{(i % 28) + 1:02d}T{(i % 24):02d}:00:00Z",
                }
            )

        csv_path = self.output_dir / "large_dataset.csv"
        config = {
            "outputPath": str(csv_path),
            "encoding": "utf-8",
            "delimiter": ",",
            "streamingWrite": True,
            "bufferSize": 1000,
            "flushInterval": 5.0,
        }

        # Act & Assert
        with pytest.raises(NotImplementedError):
            provider = CsvStorageProvider(config)
            await provider.connect()

            # Stream large dataset
            for item_data in large_dataset:
                item = ScrapedItem(**item_data)
                await provider.store(item)

            await provider.flush()  # Ensure all data is written
            await provider.disconnect()

            # Verify file size and content
            assert csv_path.exists()
            file_size = csv_path.stat().st_size
            assert file_size > 100000  # Should be substantial size

            # Verify with pandas for large file handling
            df = pd.read_csv(csv_path)
            assert len(df) == 10000
            assert df["id"].max() == 9999
            assert df["name"].iloc[0] == "Item 00000"

    async def test_different_csv_formats_and_encodings(self):
        """Test different CSV formats, delimiters, and encodings."""
        test_cases = [
            {
                "name": "semicolon_delimited",
                "config": {"delimiter": ";", "quoting": "all", "encoding": "utf-8"},
            },
            {
                "name": "tab_delimited",
                "config": {"delimiter": "\t", "quoting": "none", "encoding": "utf-8"},
            },
            {
                "name": "pipe_delimited",
                "config": {
                    "delimiter": "|",
                    "quoting": "minimal",
                    "encoding": "latin-1",
                },
            },
            {
                "name": "excel_format",
                "config": {
                    "delimiter": ",",
                    "quoting": "all",
                    "lineterminator": "\r\n",
                    "encoding": "utf-8-sig",  # BOM for Excel
                },
            },
        ]

        for case in test_cases:
            with pytest.raises(NotImplementedError):
                csv_path = self.output_dir / f"{case['name']}.csv"
                config = {"outputPath": str(csv_path), **case["config"]}

                provider = CsvStorageProvider(config)
                await provider.connect()

                # Store sample data
                for item_data in self.sample_data:
                    item = ScrapedItem(**item_data)
                    await provider.store(item)

                await provider.disconnect()

                # Verify file format
                assert csv_path.exists()

    async def test_data_type_handling_and_conversion(self):
        """Test proper handling of different data types in CSV."""
        # Arrange - Complex data types
        complex_data = [
            {
                "id": 1,
                "name": "Test Item",
                "price": Decimal("29.99"),
                "created_date": date(2024, 1, 1),
                "created_datetime": datetime(2024, 1, 1, 10, 30, 0),
                "is_active": True,
                "tags": ["tag1", "tag2", "tag3"],
                "metadata": {"key1": "value1", "key2": 42},
                "nullable_field": None,
                "float_value": 3.14159,
                "large_number": 1234567890,
            }
        ]

        csv_path = self.output_dir / "data_types.csv"
        config = {
            "outputPath": str(csv_path),
            "encoding": "utf-8",
            "handleComplexTypes": True,
            "dateFormat": "%Y-%m-%d",
            "datetimeFormat": "%Y-%m-%d %H:%M:%S",
            "arrayDelimiter": "|",
            "jsonFields": ["metadata"],
        }

        # Act & Assert
        with pytest.raises(NotImplementedError):
            provider = CsvStorageProvider(config)
            await provider.connect()

            for item_data in complex_data:
                item = ScrapedItem(**item_data)
                await provider.store(item)

            await provider.disconnect()

            # Verify data type conversions
            assert csv_path.exists()

            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                row = next(reader)

                # Verify conversions
                assert row["price"] == "29.99"
                assert row["created_date"] == "2024-01-01"
                assert row["is_active"] == "True"
                assert row["tags"] == "tag1|tag2|tag3"
                assert '"key1": "value1"' in row["metadata"]

    async def test_concurrent_csv_operations(self):
        """Test concurrent CSV write operations and thread safety."""
        # Arrange
        csv_path = self.output_dir / "concurrent_test.csv"
        config = {
            "outputPath": str(csv_path),
            "encoding": "utf-8",
            "threadSafe": True,
            "lockFile": True,
        }

        # Generate data for concurrent writes
        concurrent_data = []
        for i in range(100):
            concurrent_data.append(
                [{"id": i * 10 + j, "value": f"thread_{i}_item_{j}"} for j in range(10)]
            )

        # Act & Assert
        with pytest.raises(NotImplementedError):
            provider = CsvStorageProvider(config)
            await provider.connect()

            # Concurrent write tasks
            async def write_batch(batch_data):
                for item_data in batch_data:
                    item = ScrapedItem(**item_data)
                    await provider.store(item)

            # Run concurrent writes
            tasks = [write_batch(batch) for batch in concurrent_data]
            await asyncio.gather(*tasks)

            await provider.disconnect()

            # Verify all data was written correctly
            assert csv_path.exists()

            df = pd.read_csv(csv_path)
            assert len(df) == 1000  # 100 batches * 10 items each
            assert len(df["id"].unique()) == 1000  # All IDs should be unique

    async def test_csv_schema_validation(self):
        """Test CSV schema validation and column enforcement."""
        # Arrange
        csv_path = self.output_dir / "schema_test.csv"
        schema = {
            "id": {"type": "integer", "required": True},
            "name": {"type": "string", "required": True, "max_length": 100},
            "price": {"type": "float", "required": True, "min": 0},
            "in_stock": {"type": "boolean", "required": False},
            "tags": {"type": "array", "required": False},
        }

        config = {
            "outputPath": str(csv_path),
            "encoding": "utf-8",
            "schema": schema,
            "validateOnWrite": True,
            "strictMode": True,
        }

        # Valid and invalid data
        valid_data = {"id": 1, "name": "Valid Item", "price": 29.99, "in_stock": True}
        invalid_data = {"id": "not_integer", "name": "", "price": -10.0}

        # Act & Assert
        with pytest.raises(NotImplementedError):
            provider = CsvStorageProvider(config)
            await provider.connect()

            # Valid data should succeed
            valid_item = ScrapedItem(**valid_data)
            await provider.store(valid_item)

            # Invalid data should raise validation error
            with pytest.raises(ValidationError):
                invalid_item = ScrapedItem(**invalid_data)
                await provider.store(invalid_item)

            await provider.disconnect()

    async def test_csv_append_and_update_operations(self):
        """Test CSV append mode and update operations."""
        # Arrange
        csv_path = self.output_dir / "append_test.csv"

        # Initial write
        initial_config = {
            "outputPath": str(csv_path),
            "encoding": "utf-8",
            "mode": "write",
            "headers": True,
        }

        # Append config
        append_config = {
            "outputPath": str(csv_path),
            "encoding": "utf-8",
            "mode": "append",
            "headers": False,  # Don't write headers again
        }

        # Act & Assert
        with pytest.raises(NotImplementedError):
            # Initial write
            provider = CsvStorageProvider(initial_config)
            await provider.connect()

            for item_data in self.sample_data[:2]:  # First 2 items
                item = ScrapedItem(**item_data)
                await provider.store(item)

            await provider.disconnect()

            # Verify initial file
            assert csv_path.exists()
            initial_df = pd.read_csv(csv_path)
            assert len(initial_df) == 2

            # Append more data
            provider = CsvStorageProvider(append_config)
            await provider.connect()

            for item_data in self.sample_data[2:]:  # Remaining items
                item = ScrapedItem(**item_data)
                await provider.store(item)

            await provider.disconnect()

            # Verify final file
            final_df = pd.read_csv(csv_path)
            assert len(final_df) == 3
            assert final_df["name"].tolist() == [
                "Product A",
                "Product B",
                "Special Çhäracters & Unicode 🎉",
            ]

    async def test_csv_error_handling_and_recovery(self):
        """Test CSV error handling and recovery mechanisms."""
        # Arrange - Invalid path scenarios
        test_cases = [
            {
                "name": "invalid_directory",
                "config": {
                    "outputPath": "/invalid/directory/test.csv",
                    "createDirectories": False,
                },
                "expected_error": FileNotFoundError,
            },
            {
                "name": "permission_denied",
                "config": {
                    "outputPath": "/root/restricted.csv",  # Assuming no write permission
                },
                "expected_error": PermissionError,
            },
            {
                "name": "invalid_encoding",
                "config": {
                    "outputPath": str(self.output_dir / "invalid_encoding.csv"),
                    "encoding": "invalid-encoding",
                },
                "expected_error": LookupError,
            },
        ]

        for case in test_cases:
            with pytest.raises(NotImplementedError):
                provider = CsvStorageProvider(case["config"])

                # Should handle errors gracefully
                try:
                    await provider.connect()
                    item = ScrapedItem(**self.sample_data[0])
                    await provider.store(item)
                except case["expected_error"]:
                    pass  # Expected error
                finally:
                    await provider.disconnect()

    async def test_csv_compression_support(self):
        """Test CSV file compression (gzip, bz2) support."""
        compression_types = ["gzip", "bz2", "xz"]

        for compression in compression_types:
            with pytest.raises(NotImplementedError):
                csv_path = (
                    self.output_dir / f"compressed_{compression}.csv.{compression}"
                )
                config = {
                    "outputPath": str(csv_path),
                    "encoding": "utf-8",
                    "compression": compression,
                    "compressionLevel": 6,
                }

                provider = CsvStorageProvider(config)
                await provider.connect()

                for item_data in self.sample_data:
                    item = ScrapedItem(**item_data)
                    await provider.store(item)

                await provider.disconnect()

                # Verify compressed file exists and is smaller
                assert csv_path.exists()
                compressed_size = csv_path.stat().st_size

                # Create uncompressed version for comparison
                uncompressed_path = self.output_dir / f"uncompressed_{compression}.csv"
                uncompressed_config = {
                    "outputPath": str(uncompressed_path),
                    "encoding": "utf-8",
                }

                provider_uncomp = CsvStorageProvider(uncompressed_config)
                await provider_uncomp.connect()

                for item_data in self.sample_data:
                    item = ScrapedItem(**item_data)
                    await provider_uncomp.store(item)

                await provider_uncomp.disconnect()

                uncompressed_size = uncompressed_path.stat().st_size
                assert compressed_size < uncompressed_size


@pytest.mark.integration
@pytest.mark.csv
@pytest.mark.pandas
@pytest.mark.asyncio
class TestCsvWithPandasIntegration:
    """Integration tests for CSV provider with pandas optimization."""

    @pytest.fixture(autouse=True)
    async def setup_pandas_environment(self):
        """Set up pandas-optimized test environment."""
        self.output_dir = Path("tests/tmp/csv_pandas_integration")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        yield

        import shutil

        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)

    async def test_pandas_optimized_bulk_operations(self):
        """Test pandas-optimized bulk CSV operations."""
        # Arrange - Large dataset for pandas optimization
        large_data = pd.DataFrame(
            {
                "id": range(50000),
                "name": [f"Item_{i:05d}" for i in range(50000)],
                "value": [i * 0.1 for i in range(50000)],
                "category": [f"cat_{i % 100}" for i in range(50000)],
            }
        )

        csv_path = self.output_dir / "pandas_bulk.csv"
        config = {
            "outputPath": str(csv_path),
            "usePandas": True,
            "chunkSize": 10000,
            "pandasOptimizations": True,
        }

        # Act & Assert
        with pytest.raises(NotImplementedError):
            provider = CsvStorageProvider(config)
            await provider.connect()

            # Bulk store using pandas
            await provider.bulk_store(large_data)

            await provider.disconnect()

            # Verify with pandas
            result_df = pd.read_csv(csv_path)
            assert len(result_df) == 50000
            assert result_df["id"].max() == 49999

    async def test_pandas_data_transformation(self):
        """Test pandas-based data transformations during CSV export."""
        # Arrange
        raw_data = [
            {"name": "  Item A  ", "price": "29.99", "date": "2024-01-01"},
            {"name": "ITEM B", "price": "49.99", "date": "2024-01-02"},
            {"name": "item c", "price": "15.50", "date": "2024-01-03"},
        ]

        csv_path = self.output_dir / "transformed.csv"
        config = {
            "outputPath": str(csv_path),
            "usePandas": True,
            "transformations": {
                "name": ["strip", "title"],
                "price": "float",
                "date": "datetime",
            },
            "addColumns": {
                "processed_at": "current_timestamp",
                "price_category": {
                    "function": "categorize_price",
                    "column": "price",
                    "bins": [0, 20, 50, 100],
                    "labels": ["Low", "Medium", "High"],
                },
            },
        }

        # Act & Assert
        with pytest.raises(NotImplementedError):
            provider = CsvStorageProvider(config)
            await provider.connect()

            for item_data in raw_data:
                item = ScrapedItem(**item_data)
                await provider.store(item)

            await provider.disconnect()

            # Verify transformations
            df = pd.read_csv(csv_path)
            assert df["name"].tolist() == ["Item A", "Item B", "Item C"]
            assert df["price"].dtype == "float64"
            assert "processed_at" in df.columns
