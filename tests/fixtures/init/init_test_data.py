#!/usr/bin/env python3
"""
Initialize test data in backend services for integration testing.
This script runs after all services are healthy.
"""

# Standard library imports
import json
import time
from datetime import datetime
from typing import Any, Dict

# Third-party imports
import boto3
import psycopg2
import pymongo
import redis
from botocore.exceptions import ClientError
from elasticsearch import Elasticsearch


def wait_for_service(func, service_name: str, max_retries: int = 30):
    """Wait for a service to be ready."""
    for i in range(max_retries):
        try:
            func()
            print(f"✓ {service_name} is ready")
            return
        except Exception as e:
            if i == max_retries - 1:
                raise Exception(f"Failed to connect to {service_name}: {e}")
            print(f"Waiting for {service_name}... ({i+1}/{max_retries})")
            time.sleep(2)


def init_postgres():
    """Initialize PostgreSQL test data."""

    def connect():
        conn = psycopg2.connect(
            host="postgres",
            database="test_scrapper",
            user="test_user",
            password="test_password",
        )
        return conn

    wait_for_service(connect, "PostgreSQL")

    conn = connect()
    cursor = conn.cursor()

    # Create test tables
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS scraped_products (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            price DECIMAL(10,2),
            description TEXT,
            url VARCHAR(512),
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS workflow_results (
            id SERIAL PRIMARY KEY,
            workflow_id VARCHAR(100) NOT NULL,
            status VARCHAR(50) NOT NULL,
            total_records INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """
    )

    # Insert sample data
    sample_products = [
        ("Test Product 1", 19.99, "Sample description", "http://test.com/1"),
        ("Test Product 2", 29.99, "Another description", "http://test.com/2"),
        ("Test Product 3", 39.99, "Third product", "http://test.com/3"),
    ]

    cursor.executemany(
        "INSERT INTO scraped_products (title, price, description, url) VALUES (%s, %s, %s, %s)",
        sample_products,
    )

    conn.commit()
    cursor.close()
    conn.close()
    print("✓ PostgreSQL test data initialized")


def init_mongodb():
    """Initialize MongoDB test data."""

    def connect():
        client = pymongo.MongoClient(
            "mongodb://test_user:test_password@mongodb:27017/test_scrapper?authSource=admin"
        )
        client.admin.command("ping")
        return client

    wait_for_service(connect, "MongoDB")

    client = connect()
    db = client.test_scrapper

    # Create collections and insert test data
    products = db.products
    products.create_index("url", unique=True)

    sample_documents = [
        {
            "title": "MongoDB Product 1",
            "price": 19.99,
            "description": "Document-based product",
            "url": "http://test.com/mongo/1",
            "metadata": {
                "scraped_at": datetime.now(),
                "source": "test-scraper",
                "tags": ["electronics", "test"],
            },
        },
        {
            "title": "MongoDB Product 2",
            "price": 29.99,
            "description": "Another document",
            "url": "http://test.com/mongo/2",
            "metadata": {
                "scraped_at": datetime.now(),
                "source": "test-scraper",
                "tags": ["books", "test"],
            },
        },
    ]

    products.insert_many(sample_documents)

    client.close()
    print("✓ MongoDB test data initialized")


def init_redis():
    """Initialize Redis test data."""

    def connect():
        r = redis.Redis(
            host="redis", port=6379, password="test_password", decode_responses=True
        )
        r.ping()
        return r

    wait_for_service(connect, "Redis")

    r = connect()

    # Set test cache data
    test_cache_data = {
        "scraper:session:test1": json.dumps(
            {"user_agent": "test-agent", "cookies": []}
        ),
        "scraper:rate_limit:test.com": "10",
        "scraper:results:workflow1": json.dumps({"status": "completed", "count": 5}),
    }

    for key, value in test_cache_data.items():
        r.set(key, value, ex=3600)  # 1 hour expiration

    print("✓ Redis test data initialized")


def init_elasticsearch():
    """Initialize Elasticsearch test data."""

    def connect():
        es = Elasticsearch([{"host": "elasticsearch", "port": 9200}])
        es.ping()
        return es

    wait_for_service(connect, "Elasticsearch")

    es = connect()

    # Create index with mapping
    index_name = "scraped_content"
    mapping = {
        "mappings": {
            "properties": {
                "title": {"type": "text", "analyzer": "standard"},
                "content": {"type": "text", "analyzer": "standard"},
                "url": {"type": "keyword"},
                "scraped_at": {"type": "date"},
                "price": {"type": "float"},
                "tags": {"type": "keyword"},
            }
        }
    }

    if es.indices.exists(index=index_name):
        es.indices.delete(index=index_name)

    es.indices.create(index=index_name, body=mapping)

    # Insert test documents
    test_docs = [
        {
            "title": "Elasticsearch Product 1",
            "content": "Full-text searchable content for testing",
            "url": "http://test.com/es/1",
            "scraped_at": datetime.now().isoformat(),
            "price": 19.99,
            "tags": ["electronics", "test", "searchable"],
        },
        {
            "title": "Elasticsearch Product 2",
            "content": "Another searchable document with different content",
            "url": "http://test.com/es/2",
            "scraped_at": datetime.now().isoformat(),
            "price": 29.99,
            "tags": ["books", "test", "searchable"],
        },
    ]

    for doc in test_docs:
        es.index(index=index_name, body=doc)

    es.indices.refresh(index=index_name)
    print("✓ Elasticsearch test data initialized")


def init_minio():
    """Initialize MinIO test data."""

    def connect():
        client = boto3.client(
            "s3",
            endpoint_url="http://minio:9000",
            aws_access_key_id="test_user",
            aws_secret_access_key="test_password123",
            region_name="us-east-1",
        )
        client.list_buckets()
        return client

    wait_for_service(connect, "MinIO")

    s3_client = connect()

    # Create test bucket
    bucket_name = "scraper-test-bucket"
    try:
        s3_client.create_bucket(Bucket=bucket_name)
    except ClientError as e:
        if e.response["Error"]["Code"] != "BucketAlreadyOwnedByYou":
            raise

    # Upload test files
    test_files = {
        "test-data/sample1.json": json.dumps({"test": "data1", "count": 1}),
        "test-data/sample2.json": json.dumps({"test": "data2", "count": 2}),
        "exports/test-export.csv": "id,name,price\\n1,Product 1,19.99\\n2,Product 2,29.99",
    }

    for key, content in test_files.items():
        s3_client.put_object(Bucket=bucket_name, Key=key, Body=content.encode("utf-8"))

    print("✓ MinIO test data initialized")


def main():
    """Initialize all test services with sample data."""
    print("Initializing test backends...")

    try:
        init_postgres()
        init_mongodb()
        init_redis()
        init_elasticsearch()
        init_minio()

        print("\n🎉 All test backends initialized successfully!")

        # Create status file
        with open("/tmp/init_complete", "w") as f:
            f.write(f"Initialization completed at {datetime.now().isoformat()}")

    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        raise


if __name__ == "__main__":
    main()
