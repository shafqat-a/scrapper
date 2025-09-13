"""
Scrapy scraping provider implementation.
This provider uses Scrapy framework for industrial-grade web scraping.
"""

# Standard library imports
import asyncio
from typing import Dict, List, Optional
from urllib.parse import urljoin

# Third-party imports
import scrapy
from scrapy.crawler import CrawlerRunner
from scrapy.http import Request, Response
from scrapy.selector import Selector
from scrapy.utils.log import configure_logging
from twisted.internet import asyncioreactor

# Configure asyncio reactor before any other twisted imports
try:
    asyncioreactor.install()
except Exception:
    pass  # Already installed

# Third-party imports
from twisted.internet import defer, reactor

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


class ScrapySpider(scrapy.Spider):
    """Internal Scrapy spider for workflow execution."""

    name = "scrapper_spider"

    def __init__(self, scraper_instance, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scraper_instance = scraper_instance
        self.results = []
        self.context = None

    def parse(self, response):
        """Default parse method."""
        self.scraper_instance._current_response = response
        self.scraper_instance._current_selector = Selector(response=response)

        # Store context
        self.context = PageContext(
            url=response.url,
            title=response.css("title::text").get(""),
            metadata={
                "status_code": response.status,
                "content_type": response.headers.get("content-type", b"").decode(),
                "scrapy_spider": self.name,
            },
        )

        return self.context


class ScrapyScraper(BaseScraper):
    """Scrapy-based scraping provider for industrial-grade web scraping."""

    def __init__(self):
        super().__init__()
        self._runner: Optional[CrawlerRunner] = None
        self._config: Optional[ConnectionConfig] = None
        self._current_response: Optional[Response] = None
        self._current_selector: Optional[Selector] = None
        self._spider: Optional[ScrapySpider] = None

    @property
    def metadata(self) -> ProviderMetadata:
        """Provider metadata."""
        return ProviderMetadata(
            name="scrapy",
            version="1.0.0",
            provider_type="scraping",
            capabilities=[
                "javascript_rendering",
                "concurrent_requests",
                "middleware_support",
                "robots_txt",
                "cookies",
                "sessions",
                "retries",
                "caching",
            ],
            description="Industrial-grade web scraping with Scrapy framework",
        )

    async def initialize(self, config: ConnectionConfig) -> None:
        """Initialize the Scrapy scraper with configuration."""
        self._config = config

        # Extract Scrapy-specific config
        scrapy_config = config.get("scrapy", {})

        # Configure logging
        configure_logging({"LOG_LEVEL": "WARNING"})

        # Scrapy settings
        settings = {
            "USER_AGENT": scrapy_config.get(
                "user_agent", "scrapper (+https://github.com/example/scrapper)"
            ),
            "ROBOTSTXT_OBEY": scrapy_config.get("robotstxt_obey", True),
            "CONCURRENT_REQUESTS": scrapy_config.get("concurrent_requests", 16),
            "CONCURRENT_REQUESTS_PER_DOMAIN": scrapy_config.get(
                "concurrent_requests_per_domain", 8
            ),
            "DOWNLOAD_DELAY": scrapy_config.get("download_delay", 1.0),
            "RANDOMIZE_DOWNLOAD_DELAY": scrapy_config.get(
                "randomize_download_delay", 0.5
            ),
            "COOKIES_ENABLED": scrapy_config.get("cookies_enabled", True),
            "TELNETCONSOLE_ENABLED": False,
            "RETRY_ENABLED": scrapy_config.get("retry_enabled", True),
            "RETRY_TIMES": scrapy_config.get("retry_times", 3),
            "RETRY_HTTP_CODES": [500, 502, 503, 504, 408, 429],
        }

        # Create crawler runner
        self._runner = CrawlerRunner(settings)

    async def cleanup(self) -> None:
        """Clean up resources."""
        self._current_response = None
        self._current_selector = None
        self._spider = None

        # Stop reactor if running
        if reactor.running:
            reactor.stop()

    async def health_check(self) -> bool:
        """Check provider health."""
        try:
            if not self._runner:
                return False
            return True
        except Exception:
            return False

    async def execute_init(self, step_config: InitStepConfig) -> PageContext:
        """Execute init step - navigate to URL with Scrapy."""
        if not self._runner:
            raise RuntimeError("Scraper not initialized")

        url = step_config.url

        # Create spider instance
        self._spider = ScrapySpider(self)

        # Set up request with cookies and headers
        request_kwargs = {"url": url}

        if step_config.cookies:
            cookies = {}
            for cookie in step_config.cookies:
                cookies[cookie.name] = cookie.value
            request_kwargs["cookies"] = cookies

        if step_config.headers:
            request_kwargs["headers"] = step_config.headers

        # Create deferred for async execution
        deferred = self._runner.crawl(
            ScrapySpider,
            scraper_instance=self,
            start_requests=[Request(**request_kwargs)],
        )

        # Convert deferred to asyncio future
        future = defer.ensureDeferred(deferred).asFuture(asyncio.get_event_loop())

        try:
            await future
        except Exception as e:
            raise RuntimeError(f"Scrapy crawl failed: {e}")

        if not self._current_response:
            raise RuntimeError("No response received from Scrapy")

        # Handle wait_for
        if step_config.wait_for:
            if isinstance(step_config.wait_for, int):
                await asyncio.sleep(step_config.wait_for / 1000)
            elif isinstance(step_config.wait_for, str):
                # Check if selector exists
                if not self._current_selector.css(step_config.wait_for):
                    raise RuntimeError(
                        f"Wait selector not found: {step_config.wait_for}"
                    )

        return PageContext(
            url=self._current_response.url,
            title=self._current_selector.css("title::text").get(""),
            metadata={
                "status_code": self._current_response.status,
                "content_type": self._current_response.headers.get(
                    "content-type", b""
                ).decode(),
                "scrapy_meta": dict(self._current_response.meta),
            },
        )

    async def execute_discover(
        self, step_config: DiscoverStepConfig, context: PageContext
    ) -> List[DataElement]:
        """Execute discover step - analyze page structure with Scrapy selectors."""
        if not self._current_selector:
            raise RuntimeError("No selector available")

        discovered_elements = []

        for element_type, selector in step_config.selectors.items():
            elements = self._current_selector.css(selector)

            for i, element in enumerate(elements):
                # Extract text and attributes
                text_value = element.css("::text").get("").strip()

                # Get all attributes (Scrapy doesn't expose attributes directly)
                attributes = {}

                discovered_elements.append(
                    DataElement(
                        type=element_type,
                        selector=selector,
                        value=text_value,
                        attributes=attributes,
                        metadata={
                            "index": i,
                            "scrapy_selector": str(element),
                        },
                    )
                )

        return discovered_elements

    async def execute_extract(
        self, step_config: ExtractStepConfig, context: PageContext
    ) -> List[DataElement]:
        """Execute extract step - extract specific data elements with Scrapy."""
        if not self._current_selector:
            raise RuntimeError("No selector available")

        extracted_elements = []

        for field_name, config in step_config.elements.items():
            css_selector = config["selector"]
            extract_type = config.get("type", "text")
            attribute = config.get("attribute")
            transform = config.get("transform")

            elements = self._current_selector.css(css_selector)

            for element in elements:
                # Extract value based on type
                if extract_type == "text":
                    value = element.css("::text").get("").strip()
                elif extract_type == "html":
                    value = element.get()
                elif extract_type == "attribute" and attribute:
                    value = element.css(f"::{attribute}").get("")
                else:
                    value = element.css("::text").get("").strip()

                # Apply transform if specified
                if transform == "float":
                    try:
                        value = float(str(value).replace(",", "").replace("$", ""))
                    except (ValueError, TypeError):
                        value = 0.0
                elif transform == "int":
                    try:
                        value = int(str(value).replace(",", ""))
                    except (ValueError, TypeError):
                        value = 0

                extracted_elements.append(
                    DataElement(
                        type=field_name,
                        selector=css_selector,
                        value=value,
                        attributes={},
                        metadata={
                            "extract_type": extract_type,
                            "transform": transform,
                            "scrapy_selector": str(element),
                        },
                    )
                )

        return extracted_elements

    async def execute_paginate(
        self, step_config: PaginateStepConfig, context: PageContext
    ) -> Optional[PageContext]:
        """Execute paginate step - navigate to next page with Scrapy."""
        if not self._current_selector or not self._current_response:
            raise RuntimeError("No selector or response available")

        # Find next page link
        next_elements = self._current_selector.css(step_config.next_page_selector)
        if not next_elements:
            return None  # No next page found

        # Get URL for next page
        next_url = next_elements.css("::attr(href)").get()
        if not next_url:
            return None  # Cannot determine next URL

        # Resolve relative URL
        next_url = urljoin(self._current_response.url, next_url)

        # Wait after navigation
        await asyncio.sleep(step_config.wait_after_click / 1000)

        # Create new request for next page
        request = Request(
            url=next_url,
            headers=self._current_response.request.headers,
            cookies=getattr(self._current_response.request, "cookies", {}),
        )

        # Execute request (simplified - in real implementation would use proper Scrapy flow)
        deferred = self._runner.crawl(
            ScrapySpider, scraper_instance=self, start_requests=[request]
        )
        future = defer.ensureDeferred(deferred).asFuture(asyncio.get_event_loop())

        try:
            await future
        except Exception:
            return None

        if not self._current_response:
            return None

        return PageContext(
            url=self._current_response.url,
            title=self._current_selector.css("title::text").get(""),
            metadata={
                "status_code": self._current_response.status,
                "content_type": self._current_response.headers.get(
                    "content-type", b""
                ).decode(),
                "page_type": "paginated",
                "scrapy_meta": dict(self._current_response.meta),
            },
        )
