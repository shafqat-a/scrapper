"""
Provider Management - Provider factory and registry.

This module handles provider registration, loading, and management
for both scraping and storage providers.
"""

from .factory import (
    ProviderFactory,
    ProviderRegistry,
    get_provider_factory,
    register_scraping_provider,
    register_storage_provider,
)

__all__ = [
    "ProviderFactory",
    "ProviderRegistry",
    "get_provider_factory",
    "register_scraping_provider",
    "register_storage_provider",
]
