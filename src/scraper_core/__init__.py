"""
Scraper Core - Core workflow engine for web scraping system.

This package provides the main workflow execution engine, data models,
and provider management for the web scrapper system.
"""

# Local folder imports
from .workflow import WorkflowEngine, WorkflowExecutionError, WorkflowValidationError

__version__ = "0.1.0"

__all__ = [
    "WorkflowEngine",
    "WorkflowExecutionError",
    "WorkflowValidationError",
]
