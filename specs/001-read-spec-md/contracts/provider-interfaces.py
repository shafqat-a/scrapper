"""
Provider Interface Contracts
These Python classes and protocols define the contracts that all providers must implement.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Protocol, Literal
from pydantic import BaseModel, Field
from dataclasses import dataclass
from datetime import datetime

# Common Types
class ProviderMetadata(BaseModel):
    name: str
    version: str
    type: Literal["scraping", "storage"]
    capabilities: List[str]

class ConnectionConfig(BaseModel):
    """Base configuration for provider connections."""
    pass

class Cookie(BaseModel):
    name: str
    value: str
    domain: str
    path: str
    expires: Optional[int] = None
    http_only: bool = False
    secure: bool = False

class Viewport(BaseModel):
    width: int = Field(ge=320)
    height: int = Field(ge=240)

class PageContext(BaseModel):
    url: str
    title: str
    cookies: List[Cookie] = []
    navigation_history: List[str] = []
    viewport: Viewport = Viewport(width=1920, height=1080)
    user_agent: str = "scrapper/1.0.0"

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

# Step Configuration Types
class InitStepConfig(BaseModel):
    url: str = Field(..., description="Target URL to navigate to")
    wait_for: Optional[str | int] = Field(None, description="CSS selector or milliseconds to wait")
    cookies: List[Cookie] = []
    headers: Dict[str, str] = {}

class DiscoverStepConfig(BaseModel):
    selectors: Dict[str, str] = Field(
        ...,
        description="CSS selectors for different element types"
    )
    pagination: Optional[Dict[str, Any]] = None

class ExtractStepConfig(BaseModel):
    elements: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="Element extraction configuration"
    )

class PaginateStepConfig(BaseModel):
    next_page_selector: str = Field(..., description="CSS selector for next page link")
    max_pages: Optional[int] = Field(None, ge=1)
    wait_after_click: int = Field(default=1000, ge=0)
    stop_condition: Optional[Dict[str, Any]] = None

# Scraping Provider Protocol
class ScrapingProvider(Protocol):
    """Protocol defining the interface for scraping providers."""

    metadata: ProviderMetadata

    async def initialize(self, config: ConnectionConfig) -> None:
        """Initialize the provider with configuration."""
        ...

    async def execute_init(self, step_config: InitStepConfig) -> PageContext:
        """Navigate to initial URL and setup page context."""
        ...

    async def execute_discover(
        self,
        step_config: DiscoverStepConfig,
        context: PageContext
    ) -> List[DataElement]:
        """Discover available data elements on the page."""
        ...

    async def execute_extract(
        self,
        step_config: ExtractStepConfig,
        context: PageContext
    ) -> List[DataElement]:
        """Extract specific data elements from the page."""
        ...

    async def execute_paginate(
        self,
        step_config: PaginateStepConfig,
        context: PageContext
    ) -> Optional[PageContext]:
        """Navigate to next page if available. Returns new context or None."""
        ...

    async def cleanup(self) -> None:
        """Clean up resources (close browser, etc.)."""
        ...

    async def health_check(self) -> bool:
        """Health check for provider availability."""
        ...

# Abstract Base Class for Scraping Providers
class BaseScraper(ABC):
    """Abstract base class for scraping providers."""

    def __init__(self):
        self.metadata = ProviderMetadata(
            name="base-scraper",
            version="1.0.0",
            type="scraping",
            capabilities=[]
        )

    @abstractmethod
    async def initialize(self, config: ConnectionConfig) -> None:
        pass

    @abstractmethod
    async def execute_init(self, step_config: InitStepConfig) -> PageContext:
        pass

    @abstractmethod
    async def execute_discover(
        self,
        step_config: DiscoverStepConfig,
        context: PageContext
    ) -> List[DataElement]:
        pass

    @abstractmethod
    async def execute_extract(
        self,
        step_config: ExtractStepConfig,
        context: PageContext
    ) -> List[DataElement]:
        pass

    @abstractmethod
    async def execute_paginate(
        self,
        step_config: PaginateStepConfig,
        context: PageContext
    ) -> Optional[PageContext]:
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        pass

    async def health_check(self) -> bool:
        """Default health check implementation."""
        return True

# Storage Provider Types
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

class QueryCriteria(BaseModel):
    where: Dict[str, Any] = {}
    order_by: List[Dict[str, str]] = []  # [{"field": "name", "direction": "ASC"}]
    limit: Optional[int] = None
    offset: Optional[int] = None

class StorageStats(BaseModel):
    total_records: int
    last_updated: datetime
    storage_size: Optional[int] = None

# Storage Provider Protocol
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
        self,
        criteria: QueryCriteria,
        schema: SchemaDefinition
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

# Abstract Base Class for Storage Providers
class BaseStorage(ABC):
    """Abstract base class for storage providers."""

    def __init__(self):
        self.metadata = ProviderMetadata(
            name="base-storage",
            version="1.0.0",
            type="storage",
            capabilities=[]
        )

    @abstractmethod
    async def connect(self, config: ConnectionConfig) -> None:
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        pass

    @abstractmethod
    async def store(self, data: List[DataElement], schema: SchemaDefinition) -> None:
        pass

    @abstractmethod
    async def query(
        self,
        criteria: QueryCriteria,
        schema: SchemaDefinition
    ) -> List[DataElement]:
        pass

    @abstractmethod
    async def create_schema(self, definition: SchemaDefinition) -> None:
        pass

    async def validate_schema(self, definition: SchemaDefinition) -> bool:
        """Default schema validation."""
        return True

    async def health_check(self) -> bool:
        """Default health check."""
        return True

    async def get_stats(self) -> StorageStats:
        """Default stats implementation."""
        return StorageStats(
            total_records=0,
            last_updated=datetime.now()
        )

# Workflow Types
class WorkflowMetadata(BaseModel):
    name: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    author: str
    created: datetime = Field(default_factory=datetime.now)
    tags: List[str] = []
    target_site: str = Field(..., description="Target website URL")

class ScrapingConfig(BaseModel):
    provider: str
    config: Dict[str, Any]

class StorageConfig(BaseModel):
    provider: str
    config: Dict[str, Any]
    schema: Optional[SchemaDefinition] = None

class WorkflowStep(BaseModel):
    id: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+$")
    command: Literal["init", "discover", "extract", "paginate"]
    config: Dict[str, Any]
    retries: int = Field(default=3, ge=0)
    timeout: int = Field(default=30000, gt=0)
    continue_on_error: bool = False

class PostProcessingStep(BaseModel):
    type: Literal["filter", "transform", "validate", "deduplicate"]
    config: Dict[str, Any]

class Workflow(BaseModel):
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    metadata: WorkflowMetadata
    scraping: ScrapingConfig
    storage: StorageConfig
    steps: List[WorkflowStep] = Field(..., min_length=1)
    post_processing: Optional[List[PostProcessingStep]] = None

# Execution Result Types
class StepError(BaseModel):
    code: str
    message: str
    stack: Optional[str] = None

class StepResult(BaseModel):
    step_id: str
    status: Literal["completed", "failed", "skipped"]
    start_time: datetime
    end_time: datetime
    duration: int  # milliseconds
    data: Optional[List[DataElement]] = None
    error: Optional[StepError] = None
    retry_count: int = 0

class WorkflowError(BaseModel):
    step: str
    message: str
    recoverable: bool

class WorkflowResult(BaseModel):
    workflow_id: str
    status: Literal["completed", "failed", "partial"]
    start_time: datetime
    end_time: datetime
    duration: int  # milliseconds
    steps: List[StepResult]
    total_records: int
    storage: Dict[str, str]  # provider and location info
    errors: List[WorkflowError] = []

# Provider Factory Protocol
class ProviderFactory(Protocol):
    """Factory for creating provider instances."""

    async def create_scraping_provider(self, name: str) -> ScrapingProvider:
        """Create scraping provider instance."""
        ...

    async def create_storage_provider(self, name: str) -> StorageProvider:
        """Create storage provider instance."""
        ...

    async def list_providers(
        self,
        type_filter: Optional[Literal["scraping", "storage"]] = None
    ) -> List[ProviderMetadata]:
        """List available providers."""
        ...

    def register_provider(self, provider: ScrapingProvider | StorageProvider) -> None:
        """Register new provider."""
        ...

    async def test_provider(self, name: str, config: ConnectionConfig) -> bool:
        """Test provider connectivity."""
        ...

# Workflow Engine Protocol
class WorkflowEngine(Protocol):
    """Main workflow execution engine."""

    async def execute(self, workflow: Workflow) -> WorkflowResult:
        """Execute workflow from definition."""
        ...

    async def validate(self, workflow: Workflow) -> Dict[str, Any]:
        """Validate workflow definition."""
        ...

    async def get_status(self, workflow_id: str) -> WorkflowResult:
        """Get execution status."""
        ...

    async def cancel(self, workflow_id: str) -> None:
        """Cancel running workflow."""
        ...

# Configuration Classes for different storage types
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

# Configuration Classes for scraping providers
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