"""
Provider factory and registry implementation.
This module provides dynamic provider loading and management.
"""

# Standard library imports
from typing import Dict, List, Optional, Type, Union

# Local imports
from ...providers.scrapers.base import ScrapingProvider, ProviderMetadata
from ...providers.storage.base import StorageProvider, ConnectionConfig


class ProviderRegistry:
    """Registry for managing available providers."""

    def __init__(self):
        self._scraping_providers: Dict[str, Type[ScrapingProvider]] = {}
        self._storage_providers: Dict[str, Type[StorageProvider]] = {}

    def register_scraping_provider(self, name: str, provider_class: Type[ScrapingProvider]) -> None:
        """Register a scraping provider."""
        self._scraping_providers[name] = provider_class

    def register_storage_provider(self, name: str, provider_class: Type[StorageProvider]) -> None:
        """Register a storage provider."""
        self._storage_providers[name] = provider_class

    def get_scraping_provider_class(self, name: str) -> Type[ScrapingProvider]:
        """Get scraping provider class by name."""
        if name not in self._scraping_providers:
            raise ValueError(f"Unknown scraping provider: {name}")
        return self._scraping_providers[name]

    def get_storage_provider_class(self, name: str) -> Type[StorageProvider]:
        """Get storage provider class by name."""
        if name not in self._storage_providers:
            raise ValueError(f"Unknown storage provider: {name}")
        return self._storage_providers[name]

    def list_scraping_providers(self) -> List[str]:
        """List available scraping provider names."""
        return list(self._scraping_providers.keys())

    def list_storage_providers(self) -> List[str]:
        """List available storage provider names."""
        return list(self._storage_providers.keys())

    def list_all_providers(self) -> List[ProviderMetadata]:
        """List all provider metadata."""
        providers = []

        # Add scraping providers
        for name, provider_class in self._scraping_providers.items():
            # Create temporary instance to get metadata
            try:
                instance = provider_class()
                providers.append(instance.metadata)
            except Exception:
                # If instantiation fails, create minimal metadata
                providers.append(
                    ProviderMetadata(name=name, version="unknown", provider_type="scraping", capabilities=[])
                )

        # Add storage providers
        for name, provider_class in self._storage_providers.items():
            try:
                instance = provider_class()
                providers.append(instance.metadata)
            except Exception:
                providers.append(
                    ProviderMetadata(name=name, version="unknown", provider_type="storage", capabilities=[])
                )

        return providers


class ProviderFactory:
    """Factory for creating provider instances."""

    def __init__(self):
        self.registry = ProviderRegistry()
        self._initialize_built_in_providers()

    def _initialize_built_in_providers(self) -> None:
        """Register built-in providers."""
        # Note: Actual provider classes will be imported and registered when they're implemented
        # This is a placeholder for now
        pass

    async def create_scraping_provider(self, name: str) -> ScrapingProvider:
        """Create a scraping provider instance."""
        provider_class = self.registry.get_scraping_provider_class(name)
        return provider_class()

    async def create_storage_provider(self, name: str) -> StorageProvider:
        """Create a storage provider instance."""
        provider_class = self.registry.get_storage_provider_class(name)
        return provider_class()

    async def list_providers(
        self, type_filter: Optional[str] = None
    ) -> List[ProviderMetadata]:
        """List available providers with optional type filter."""
        all_providers = self.registry.list_all_providers()

        if type_filter is None:
            return all_providers

        return [p for p in all_providers if p.type == type_filter]

    def register_provider(self, provider: Union[ScrapingProvider, StorageProvider]) -> None:
        """Register a new provider instance."""
        if hasattr(provider, 'execute_init'):  # Duck typing for scraping provider
            self.registry.register_scraping_provider(
                provider.metadata.name, type(provider)
            )
        elif hasattr(provider, 'connect'):  # Duck typing for storage provider
            self.registry.register_storage_provider(
                provider.metadata.name, type(provider)
            )
        else:
            raise ValueError(f"Unknown provider type: {type(provider)}")

    async def test_provider(self, name: str, config: ConnectionConfig) -> bool:
        """Test provider connectivity."""
        try:
            # Try to create and initialize the provider
            if name in self.registry.list_scraping_providers():
                provider = await self.create_scraping_provider(name)
                await provider.initialize(config)
                return await provider.health_check()
            elif name in self.registry.list_storage_providers():
                provider = await self.create_storage_provider(name)
                await provider.connect(config)
                return await provider.health_check()
            else:
                return False
        except Exception:
            return False


# Global factory instance
_global_factory: Optional[ProviderFactory] = None


def get_provider_factory() -> ProviderFactory:
    """Get the global provider factory instance."""
    global _global_factory
    if _global_factory is None:
        _global_factory = ProviderFactory()
    return _global_factory


def register_scraping_provider(name: str, provider_class: Type[ScrapingProvider]) -> None:
    """Convenience function to register a scraping provider globally."""
    factory = get_provider_factory()
    factory.registry.register_scraping_provider(name, provider_class)


def register_storage_provider(name: str, provider_class: Type[StorageProvider]) -> None:
    """Convenience function to register a storage provider globally."""
    factory = get_provider_factory()
    factory.registry.register_storage_provider(name, provider_class)