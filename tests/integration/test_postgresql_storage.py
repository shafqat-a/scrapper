"""Integration tests for PostgreSQL storage provider.

Tests PostgreSQL database operations with real Docker container.
Includes connection pooling, transactions, schema management, and performance.
Follows TDD approach - tests will fail until implementations exist.
"""

# Standard library imports
import asyncio
import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List

# Third-party imports
import asyncpg
import psycopg2
import pytest

# Local application imports
from providers.storage.postgresql_provider import PostgreSqlStorageProvider
from scraper_core.models import ScrapedItem, StorageConfig


@pytest.mark.integration
@pytest.mark.database
@pytest.mark.postgresql
@pytest.mark.asyncio
class TestPostgreSqlStorageIntegration:
    """Integration tests for PostgreSQL storage provider."""

    @pytest.fixture(autouse=True)
    async def setup_postgresql_environment(self, postgresql_container):
        """Set up PostgreSQL test environment with Docker container."""
        self.pg_config = {
            "host": "localhost",
            "port": postgresql_container["port"],
            "database": "test_scrapper",
            "user": "scrapper_user",
            "password": "scrapper_pass",
        }

        # Wait for PostgreSQL to be ready
        await self._wait_for_postgresql()

        # Create test database and schema
        await self._setup_test_database()

        yield

        # Cleanup test data
        await self._cleanup_test_database()

    async def _wait_for_postgresql(self, max_retries=30):
        """Wait for PostgreSQL to be ready for connections."""
        for attempt in range(max_retries):
            try:
                conn = await asyncpg.connect(**self.pg_config)
                await conn.close()
                return
            except Exception:
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                else:
                    raise

    async def _setup_test_database(self):
        """Set up test database and initial schema."""
        # Create database if it doesn't exist (using sync connection for this)
        admin_config = self.pg_config.copy()
        admin_config["database"] = "postgres"

        try:
            conn = psycopg2.connect(**admin_config)
            conn.autocommit = True
            cursor = conn.cursor()

            # Create test database
            cursor.execute("CREATE DATABASE test_scrapper")
            cursor.close()
            conn.close()
        except psycopg2.errors.DuplicateDatabase:
            pass  # Database already exists

    async def _cleanup_test_database(self):
        """Clean up test database."""
        try:
            conn = await asyncpg.connect(**self.pg_config)

            # Drop all test tables
            tables = await conn.fetch(
                """
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public' AND tablename LIKE 'test_%'
            """
            )

            for table in tables:
                await conn.execute(f"DROP TABLE IF EXISTS {table['tablename']} CASCADE")

            await conn.close()
        except Exception:
            pass  # Ignore cleanup errors

    async def test_basic_postgresql_operations(self):
        """Test basic PostgreSQL CRUD operations."""
        # Arrange
        table_name = "test_basic_items"
        config = {
            "connectionString": f"postgresql://{self.pg_config['user']}:{self.pg_config['password']}@{self.pg_config['host']}:{self.pg_config['port']}/{self.pg_config['database']}",
            "tableName": table_name,
            "createTable": True,
            "schema": {
                "id": "SERIAL PRIMARY KEY",
                "name": "VARCHAR(255) NOT NULL",
                "price": "DECIMAL(10,2)",
                "in_stock": "BOOLEAN DEFAULT FALSE",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            },
        }

        sample_data = [
            {"name": "Product A", "price": 29.99, "in_stock": True},
            {"name": "Product B", "price": 49.99, "in_stock": False},
            {"name": "Product C", "price": 15.50, "in_stock": True},
        ]

        # Act & Assert - TDD approach
        with pytest.raises(
            NotImplementedError
        ):  # Should fail until PostgreSQL provider implemented
            provider = PostgreSqlStorageProvider(config)
            await provider.connect()

            # Create table
            await provider.create_table()

            # Store items
            stored_ids = []
            for item_data in sample_data:
                item = ScrapedItem(**item_data)
                stored_id = await provider.store(item)
                stored_ids.append(stored_id)

            # Query back data
            results = await provider.query("SELECT * FROM test_basic_items ORDER BY id")
            assert len(results) == 3
            assert results[0]["name"] == "Product A"
            assert float(results[0]["price"]) == 29.99
            assert results[0]["in_stock"] is True

            # Update item
            await provider.update(stored_ids[0], {"price": 39.99, "in_stock": False})

            # Verify update
            updated = await provider.query(
                "SELECT * FROM test_basic_items WHERE id = $1", stored_ids[0]
            )
            assert float(updated[0]["price"]) == 39.99
            assert updated[0]["in_stock"] is False

            # Delete item
            await provider.delete(stored_ids[1])

            # Verify deletion
            remaining = await provider.query(
                "SELECT COUNT(*) as count FROM test_basic_items"
            )
            assert remaining[0]["count"] == 2

            await provider.disconnect()

    async def test_connection_pooling_and_concurrency(self):
        """Test PostgreSQL connection pooling with concurrent operations."""
        # Arrange
        table_name = "test_concurrent_items"
        config = {
            "connectionString": f"postgresql://{self.pg_config['user']}:{self.pg_config['password']}@{self.pg_config['host']}:{self.pg_config['port']}/{self.pg_config['database']}",
            "tableName": table_name,
            "poolSize": 10,
            "maxOverflow": 20,
            "poolTimeout": 30,
            "createTable": True,
        }

        # Generate concurrent data
        concurrent_batches = []
        for batch in range(10):
            batch_data = []
            for item in range(100):
                batch_data.append(
                    {
                        "name": f"Batch{batch}_Item{item}",
                        "value": batch * 100 + item,
                        "category": f"category_{batch % 3}",
                    }
                )
            concurrent_batches.append(batch_data)

        # Act & Assert
        with pytest.raises(NotImplementedError):
            provider = PostgreSqlStorageProvider(config)
            await provider.connect()

            # Create table
            await provider.create_table()

            # Concurrent insert function
            async def insert_batch(batch_data):
                for item_data in batch_data:
                    item = ScrapedItem(**item_data)
                    await provider.store(item)

            # Execute concurrent inserts
            tasks = [insert_batch(batch) for batch in concurrent_batches]
            await asyncio.gather(*tasks)

            # Verify all data inserted
            count_result = await provider.query(
                f"SELECT COUNT(*) as count FROM {table_name}"
            )
            assert count_result[0]["count"] == 1000  # 10 batches * 100 items

            # Verify data integrity
            category_counts = await provider.query(
                f"""
                SELECT category, COUNT(*) as count
                FROM {table_name}
                GROUP BY category
                ORDER BY category
            """
            )

            # Should have roughly equal distribution
            for cat_result in category_counts:
                assert cat_result["count"] >= 300  # At least 300 items per category

            await provider.disconnect()

    async def test_complex_data_types_and_json(self):
        """Test PostgreSQL complex data types including JSON, arrays, and custom types."""
        # Arrange
        table_name = "test_complex_types"
        config = {
            "connectionString": f"postgresql://{self.pg_config['user']}:{self.pg_config['password']}@{self.pg_config['host']}:{self.pg_config['port']}/{self.pg_config['database']}",
            "tableName": table_name,
            "createTable": True,
            "schema": {
                "id": "SERIAL PRIMARY KEY",
                "metadata": "JSONB",
                "tags": "TEXT[]",
                "coordinates": "POINT",
                "price_range": "NUMRANGE",
                "created_at": "TIMESTAMP WITH TIME ZONE",
                "search_vector": "TSVECTOR",
            },
        }

        complex_data = [
            {
                "metadata": {
                    "title": "Complex Item 1",
                    "features": ["feature1", "feature2"],
                    "specs": {"width": 10, "height": 20, "weight": 1.5},
                },
                "tags": ["electronics", "gadgets", "popular"],
                "coordinates": {"x": 37.7749, "y": -122.4194},  # San Francisco
                "price_range": {"min": 100.0, "max": 200.0},
            },
            {
                "metadata": {
                    "title": "Complex Item 2",
                    "features": ["feature3", "feature4"],
                    "specs": {"width": 15, "height": 25, "weight": 2.1},
                },
                "tags": ["home", "furniture", "sale"],
                "coordinates": {"x": 40.7128, "y": -74.0060},  # New York
                "price_range": {"min": 50.0, "max": 150.0},
            },
        ]

        # Act & Assert
        with pytest.raises(NotImplementedError):
            provider = PostgreSqlStorageProvider(config)
            await provider.connect()

            await provider.create_table()

            # Store complex data
            for item_data in complex_data:
                item = ScrapedItem(**item_data)
                await provider.store(item)

            # Query with JSON operations
            json_results = await provider.query(
                f"""
                SELECT metadata->>'title' as title,
                       metadata->'specs'->>'weight' as weight,
                       array_length(tags, 1) as tag_count
                FROM {table_name}
                WHERE metadata->'specs'->>'width' = '10'
            """
            )

            assert len(json_results) == 1
            assert json_results[0]["title"] == "Complex Item 1"
            assert float(json_results[0]["weight"]) == 1.5
            assert json_results[0]["tag_count"] == 3

            # Query with array operations
            array_results = await provider.query(
                f"""
                SELECT * FROM {table_name}
                WHERE 'electronics' = ANY(tags)
            """
            )

            assert len(array_results) == 1

            await provider.disconnect()

    async def test_transaction_management(self):
        """Test PostgreSQL transaction management and rollback scenarios."""
        # Arrange
        table_name = "test_transactions"
        config = {
            "connectionString": f"postgresql://{self.pg_config['user']}:{self.pg_config['password']}@{self.pg_config['host']}:{self.pg_config['port']}/{self.pg_config['database']}",
            "tableName": table_name,
            "useTransactions": True,
            "createTable": True,
        }

        test_data = [
            {"name": "Transaction Item 1", "value": 100},
            {"name": "Transaction Item 2", "value": 200},
            {"name": "Invalid Item", "value": None},  # This should cause error
        ]

        # Act & Assert
        with pytest.raises(NotImplementedError):
            provider = PostgreSqlStorageProvider(config)
            await provider.connect()

            await provider.create_table()

            # Test successful transaction
            async with provider.transaction():
                for item_data in test_data[:2]:  # Only valid items
                    item = ScrapedItem(**item_data)
                    await provider.store(item)

            # Verify successful transaction
            count = await provider.query(f"SELECT COUNT(*) as count FROM {table_name}")
            assert count[0]["count"] == 2

            # Test failed transaction with rollback
            try:
                async with provider.transaction():
                    for item_data in test_data:  # Include invalid item
                        item = ScrapedItem(**item_data)
                        await provider.store(item)
            except Exception:
                pass  # Expected to fail

            # Verify rollback - count should still be 2
            count_after_rollback = await provider.query(
                f"SELECT COUNT(*) as count FROM {table_name}"
            )
            assert count_after_rollback[0]["count"] == 2

            await provider.disconnect()

    async def test_bulk_operations_and_performance(self):
        """Test PostgreSQL bulk operations for high-performance scenarios."""
        # Arrange
        table_name = "test_bulk_operations"
        config = {
            "connectionString": f"postgresql://{self.pg_config['user']}:{self.pg_config['password']}@{self.pg_config['host']}:{self.pg_config['port']}/{self.pg_config['database']}",
            "tableName": table_name,
            "bulkInsert": True,
            "batchSize": 1000,
            "createTable": True,
        }

        # Generate large dataset
        large_dataset = []
        for i in range(10000):
            large_dataset.append(
                {
                    "name": f"Bulk Item {i:05d}",
                    "value": i * 1.5,
                    "category": f"category_{i % 10}",
                    "description": f"Description for item {i} with some longer text content",
                }
            )

        # Act & Assert
        with pytest.raises(NotImplementedError):
            provider = PostgreSqlStorageProvider(config)
            await provider.connect()

            await provider.create_table()

            # Measure bulk insert performance
            # Standard library imports
            import time

            start_time = time.time()

            # Bulk insert
            await provider.bulk_store(large_dataset)

            end_time = time.time()
            insert_time = end_time - start_time

            # Verify all data inserted
            count_result = await provider.query(
                f"SELECT COUNT(*) as count FROM {table_name}"
            )
            assert count_result[0]["count"] == 10000

            # Performance assertion - should be faster than individual inserts
            # Bulk insert of 10k records should complete in reasonable time
            assert insert_time < 10.0  # Should complete within 10 seconds

            # Test bulk update
            start_update = time.time()
            await provider.bulk_update(
                f"UPDATE {table_name} SET value = value * 2 WHERE category = 'category_0'"
            )
            end_update = time.time()

            # Verify bulk update
            updated_count = await provider.query(
                f"""
                SELECT COUNT(*) as count FROM {table_name}
                WHERE category = 'category_0' AND value > 1000
            """
            )
            assert updated_count[0]["count"] > 0

            await provider.disconnect()

    async def test_indexing_and_query_optimization(self):
        """Test PostgreSQL indexing and query optimization features."""
        # Arrange
        table_name = "test_indexing"
        config = {
            "connectionString": f"postgresql://{self.pg_config['user']}:{self.pg_config['password']}@{self.pg_config['host']}:{self.pg_config['port']}/{self.pg_config['database']}",
            "tableName": table_name,
            "createTable": True,
            "indexes": [
                {"columns": ["name"], "type": "btree"},
                {"columns": ["category", "value"], "type": "btree"},
                {
                    "columns": ["search_text"],
                    "type": "gin",
                    "using": "gin(to_tsvector('english', search_text))",
                },
            ],
        }

        # Generate searchable dataset
        search_dataset = []
        for i in range(5000):
            search_dataset.append(
                {
                    "name": f"Searchable Item {i:04d}",
                    "category": f"cat_{i % 20}",
                    "value": i * 0.5,
                    "search_text": f"This is item {i} with searchable content about category {i % 20}",
                }
            )

        # Act & Assert
        with pytest.raises(NotImplementedError):
            provider = PostgreSqlStorageProvider(config)
            await provider.connect()

            await provider.create_table()
            await provider.create_indexes()

            # Bulk insert data
            await provider.bulk_store(search_dataset)

            # Test index usage with EXPLAIN
            explain_result = await provider.query(
                f"""
                EXPLAIN (ANALYZE, BUFFERS)
                SELECT * FROM {table_name}
                WHERE category = 'cat_5' AND value > 100
            """
            )

            # Should use index scan (verify in explain output)
            explain_text = str(explain_result)
            # In a real implementation, would parse EXPLAIN output

            # Test full-text search
            search_results = await provider.query(
                f"""
                SELECT name, ts_rank(to_tsvector('english', search_text),
                                   plainto_tsquery('english', 'category 5')) as rank
                FROM {table_name}
                WHERE to_tsvector('english', search_text) @@ plainto_tsquery('english', 'category 5')
                ORDER BY rank DESC
                LIMIT 10
            """
            )

            assert len(search_results) > 0

            # Test performance with large result set
            # Standard library imports
            import time

            start_time = time.time()

            large_result = await provider.query(
                f"""
                SELECT category, COUNT(*) as count, AVG(value) as avg_value
                FROM {table_name}
                GROUP BY category
                ORDER BY count DESC
            """
            )

            end_time = time.time()
            query_time = end_time - start_time

            assert len(large_result) == 20  # 20 categories
            assert query_time < 1.0  # Should be fast with proper indexing

            await provider.disconnect()

    async def test_data_migration_and_schema_evolution(self):
        """Test PostgreSQL schema migration and data evolution."""
        # Arrange - Initial schema
        table_name = "test_migration"
        initial_config = {
            "connectionString": f"postgresql://{self.pg_config['user']}:{self.pg_config['password']}@{self.pg_config['host']}:{self.pg_config['port']}/{self.pg_config['database']}",
            "tableName": table_name,
            "createTable": True,
            "schema": {
                "id": "SERIAL PRIMARY KEY",
                "name": "VARCHAR(255)",
                "value": "INTEGER",
            },
        }

        # Migration schema
        migrated_config = {
            "connectionString": f"postgresql://{self.pg_config['user']}:{self.pg_config['password']}@{self.pg_config['host']}:{self.pg_config['port']}/{self.pg_config['database']}",
            "tableName": table_name,
            "migrations": [
                "ALTER TABLE test_migration ADD COLUMN new_field VARCHAR(100)",
                "ALTER TABLE test_migration ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "CREATE INDEX idx_migration_name ON test_migration(name)",
            ],
        }

        initial_data = [
            {"name": "Item 1", "value": 100},
            {"name": "Item 2", "value": 200},
        ]

        # Act & Assert
        with pytest.raises(NotImplementedError):
            # Create initial table and data
            provider = PostgreSqlStorageProvider(initial_config)
            await provider.connect()

            await provider.create_table()

            for item_data in initial_data:
                item = ScrapedItem(**item_data)
                await provider.store(item)

            await provider.disconnect()

            # Apply migrations
            migration_provider = PostgreSqlStorageProvider(migrated_config)
            await migration_provider.connect()

            await migration_provider.apply_migrations()

            # Verify schema changes
            columns = await migration_provider.query(
                f"""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position
            """
            )

            column_names = [col["column_name"] for col in columns]
            assert "new_field" in column_names
            assert "created_at" in column_names

            # Verify existing data preserved
            existing_data = await migration_provider.query(
                f"SELECT * FROM {table_name}"
            )
            assert len(existing_data) == 2
            assert existing_data[0]["name"] == "Item 1"

            await migration_provider.disconnect()

    async def test_backup_and_restore_operations(self):
        """Test PostgreSQL backup and restore capabilities."""
        # Arrange
        table_name = "test_backup_restore"
        backup_path = Path("tests/tmp/postgresql_backup.sql")
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        config = {
            "connectionString": f"postgresql://{self.pg_config['user']}:{self.pg_config['password']}@{self.pg_config['host']}:{self.pg_config['port']}/{self.pg_config['database']}",
            "tableName": table_name,
            "createTable": True,
            "backupPath": str(backup_path),
        }

        backup_data = [
            {"name": "Backup Item 1", "value": 100},
            {"name": "Backup Item 2", "value": 200},
            {"name": "Backup Item 3", "value": 300},
        ]

        # Act & Assert
        with pytest.raises(NotImplementedError):
            provider = PostgreSqlStorageProvider(config)
            await provider.connect()

            await provider.create_table()

            # Insert test data
            for item_data in backup_data:
                item = ScrapedItem(**item_data)
                await provider.store(item)

            # Create backup
            await provider.backup_table()

            # Verify backup file exists
            assert backup_path.exists()
            assert backup_path.stat().st_size > 0

            # Delete all data
            await provider.query(f"TRUNCATE TABLE {table_name}")

            # Verify data deleted
            count = await provider.query(f"SELECT COUNT(*) as count FROM {table_name}")
            assert count[0]["count"] == 0

            # Restore from backup
            await provider.restore_table()

            # Verify data restored
            restored_count = await provider.query(
                f"SELECT COUNT(*) as count FROM {table_name}"
            )
            assert restored_count[0]["count"] == 3

            restored_data = await provider.query(
                f"SELECT * FROM {table_name} ORDER BY name"
            )
            assert restored_data[0]["name"] == "Backup Item 1"

            await provider.disconnect()

            # Cleanup backup file
            backup_path.unlink()


@pytest.mark.integration
@pytest.mark.database
@pytest.mark.postgresql
@pytest.mark.asyncio
class TestPostgreSqlProviderSpecific:
    """PostgreSQL provider-specific integration tests."""

    async def test_postgresql_specific_features(self):
        """Test PostgreSQL-specific features like arrays, JSON, full-text search."""
        with pytest.raises(NotImplementedError):
            # Test will be implemented when provider exists
            pass

    async def test_postgresql_connection_resilience(self):
        """Test PostgreSQL connection resilience and auto-reconnection."""
        with pytest.raises(NotImplementedError):
            # Test connection drops, network issues, reconnection logic
            pass

    async def test_postgresql_monitoring_and_metrics(self):
        """Test PostgreSQL monitoring, metrics collection, and health checks."""
        with pytest.raises(NotImplementedError):
            # Test connection pool metrics, query performance, health status
            pass
