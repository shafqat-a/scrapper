#!/usr/bin/env python3
"""
BPDB Archive PDF Scraper
Downloads Page 1 PDFs from BPDB archive and extracts first 5 tables
Exports data to JSON format with parameterized date range
"""

import requests
import pdfplumber
import json
import os
import re
import argparse
import urllib3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class BPDBArchiveScraper:
    """BPDB Archive PDF scraper with date range parameters"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.session = self.create_session()

        # Configuration
        self.base_url = "https://misc.bpdb.gov.bd/daily-generation-archive"
        self.pdf_storage = config.get('pdf_storage', 'bpdb_pdfs/')
        self.output_file = config.get('output_file', 'bpdb_archive_data.json')
        self.delay_between_requests = config.get('delay', 2.0)
        self.verbose = config.get('verbose', False)

        # Date range parameters
        self.from_date = config.get('from_date')
        self.to_date = config.get('to_date')
        self.date_format = '%d/%m/%Y'  # BPDB uses DD/MM/YYYY format

        # Create PDF storage directory
        os.makedirs(self.pdf_storage, exist_ok=True)

        # Statistics
        self.stats = {
            'archive_pages_scraped': 0,
            'pdfs_downloaded': 0,
            'pdfs_processed': 0,
            'tables_extracted': 0,
            'errors': 0,
            'start_time': None
        }

    def create_session(self) -> requests.Session:
        """Create a robust requests session"""
        session = requests.Session()

        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

        return session

    def parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime object"""
        try:
            return datetime.strptime(date_str, self.date_format)
        except ValueError:
            # Try alternative formats
            for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y']:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            raise ValueError(f"Unable to parse date: {date_str}")

    def is_date_in_range(self, date_str: str) -> bool:
        """Check if date falls within specified range"""
        if not self.from_date or not self.to_date:
            return True

        try:
            date_obj = self.parse_date(date_str)
            from_date_obj = self.parse_date(self.from_date)
            to_date_obj = self.parse_date(self.to_date)

            return from_date_obj <= date_obj <= to_date_obj

        except ValueError as e:
            if self.verbose:
                print(f"   ⚠️  Date parsing error for {date_str}: {e}")
            return False

    def scrape_archive_page(self, page_num: int = 1) -> List[Dict[str, str]]:
        """Scrape a single archive page and extract PDF links"""

        url = f"{self.base_url}?page={page_num}" if page_num > 1 else self.base_url

        if self.verbose:
            print(f"📄 Scraping archive page {page_num}: {url}")

        try:
            response = self.session.get(url, verify=False, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find the main data table
            tables = soup.find_all('table')
            if len(tables) < 2:
                if self.verbose:
                    print(f"   ❌ Expected table not found on page {page_num}")
                return []

            data_table = tables[1]  # Second table contains the data
            rows = data_table.find_all('tr')[1:]  # Skip header

            pdf_links = []

            for row in rows:
                cells = row.find_all('td')
                if len(cells) < 3:
                    continue

                # Extract date from second cell
                date_cell = cells[1].get_text(strip=True)

                # Find Page 1 download link (third cell)
                page1_cell = cells[2]
                page1_link = page1_cell.find('a', href=True)

                if page1_link and date_cell:
                    href = page1_link.get('href')
                    full_url = urljoin(self.base_url, href)

                    # Check if date is in range
                    if self.is_date_in_range(date_cell):
                        pdf_links.append({
                            'date': date_cell,
                            'page1_url': full_url,
                            'filename': f"bpdb_page1_{date_cell.replace('/', '_')}.pdf"
                        })

                        if self.verbose:
                            print(f"   ✅ Found PDF for {date_cell}: {full_url}")
                    elif self.verbose:
                        print(f"   ⏭️  Skipped {date_cell} (outside date range)")

            self.stats['archive_pages_scraped'] += 1

            if self.verbose:
                print(f"   📊 Found {len(pdf_links)} PDFs in date range on page {page_num}")

            return pdf_links

        except Exception as e:
            print(f"❌ Error scraping archive page {page_num}: {e}")
            self.stats['errors'] += 1
            return []

    def scrape_all_archive_pages(self, max_pages: int = 10) -> List[Dict[str, str]]:
        """Scrape multiple archive pages to find PDFs in date range"""

        print(f"🔍 Scraping archive pages (max {max_pages} pages)")

        all_pdf_links = []

        for page_num in range(1, max_pages + 1):
            pdf_links = self.scrape_archive_page(page_num)
            all_pdf_links.extend(pdf_links)

            # If no links found, likely reached end of pages
            if not pdf_links:
                if self.verbose:
                    print(f"   ⏹️  No more PDFs found, stopping at page {page_num}")
                break

            # Rate limiting
            if self.delay_between_requests > 0:
                time.sleep(self.delay_between_requests)

        print(f"✅ Found {len(all_pdf_links)} total PDFs in date range")
        return all_pdf_links

    def download_pdf(self, pdf_info: Dict[str, str]) -> Optional[str]:
        """Download a single PDF file"""

        url = pdf_info['page1_url']
        filename = pdf_info['filename']
        filepath = os.path.join(self.pdf_storage, filename)

        # Skip if already downloaded
        if os.path.exists(filepath):
            if self.verbose:
                print(f"   ⏭️  PDF already exists: {filename}")
            return filepath

        try:
            if self.verbose:
                print(f"   📥 Downloading: {filename}")

            response = self.session.get(url, verify=False, timeout=30)
            response.raise_for_status()

            with open(filepath, 'wb') as f:
                f.write(response.content)

            self.stats['pdfs_downloaded'] += 1

            if self.verbose:
                print(f"   ✅ Downloaded {len(response.content)} bytes")

            return filepath

        except Exception as e:
            print(f"   ❌ Error downloading {filename}: {e}")
            self.stats['errors'] += 1
            return None

    def extract_first_5_tables(self, pdf_path: str) -> Dict[str, Any]:
        """Extract first 5 tables from PDF"""

        if self.verbose:
            print(f"   📊 Extracting tables from: {os.path.basename(pdf_path)}")

        try:
            with pdfplumber.open(pdf_path) as pdf:
                if len(pdf.pages) == 0:
                    raise ValueError("PDF has no pages")

                page = pdf.pages[0]
                tables = page.extract_tables()

                if len(tables) < 5:
                    print(f"   ⚠️  Only found {len(tables)} tables (expected 5+)")

                extracted_tables = {}

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

                        if self.verbose:
                            print(f"     ✅ {table_name}: {len(cleaned_table)} rows × {len(cleaned_table[0]) if cleaned_table else 0} cols")

                self.stats['tables_extracted'] += len(extracted_tables)
                return extracted_tables

        except Exception as e:
            print(f"   ❌ Error extracting tables: {e}")
            self.stats['errors'] += 1
            return {}

    def process_pdf_data(self, pdf_info: Dict[str, str], pdf_path: str) -> Dict[str, Any]:
        """Process a single PDF and extract data"""

        date_str = pdf_info['date']

        if self.verbose:
            print(f"📄 Processing PDF for {date_str}")

        # Extract tables
        tables = self.extract_first_5_tables(pdf_path)

        if not tables:
            return {}

        # Structure the data
        pdf_data = {
            'date': date_str,
            'source_pdf': pdf_info['page1_url'],
            'processed_timestamp': datetime.now().isoformat(),
            'tables': tables
        }

        self.stats['pdfs_processed'] += 1

        if self.verbose:
            print(f"   ✅ Processed {len(tables)} tables for {date_str}")

        return pdf_data

    def save_to_json(self, data: List[Dict[str, Any]]) -> None:
        """Save processed data to JSON file"""

        output_data = {
            'metadata': {
                'extraction_timestamp': datetime.now().isoformat(),
                'date_range': {
                    'from_date': self.from_date,
                    'to_date': self.to_date
                },
                'statistics': self.stats,
                'total_records': len(data)
            },
            'data': data
        }

        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            print(f"💾 Data saved to: {self.output_file}")
            print(f"📊 Total records: {len(data)}")

        except Exception as e:
            print(f"❌ Error saving JSON: {e}")

    def run(self) -> None:
        """Main execution function"""

        print("🚀 Starting BPDB Archive PDF Scraper")
        print(f"📅 Date range: {self.from_date} to {self.to_date}")
        print(f"💾 Output file: {self.output_file}")
        print(f"📁 PDF storage: {self.pdf_storage}")
        print(f"⏱️  Request delay: {self.delay_between_requests}s")
        print(f"🗣️  Verbose mode: {'On' if self.verbose else 'Off'}")

        self.stats['start_time'] = time.time()

        try:
            # Step 1: Scrape archive pages to find PDF links
            pdf_links = self.scrape_all_archive_pages(max_pages=20)

            if not pdf_links:
                print("❌ No PDFs found in specified date range")
                return

            print(f"\n📥 Downloading {len(pdf_links)} PDFs...")

            # Step 2: Download PDFs and process them
            processed_data = []

            for i, pdf_info in enumerate(pdf_links, 1):
                print(f"\n[{i}/{len(pdf_links)}] Processing {pdf_info['date']}")

                # Download PDF
                pdf_path = self.download_pdf(pdf_info)

                if pdf_path:
                    # Extract and process data
                    pdf_data = self.process_pdf_data(pdf_info, pdf_path)

                    if pdf_data:
                        processed_data.append(pdf_data)

                # Rate limiting
                if self.delay_between_requests > 0:
                    time.sleep(self.delay_between_requests)

            # Step 3: Save to JSON
            if processed_data:
                self.save_to_json(processed_data)

            # Final statistics
            elapsed = time.time() - self.stats['start_time']
            print(f"\n📊 Final Statistics:")
            print(f"   Archive pages scraped: {self.stats['archive_pages_scraped']}")
            print(f"   PDFs downloaded: {self.stats['pdfs_downloaded']}")
            print(f"   PDFs processed: {self.stats['pdfs_processed']}")
            print(f"   Tables extracted: {self.stats['tables_extracted']}")
            print(f"   Errors: {self.stats['errors']}")
            print(f"   Total time: {elapsed:.1f}s")

            if processed_data:
                print(f"\n✅ Successfully processed {len(processed_data)} PDFs")
                print(f"📄 Data available in: {self.output_file}")
            else:
                print(f"\n⚠️  No data was successfully processed")

        except KeyboardInterrupt:
            print(f"\n⏹️  Process interrupted by user")
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            self.stats['errors'] += 1

def main():
    """Main function with command line arguments"""
    parser = argparse.ArgumentParser(description='BPDB Archive PDF Scraper')

    parser.add_argument('--from-date', type=str, required=True,
                       help='Start date (format: DD/MM/YYYY)')
    parser.add_argument('--to-date', type=str, required=True,
                       help='End date (format: DD/MM/YYYY)')
    parser.add_argument('--output', type=str, default='bpdb_archive_data.json',
                       help='Output JSON file name')
    parser.add_argument('--pdf-storage', type=str, default='bpdb_pdfs/',
                       help='Directory to store downloaded PDFs')
    parser.add_argument('--delay', type=float, default=2.0,
                       help='Delay between requests in seconds')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')

    args = parser.parse_args()

    # Configuration
    config = {
        'from_date': args.from_date,
        'to_date': args.to_date,
        'output_file': args.output,
        'pdf_storage': args.pdf_storage,
        'delay': args.delay,
        'verbose': args.verbose,
    }

    # Create and run scraper
    scraper = BPDBArchiveScraper(config)
    scraper.run()

if __name__ == "__main__":
    main()