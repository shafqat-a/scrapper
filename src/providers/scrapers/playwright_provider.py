"""
Playwright scraping provider implementation.
This provider uses Playwright for JavaScript-heavy sites requiring browser automation.
"""

# Standard library imports
import asyncio
from typing import Dict, List, Optional

# Third-party imports
from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)

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


class PlaywrightScraper(BaseScraper):
    """Playwright-based scraping provider for JavaScript-heavy sites."""

    def __init__(self):
        super().__init__()
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._config: Optional[ConnectionConfig] = None

    @property
    def metadata(self) -> ProviderMetadata:
        """Provider metadata."""
        return ProviderMetadata(
            name="playwright",
            version="1.0.0",
            provider_type="scraping",
            capabilities=[
                "javascript_execution",
                "browser_automation",
                "file_downloads",
                "screenshot_capture",
                "network_interception",
                "mobile_emulation",
                "geolocation",
                "cookies",
                "local_storage",
            ],
            description="Full browser automation with Playwright for JavaScript-heavy sites",
        )

    async def initialize(self, config: ConnectionConfig) -> None:
        """Initialize the Playwright scraper with configuration."""
        self._config = config

        # Extract Playwright-specific config
        pw_config = config.get("playwright", {})
        browser_type = pw_config.get("browser", "chromium")  # chromium, firefox, webkit
        headless = pw_config.get("headless", True)
        timeout = pw_config.get("timeout", 30000)
        viewport = pw_config.get("viewport", {"width": 1280, "height": 720})
        user_agent = pw_config.get(
            "user_agent",
            "Mozilla/5.0 (compatible; scrapper/1.0.0)",
        )

        # Start Playwright
        self._playwright = await async_playwright().start()

        # Launch browser
        if browser_type == "firefox":
            browser = self._playwright.firefox
        elif browser_type == "webkit":
            browser = self._playwright.webkit
        else:
            browser = self._playwright.chromium

        self._browser = await browser.launch(
            headless=headless,
            args=pw_config.get("browser_args", []),
        )

        # Create browser context
        context_options = {
            "viewport": viewport,
            "user_agent": user_agent,
            "java_script_enabled": pw_config.get("javascript_enabled", True),
            "accept_downloads": pw_config.get("accept_downloads", False),
        }

        # Add geolocation if specified
        if "geolocation" in pw_config:
            context_options["geolocation"] = pw_config["geolocation"]
            context_options["permissions"] = ["geolocation"]

        self._context = await self._browser.new_context(**context_options)

        # Set default timeouts
        self._context.set_default_timeout(timeout)
        self._context.set_default_navigation_timeout(timeout)

        # Create page
        self._page = await self._context.new_page()

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._page:
            await self._page.close()
            self._page = None

        if self._context:
            await self._context.close()
            self._context = None

        if self._browser:
            await self._browser.close()
            self._browser = None

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    async def health_check(self) -> bool:
        """Check provider health."""
        if not self._page or not self._browser:
            return False

        try:
            # Test with a simple navigation
            await self._page.goto("data:text/html,<h1>Health Check</h1>", timeout=5000)
            return True
        except Exception:
            return False

    async def execute_init(self, step_config: InitStepConfig) -> PageContext:
        """Execute init step - navigate to URL with Playwright."""
        if not self._page:
            raise RuntimeError("Scraper not initialized")

        # Set cookies if provided
        if step_config.cookies:
            cookies = []
            for cookie in step_config.cookies:
                cookies.append(
                    {
                        "name": cookie.name,
                        "value": cookie.value,
                        "domain": cookie.domain,
                        "path": cookie.path,
                        "expires": cookie.expires,
                        "httpOnly": cookie.http_only,
                        "secure": cookie.secure,
                    }
                )
            await self._context.add_cookies(cookies)

        # Set extra headers
        if step_config.headers:
            await self._page.set_extra_http_headers(step_config.headers)

        # Navigate to URL
        response = await self._page.goto(step_config.url, wait_until="domcontentloaded")

        if not response or not response.ok:
            raise RuntimeError(
                f"Navigation failed: {response.status if response else 'No response'}"
            )

        # Wait for condition if specified
        if step_config.wait_for:
            if isinstance(step_config.wait_for, int):
                await asyncio.sleep(step_config.wait_for / 1000)
            elif isinstance(step_config.wait_for, str):
                try:
                    await self._page.wait_for_selector(
                        step_config.wait_for, timeout=30000
                    )
                except Exception as e:
                    raise RuntimeError(
                        f"Wait selector not found: {step_config.wait_for} - {e}"
                    )

        # Get page title
        title = await self._page.title()

        return PageContext(
            url=self._page.url,
            title=title,
            metadata={
                "status_code": response.status,
                "content_type": response.headers.get("content-type", ""),
                "user_agent": await self._page.evaluate("navigator.userAgent"),
                "viewport": await self._page.viewport_size(),
            },
        )

    async def execute_discover(
        self, step_config: DiscoverStepConfig, context: PageContext
    ) -> List[DataElement]:
        """Execute discover step - analyze page structure with Playwright."""
        if not self._page:
            raise RuntimeError("No page available")

        discovered_elements = []

        for element_type, selector in step_config.selectors.items():
            elements = await self._page.query_selector_all(selector)

            for i, element in enumerate(elements):
                # Get text content
                text_content = await element.text_content()

                # Get attributes
                attributes = await element.evaluate(
                    "el => Object.fromEntries(Array.from(el.attributes).map(attr => [attr.name, attr.value]))"
                )

                # Get bounding box for metadata
                try:
                    bounding_box = await element.bounding_box()
                except Exception:
                    bounding_box = None

                discovered_elements.append(
                    DataElement(
                        type=element_type,
                        selector=selector,
                        value=text_content.strip() if text_content else "",
                        attributes=attributes or {},
                        metadata={
                            "index": i,
                            "bounding_box": bounding_box,
                            "tag_name": await element.evaluate(
                                "el => el.tagName.toLowerCase()"
                            ),
                        },
                    )
                )

        return discovered_elements

    async def execute_extract(
        self, step_config: ExtractStepConfig, context: PageContext
    ) -> List[DataElement]:
        """Execute extract step - extract specific data elements with Playwright."""
        if not self._page:
            raise RuntimeError("No page available")

        extracted_elements = []

        for field_name, config in step_config.elements.items():
            selector = config["selector"]
            extract_type = config.get("type", "text")
            attribute = config.get("attribute")
            transform = config.get("transform")

            elements = await self._page.query_selector_all(selector)

            for element in elements:
                # Extract value based on type
                if extract_type == "text":
                    value = await element.text_content()
                    value = value.strip() if value else ""
                elif extract_type == "html":
                    value = await element.inner_html()
                elif extract_type == "attribute" and attribute:
                    value = await element.get_attribute(attribute)
                    value = value or ""
                else:
                    value = await element.text_content()
                    value = value.strip() if value else ""

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

                # Get attributes
                try:
                    attributes = await element.evaluate(
                        "el => Object.fromEntries(Array.from(el.attributes).map(attr => [attr.name, attr.value]))"
                    )
                except Exception:
                    attributes = {}

                extracted_elements.append(
                    DataElement(
                        type=field_name,
                        selector=selector,
                        value=value,
                        attributes=attributes or {},
                        metadata={
                            "extract_type": extract_type,
                            "transform": transform,
                            "tag_name": await element.evaluate(
                                "el => el.tagName.toLowerCase()"
                            ),
                        },
                    )
                )

        return extracted_elements

    async def execute_paginate(
        self, step_config: PaginateStepConfig, context: PageContext
    ) -> Optional[PageContext]:
        """Execute paginate step - navigate to next page with Playwright."""
        if not self._page:
            raise RuntimeError("No page available")

        # Find next page element
        next_element = await self._page.query_selector(step_config.next_page_selector)
        if not next_element:
            return None  # No next page found

        # Check if element is visible and enabled
        is_visible = await next_element.is_visible()
        is_enabled = await next_element.is_enabled()

        if not is_visible or not is_enabled:
            return None  # Cannot click next page

        # Wait for network to be idle before clicking
        try:
            # Click the next page element
            await next_element.click()

            # Wait for navigation or content update
            try:
                await self._page.wait_for_load_state("networkidle", timeout=30000)
            except Exception:
                # Fallback: just wait for the specified time
                await asyncio.sleep(step_config.wait_after_click / 1000)

        except Exception:
            return None  # Click failed

        # Additional wait if specified
        if step_config.wait_after_click > 0:
            await asyncio.sleep(step_config.wait_after_click / 1000)

        # Get updated page information
        title = await self._page.title()

        return PageContext(
            url=self._page.url,
            title=title,
            metadata={
                "page_type": "paginated",
                "viewport": await self._page.viewport_size(),
                "user_agent": await self._page.evaluate("navigator.userAgent"),
            },
        )
