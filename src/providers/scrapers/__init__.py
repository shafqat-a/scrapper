"""
Scraping Providers - Web scraping provider implementations.

This module contains all scraping provider implementations including
Scrapy, Playwright, and BeautifulSoup providers.
"""

# Local folder imports
from .base import BaseScraper, ProviderMetadata, ScrapingProvider

try:
    from .bpdb_archive_provider import BPDBArchiveProvider
    __all__ = [
        "BaseScraper",
        "ScrapingProvider",
        "ProviderMetadata",
        "BPDBArchiveProvider",
    ]
except ImportError:
    __all__ = [
        "BaseScraper",
        "ScrapingProvider",
        "ProviderMetadata",
    ]
