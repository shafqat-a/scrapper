"""
BPDB Archive PDF Scraping Provider
Integrates BPDB archive scraping functionality with the scrapper framework.
"""

import asyncio
import json
import os
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import aiohttp
import pdfplumber
import urllib3
from bs4 import BeautifulSoup

from .base import BaseScraper, ProviderMetadata
from ...scraper_core.models import (
    ConnectionConfig,
    DataElement,
    DiscoverStepConfig,
    ExtractStepConfig,
    InitStepConfig,
    PageContext,
    PaginateStepConfig,
)

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class BPDBArchiveProvider(BaseScraper):
    """BPDB Archive PDF scraping provider for the scrapper framework."""

    def __init__(self):
        super().__init__()
        self.metadata = ProviderMetadata(
            name="bpdb-archive",
            version="1.0.0",
            provider_type="scraping",
            capabilities=["pdf-extraction", "date-range", "archive-navigation", "table-extraction"],
        )

        self.session = None
        self.pdf_storage = "bpdb_pdfs/"
        self.archive_base_url = "https://misc.bpdb.gov.bd/daily-generation-archive"
        self.current_page = 1
        self.pdf_links = []
        self.processed_pdfs = []

        # Create PDF storage directory
        os.makedirs(self.pdf_storage, exist_ok=True)

    async def initialize(self, config: ConnectionConfig) -> None:
        """Initialize the BPDB Archive provider."""
        # Create HTTP session
        connector = aiohttp.TCPConnector(ssl=False)  # Disable SSL verification
        self.session = aiohttp.ClientSession(
            connector=connector,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
        )

    async def execute_init(self, step_config: InitStepConfig) -> PageContext:
        """Initialize by discovering available PDFs in the archive."""

        # Extract configuration
        config = step_config.config or {}
        from_date = config.get('from_date')
        to_date = config.get('to_date')

        if not from_date or not to_date:
            raise ValueError("BPDB Archive provider requires 'from_date' and 'to_date' in config")

        # Discover all PDF links in date range
        await self._discover_pdf_links(from_date, to_date)

        return PageContext(
            url=self.archive_base_url,
            page_number=1,
            total_pages=len(self.pdf_links),
            metadata={
                "from_date": from_date,
                "to_date": to_date,
                "total_pdfs": len(self.pdf_links),
                "pdf_links": self.pdf_links
            }
        )

    async def execute_discover(
        self, step_config: DiscoverStepConfig, context: PageContext
    ) -> List[DataElement]:
        """Discover table structures in the archive PDFs."""

        discover_elements = []

        # Sample a few PDFs to discover table structure
        sample_size = min(3, len(self.pdf_links))

        for i, pdf_info in enumerate(self.pdf_links[:sample_size]):
            try:
                # Download and analyze PDF
                pdf_path = await self._download_pdf(pdf_info)
                if pdf_path:
                    tables = await self._extract_tables_from_pdf(pdf_path)

                    for table_name, table_data in tables.items():
                        if table_data:
                            discover_elements.append(DataElement(
                                name=f"{table_name}_{pdf_info['date'].replace('/', '_')}",
                                element_type="table",
                                value=f"Table: {table_name}",
                                attributes={
                                    "table_name": table_name,
                                    "date": pdf_info['date'],
                                    "rows": len(table_data),
                                    "columns": len(table_data[0]) if table_data else 0,
                                    "source_pdf": pdf_info['page1_url']
                                }
                            ))
            except Exception as e:
                # Continue with other PDFs if one fails
                continue

        return discover_elements

    async def execute_extract(
        self, step_config: ExtractStepConfig, context: PageContext
    ) -> List[DataElement]:
        """Extract data from all PDFs in the date range."""

        extracted_elements = []

        for pdf_info in self.pdf_links:
            try:
                # Download PDF
                pdf_path = await self._download_pdf(pdf_info)
                if not pdf_path:
                    continue

                # Extract tables
                tables = await self._extract_tables_from_pdf(pdf_path)
                date_str = pdf_info['date']

                # Create data elements for each table
                for table_name, table_data in tables.items():
                    if table_data:
                        # Convert table to structured format
                        structured_data = {
                            "date": date_str,
                            "table_name": table_name,
                            "source_pdf": pdf_info['page1_url'],
                            "extracted_timestamp": datetime.now().isoformat(),
                            "data": table_data
                        }

                        extracted_elements.append(DataElement(
                            name=f"{table_name}_{date_str.replace('/', '_')}",
                            element_type="structured_data",
                            value=json.dumps(structured_data, ensure_ascii=False),
                            attributes={
                                "date": date_str,
                                "table_name": table_name,
                                "data_type": "bpdb_archive_table",
                                "source_pdf": pdf_info['page1_url'],
                                "rows": len(table_data),
                                "columns": len(table_data[0]) if table_data else 0
                            }
                        ))

                # Add small delay between PDFs
                await asyncio.sleep(0.5)

            except Exception as e:
                # Log error but continue with other PDFs
                print(f"Error processing PDF for {pdf_info['date']}: {e}")
                continue

        return extracted_elements

    async def execute_paginate(
        self, step_config: PaginateStepConfig, context: PageContext
    ) -> Optional[PageContext]:
        """Handle pagination through the PDF list."""

        current_pdf_index = context.page_number - 1

        if current_pdf_index >= len(self.pdf_links) - 1:
            return None  # No more PDFs to process

        return PageContext(
            url=context.url,
            page_number=context.page_number + 1,
            total_pages=context.total_pages,
            metadata=context.metadata
        )

    async def cleanup(self) -> None:
        """Clean up HTTP session and resources."""
        if self.session:
            await self.session.close()

    async def _discover_pdf_links(self, from_date: str, to_date: str) -> None:
        """Discover all PDF links within the specified date range."""

        self.pdf_links = []
        page_num = 1
        max_pages = 20

        while page_num <= max_pages:
            url = f"{self.archive_base_url}?page={page_num}" if page_num > 1 else self.archive_base_url

            try:
                async with self.session.get(url) as response:
                    if response.status != 200:
                        break

                    html_content = await response.text()
                    soup = BeautifulSoup(html_content, 'html.parser')

                    # Find the main data table
                    tables = soup.find_all('table')
                    if len(tables) < 2:
                        break

                    data_table = tables[1]  # Second table contains the data
                    rows = data_table.find_all('tr')[1:]  # Skip header

                    page_links_found = False

                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) < 3:
                            continue

                        # Extract date and Page 1 link
                        date_cell = cells[1].get_text(strip=True)
                        page1_cell = cells[2]
                        page1_link = page1_cell.find('a', href=True)

                        if page1_link and date_cell:
                            if self._is_date_in_range(date_cell, from_date, to_date):
                                href = page1_link.get('href')
                                full_url = urljoin(self.archive_base_url, href)

                                self.pdf_links.append({
                                    'date': date_cell,
                                    'page1_url': full_url,
                                    'filename': f"bpdb_page1_{date_cell.replace('/', '_')}.pdf"
                                })
                                page_links_found = True

                    if not page_links_found:
                        break  # No more relevant links found

                    page_num += 1
                    await asyncio.sleep(1)  # Rate limiting

            except Exception as e:
                print(f"Error scraping archive page {page_num}: {e}")
                break

    def _is_date_in_range(self, date_str: str, from_date: str, to_date: str) -> bool:
        """Check if date falls within specified range."""
        try:
            date_obj = datetime.strptime(date_str, '%d/%m/%Y')
            from_date_obj = datetime.strptime(from_date, '%d/%m/%Y')
            to_date_obj = datetime.strptime(to_date, '%d/%m/%Y')
            return from_date_obj <= date_obj <= to_date_obj
        except ValueError:
            return False

    async def _download_pdf(self, pdf_info: Dict[str, str]) -> Optional[str]:
        """Download a PDF file if not already cached."""

        filename = pdf_info['filename']
        filepath = os.path.join(self.pdf_storage, filename)

        # Skip if already downloaded
        if os.path.exists(filepath):
            return filepath

        try:
            async with self.session.get(pdf_info['page1_url']) as response:
                if response.status == 200:
                    content = await response.read()

                    with open(filepath, 'wb') as f:
                        f.write(content)

                    return filepath
        except Exception as e:
            print(f"Error downloading PDF {filename}: {e}")

        return None

    async def _extract_tables_from_pdf(self, pdf_path: str) -> Dict[str, List[List[str]]]:
        """Extract first 5 tables from PDF using pdfplumber."""

        extracted_tables = {}

        try:
            with pdfplumber.open(pdf_path) as pdf:
                if len(pdf.pages) == 0:
                    return extracted_tables

                page = pdf.pages[0]
                tables = page.extract_tables()

                # Extract first 5 tables with meaningful names
                table_names = [
                    "power_supply_scenario",
                    "zone_wise_generation",
                    "summary_headers",
                    "fuel_cost_summary",
                    "interconnector_import"
                ]

                for i in range(min(5, len(tables))):
                    table_name = table_names[i] if i < len(table_names) else f"table_{i+1}"
                    raw_table = tables[i]

                    if raw_table:
                        # Clean table data
                        cleaned_table = []
                        for row in raw_table:
                            cleaned_row = [cell.strip() if cell else "" for cell in row]
                            cleaned_table.append(cleaned_row)

                        extracted_tables[table_name] = cleaned_table

        except Exception as e:
            print(f"Error extracting tables from {pdf_path}: {e}")

        return extracted_tables