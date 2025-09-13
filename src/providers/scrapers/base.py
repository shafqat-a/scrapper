"""
ScrapingProvider protocol and base class implementation.
This module defines the interface and abstract base class for all scraping providers.
"""

# Standard library imports
from abc import ABC, abstractmethod
from typing import List, Optional, Protocol

# Local imports
from ...scraper_core.models import (
    DataElement,
    PageContext,
    InitStepConfig,
    DiscoverStepConfig,
    ExtractStepConfig,
    PaginateStepConfig,
    ConnectionConfig,
)


class ProviderMetadata:
    """Metadata for provider instances."""

    def __init__(self, name: str, version: str, provider_type: str, capabilities: List[str]):
        self.name = name
        self.version = version
        self.type = provider_type
        self.capabilities = capabilities


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
        self, step_config: DiscoverStepConfig, context: PageContext
    ) -> List[DataElement]:
        """Discover available data elements on the page."""
        ...

    async def execute_extract(
        self, step_config: ExtractStepConfig, context: PageContext
    ) -> List[DataElement]:
        """Extract specific data elements from the page."""
        ...

    async def execute_paginate(
        self, step_config: PaginateStepConfig, context: PageContext
    ) -> Optional[PageContext]:
        """Navigate to next page if available. Returns new context or None."""
        ...

    async def cleanup(self) -> None:
        """Clean up resources (close browser, etc.)."""
        ...

    async def health_check(self) -> bool:
        """Health check for provider availability."""
        ...


class BaseScraper(ABC):
    """Abstract base class for scraping providers."""

    def __init__(self):
        self.metadata = ProviderMetadata(
            name="base-scraper",
            version="1.0.0",
            provider_type="scraping",
            capabilities=[]
        )

    @abstractmethod
    async def initialize(self, config: ConnectionConfig) -> None:
        """Initialize the provider with configuration."""
        pass

    @abstractmethod
    async def execute_init(self, step_config: InitStepConfig) -> PageContext:
        """Navigate to initial URL and setup page context."""
        pass

    @abstractmethod
    async def execute_discover(
        self, step_config: DiscoverStepConfig, context: PageContext
    ) -> List[DataElement]:
        """Discover available data elements on the page."""
        pass

    @abstractmethod
    async def execute_extract(
        self, step_config: ExtractStepConfig, context: PageContext
    ) -> List[DataElement]:
        """Extract specific data elements from the page."""
        pass

    @abstractmethod
    async def execute_paginate(
        self, step_config: PaginateStepConfig, context: PageContext
    ) -> Optional[PageContext]:
        """Navigate to next page if available. Returns new context or None."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources (close browser, etc.)."""
        pass

    async def health_check(self) -> bool:
        """Default health check implementation."""
        return True