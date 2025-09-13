"""
BeautifulSoup scraping provider implementation.
This provider uses requests + BeautifulSoup for lightweight HTML parsing.
"""

# Standard library imports
import asyncio
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

# Third-party imports
import aiohttp
from bs4 import BeautifulSoup

# Local folder imports
# Local imports
from ...scraper_core.models.data_element import DataElement
from ...scraper_core.models.page_context import PageContext
from ...scraper_core.models.provider_config import ConnectionConfig, ProviderMetadata
from ...scraper_core.models.workflow_step import (
    DiscoverStepConfig,
    ExtractStepConfig,
    InitStepConfig,
    PaginateStepConfig,
)
from .base import BaseScraper


class BeautifulSoupScraper(BaseScraper):
    """BeautifulSoup-based scraping provider for lightweight HTML parsing."""

    def __init__(self):
        super().__init__()
        self._session: Optional[aiohttp.ClientSession] = None
        self._config: Optional[ConnectionConfig] = None
        self._current_soup: Optional[BeautifulSoup] = None
        self._current_url: Optional[str] = None

    @property
    def metadata(self) -> ProviderMetadata:
        """Provider metadata."""
        return ProviderMetadata(
            name="beautifulsoup",
            version="1.0.0",
            provider_type="scraping",
            capabilities=["html_parsing", "css_selectors", "form_handling"],
            description="Lightweight HTML parsing with BeautifulSoup and aiohttp",
        )

    async def initialize(self, config: ConnectionConfig) -> None:
        """Initialize the BeautifulSoup scraper with configuration."""
        self._config = config

        # Extract BeautifulSoup-specific config
        bs_config = config.get("beautifulsoup", {})
        parser = bs_config.get("parser", "html.parser")
        timeout = bs_config.get("timeout", 30)
        headers = bs_config.get("headers", {})

        # Set default headers
        default_headers = {
            "User-Agent": "Mozilla/5.0 (compatible; scrapper/1.0.0)",
        }
        default_headers.update(headers)

        # Create aiohttp session
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=10)
        timeout_config = aiohttp.ClientTimeout(total=timeout)

        self._session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout_config,
            headers=default_headers,
        )

        self._parser = parser

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._session:
            await self._session.close()
            self._session = None
        self._current_soup = None
        self._current_url = None

    async def health_check(self) -> bool:
        """Check provider health."""
        if not self._session or self._session.closed:
            return False

        try:
            # Test with a simple request
            async with self._session.get("https://httpbin.org/status/200") as response:
                return response.status == 200
        except Exception:
            return False

    async def execute_init(self, step_config: InitStepConfig) -> PageContext:
        """Execute init step - navigate to URL and parse HTML."""
        if not self._session:
            raise RuntimeError("Scraper not initialized")

        url = step_config.url

        # Set cookies if provided
        cookies = {}
        for cookie in step_config.cookies:
            cookies[cookie.name] = cookie.value

        # Set headers
        headers = dict(step_config.headers)

        # Make request
        async with self._session.get(url, cookies=cookies, headers=headers) as response:
            if response.status != 200:
                raise RuntimeError(f"HTTP {response.status}: {await response.text()}")

            html_content = await response.text()

        # Parse with BeautifulSoup
        self._current_soup = BeautifulSoup(html_content, self._parser)
        self._current_url = str(response.url)

        # Wait if specified
        if step_config.wait_for:
            if isinstance(step_config.wait_for, int):
                await asyncio.sleep(step_config.wait_for / 1000)
            elif isinstance(step_config.wait_for, str):
                # Check if selector exists
                if not self._current_soup.select(step_config.wait_for):
                    raise RuntimeError(
                        f"Wait selector not found: {step_config.wait_for}"
                    )

        return PageContext(
            url=self._current_url,
            title=self._current_soup.title.string if self._current_soup.title else "",
            metadata={
                "status_code": response.status,
                "content_type": response.headers.get("content-type", ""),
                "parsed_with": self._parser,
            },
        )

    async def execute_discover(
        self, step_config: DiscoverStepConfig, context: PageContext
    ) -> List[DataElement]:
        """Execute discover step - analyze page structure."""
        if not self._current_soup:
            raise RuntimeError("No parsed content available")

        discovered_elements = []

        for element_type, selector in step_config.selectors.items():
            elements = self._current_soup.select(selector)

            for i, element in enumerate(elements):
                discovered_elements.append(
                    DataElement(
                        type=element_type,
                        selector=selector,
                        value=element.get_text(strip=True),
                        attributes=dict(element.attrs),
                        metadata={
                            "tag_name": element.name,
                            "index": i,
                            "xpath": self._get_xpath_for_element(element),
                        },
                    )
                )

        return discovered_elements

    async def execute_extract(
        self, step_config: ExtractStepConfig, context: PageContext
    ) -> List[DataElement]:
        """Execute extract step - extract specific data elements."""
        if not self._current_soup:
            raise RuntimeError("No parsed content available")

        extracted_elements = []

        for field_name, config in step_config.elements.items():
            selector = config["selector"]
            extract_type = config.get("type", "text")
            attribute = config.get("attribute")
            transform = config.get("transform")

            elements = self._current_soup.select(selector)

            for element in elements:
                # Extract value based on type
                if extract_type == "text":
                    value = element.get_text(strip=True)
                elif extract_type == "html":
                    value = str(element)
                elif extract_type == "attribute" and attribute:
                    value = element.get(attribute, "")
                else:
                    value = element.get_text(strip=True)

                # Apply transform if specified
                if transform == "float":
                    try:
                        value = float(value.replace(",", "").replace("$", ""))
                    except (ValueError, AttributeError):
                        value = 0.0
                elif transform == "int":
                    try:
                        value = int(value.replace(",", ""))
                    except (ValueError, AttributeError):
                        value = 0

                extracted_elements.append(
                    DataElement(
                        type=field_name,
                        selector=selector,
                        value=value,
                        attributes=(
                            dict(element.attrs) if hasattr(element, "attrs") else {}
                        ),
                        metadata={
                            "extract_type": extract_type,
                            "transform": transform,
                            "tag_name": element.name,
                        },
                    )
                )

        return extracted_elements

    async def execute_paginate(
        self, step_config: PaginateStepConfig, context: PageContext
    ) -> Optional[PageContext]:
        """Execute paginate step - navigate to next page."""
        if not self._current_soup or not self._session:
            raise RuntimeError("No parsed content or session available")

        # Find next page link
        next_elements = self._current_soup.select(step_config.next_page_selector)
        if not next_elements:
            return None  # No next page found

        next_element = next_elements[0]

        # Get URL for next page
        if next_element.name == "a" and next_element.get("href"):
            next_url = urljoin(self._current_url, next_element["href"])
        else:
            return None  # Cannot determine next URL

        # Wait after navigation
        await asyncio.sleep(step_config.wait_after_click / 1000)

        # Navigate to next page
        async with self._session.get(next_url) as response:
            if response.status != 200:
                return None

            html_content = await response.text()

        # Parse new page
        self._current_soup = BeautifulSoup(html_content, self._parser)
        self._current_url = str(response.url)

        return PageContext(
            url=self._current_url,
            title=self._current_soup.title.string if self._current_soup.title else "",
            metadata={
                "status_code": response.status,
                "content_type": response.headers.get("content-type", ""),
                "parsed_with": self._parser,
                "page_type": "paginated",
            },
        )

    def _get_xpath_for_element(self, element) -> str:
        """Generate XPath for BeautifulSoup element (simplified)."""
        components = []
        for parent in element.parents:
            if parent.name:
                siblings = parent.find_all(parent.name, recursive=False)
                if len(siblings) > 1:
                    index = siblings.index(parent) + 1
                    components.append(f"{parent.name}[{index}]")
                else:
                    components.append(parent.name)

        components.reverse()
        return "/" + "/".join(components) if components else f"/{element.name}"
