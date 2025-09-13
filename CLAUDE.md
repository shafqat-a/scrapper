# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a web scraper system built on a provider-based architecture that allows plugging in different scraping methods for different websites. The system uses JSON workflow definitions to configure scraping processes.

## Core Architecture

### Provider Model
- **Scraping Providers**: Different scraping strategies for different websites
- **Storage Providers**: Multiple data storage options (CSV, PostgreSQL, SQL Server, MongoDB, etc.)
- **Workflow Engine**: JSON-based workflow definition and execution

### Scraping Workflow Process
1. **Init**: Navigate to target website URL and scan
2. **Discovery**: Analyze page structure to identify available data
3. **Extraction**: Scrape and grab identified data elements
4. **Pagination**: Navigate to additional pages if available
5. **Post-processing**: Optional data transformation and cleanup

### Key Components
- Workflow definitions stored as JSON files
- Command-based workflow steps
- Pluggable provider system for both scraping and storage
- Support for multi-page scraping with navigation logic

## Development Notes

This project is designed to be configured through JSON workflow files rather than hard-coded scraping logic. When implementing new features, prioritize:

1. **Provider Pattern**: New scraping methods should be implemented as providers
2. **JSON Configuration**: Workflow steps should be definable in JSON format
3. **Modularity**: Each scraping command should be independent and composable
4. **Storage Flexibility**: Support multiple storage backends through provider pattern

## Project Status
This appears to be a new project with only the specification defined. Implementation will need to establish the core provider architecture and workflow engine.