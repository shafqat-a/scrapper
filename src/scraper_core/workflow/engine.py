"""
Workflow execution engine for the web scraper system.
This module provides the core workflow orchestration and execution logic.
"""

# Standard library imports
import asyncio
import logging
from typing import Any, Dict, List, Optional

# Local folder imports
# Local imports
from ..models.data_element import DataElement
from ..models.page_context import PageContext
from ..models.provider_config import ConnectionConfig
from ..models.workflow import Workflow
from ..models.workflow_step import WorkflowStep
from ..providers.factory import ProviderFactory, get_provider_factory
from ..providers.scrapers.base import ScrapingProvider
from ..providers.storage.base import StorageProvider
from ..post_processing import create_post_processor

# Configure logging
logger = logging.getLogger(__name__)


class WorkflowExecutionError(Exception):
    """Raised when workflow execution fails."""

    def __init__(
        self,
        message: str,
        step_id: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.step_id = step_id
        self.original_error = original_error


class WorkflowValidationError(Exception):
    """Raised when workflow validation fails."""

    def __init__(self, message: str, field_path: Optional[str] = None):
        super().__init__(message)
        self.field_path = field_path


class WorkflowExecutionResult:
    """Result of workflow execution."""

    def __init__(self):
        self.success: bool = False
        self.total_steps: int = 0
        self.completed_steps: int = 0
        self.failed_steps: int = 0
        self.extracted_data: List[DataElement] = []
        self.execution_time: float = 0.0
        self.errors: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}

    def add_error(self, step_id: str, error: Exception, message: str = ""):
        """Add an error to the execution result."""
        self.errors.append(
            {
                "step_id": step_id,
                "error_type": type(error).__name__,
                "message": message or str(error),
                "original_error": error,
            }
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "success": self.success,
            "total_steps": self.total_steps,
            "completed_steps": self.completed_steps,
            "failed_steps": self.failed_steps,
            "extracted_data_count": len(self.extracted_data),
            "execution_time": self.execution_time,
            "error_count": len(self.errors),
            "errors": [
                {
                    "step_id": err["step_id"],
                    "error_type": err["error_type"],
                    "message": err["message"],
                }
                for err in self.errors
            ],
            "metadata": self.metadata,
        }


class WorkflowEngine:
    """Core workflow execution engine."""

    def __init__(self, provider_factory: Optional[ProviderFactory] = None):
        self.provider_factory = provider_factory or get_provider_factory()
        self.logger = logger

    async def validate_workflow(self, workflow: Workflow) -> None:
        """Validate a workflow definition."""
        try:
            # Basic structure validation is handled by Pydantic
            # Additional business logic validation
            await self._validate_workflow_logic(workflow)
            await self._validate_provider_availability(workflow)
            await self._validate_workflow_steps(workflow)

            self.logger.info(
                f"Workflow '{workflow.metadata.name}' validation successful"
            )

        except Exception as e:
            self.logger.error(f"Workflow validation failed: {e}")
            raise WorkflowValidationError(f"Workflow validation failed: {e}")

    async def execute_workflow(self, workflow: Workflow) -> WorkflowExecutionResult:
        """Execute a complete workflow."""
        result = WorkflowExecutionResult()
        result.total_steps = len(workflow.steps)

        # Standard library imports
        import time

        start_time = time.time()

        # Initialize providers
        scraping_provider = None
        storage_provider = None
        current_context = None

        try:
            self.logger.info(f"Starting workflow execution: {workflow.metadata.name}")

            # Validate workflow before execution
            await self.validate_workflow(workflow)

            # Initialize scraping provider
            scraping_provider = await self.provider_factory.create_scraping_provider(
                workflow.scraping.provider
            )
            await scraping_provider.initialize(
                ConnectionConfig(workflow.scraping.config)
            )

            # Initialize storage provider
            storage_provider = await self.provider_factory.create_storage_provider(
                workflow.storage.provider
            )
            await storage_provider.connect(ConnectionConfig(workflow.storage.config))

            # Execute workflow steps
            for step in workflow.steps:
                try:
                    self.logger.info(f"Executing step: {step.id} ({step.command})")

                    step_result = await self._execute_step(
                        step, scraping_provider, current_context
                    )

                    if step.command == "init":
                        current_context = step_result
                    elif step.command in ["discover", "extract"]:
                        if isinstance(step_result, list):
                            result.extracted_data.extend(step_result)
                    elif step.command == "paginate":
                        if step_result:
                            current_context = step_result

                    result.completed_steps += 1

                except Exception as e:
                    result.failed_steps += 1
                    result.add_error(step.id, e)

                    if not step.continue_on_error:
                        raise WorkflowExecutionError(
                            f"Step {step.id} failed and continue_on_error is False",
                            step_id=step.id,
                            original_error=e,
                        )
                    else:
                        self.logger.warning(
                            f"Step {step.id} failed but continuing: {e}"
                        )

            # Store extracted data if any
            if result.extracted_data and workflow.storage.data_schema:
                await storage_provider.store(
                    result.extracted_data, workflow.storage.data_schema
                )
                self.logger.info(f"Stored {len(result.extracted_data)} data elements")

            # Apply post-processing if defined
            if workflow.post_processing:
                result.extracted_data = await self._apply_post_processing(
                    result.extracted_data, workflow.post_processing
                )

            result.success = result.failed_steps == 0
            result.execution_time = time.time() - start_time

            self.logger.info(
                f"Workflow execution completed: {result.completed_steps}/{result.total_steps} steps successful"
            )

        except Exception as e:
            result.success = False
            result.execution_time = time.time() - start_time

            if isinstance(e, WorkflowExecutionError):
                # Already logged by step execution
                pass
            else:
                result.add_error("workflow", e, "Workflow execution failed")
                self.logger.error(f"Workflow execution failed: {e}")

            raise e

        finally:
            # Cleanup resources
            if scraping_provider:
                try:
                    await scraping_provider.cleanup()
                except Exception as e:
                    self.logger.warning(f"Scraping provider cleanup failed: {e}")

            if storage_provider:
                try:
                    await storage_provider.disconnect()
                except Exception as e:
                    self.logger.warning(f"Storage provider cleanup failed: {e}")

        return result

    async def _execute_step(
        self,
        step: WorkflowStep,
        provider: ScrapingProvider,
        context: Optional[PageContext],
    ) -> Any:
        """Execute a single workflow step."""
        # Apply timeout if specified
        timeout = step.timeout / 1000 if step.timeout else None
        retries = step.retries

        for attempt in range(retries + 1):
            try:
                if step.command == "init":
                    # Local folder imports
                    from ..models.workflow_step import InitStepConfig

                    config = InitStepConfig(**step.config)
                    return await asyncio.wait_for(
                        provider.execute_init(config), timeout=timeout
                    )

                elif step.command == "discover":
                    if not context:
                        raise WorkflowExecutionError(
                            "Discover step requires page context from init step",
                            step_id=step.id,
                        )
                    # Local folder imports
                    from ..models.workflow_step import DiscoverStepConfig

                    config = DiscoverStepConfig(**step.config)
                    return await asyncio.wait_for(
                        provider.execute_discover(config, context), timeout=timeout
                    )

                elif step.command == "extract":
                    if not context:
                        raise WorkflowExecutionError(
                            "Extract step requires page context from init step",
                            step_id=step.id,
                        )
                    # Local folder imports
                    from ..models.workflow_step import ExtractStepConfig

                    config = ExtractStepConfig(**step.config)
                    return await asyncio.wait_for(
                        provider.execute_extract(config, context), timeout=timeout
                    )

                elif step.command == "paginate":
                    if not context:
                        raise WorkflowExecutionError(
                            "Paginate step requires page context from init step",
                            step_id=step.id,
                        )
                    # Local folder imports
                    from ..models.workflow_step import PaginateStepConfig

                    config = PaginateStepConfig(**step.config)
                    return await asyncio.wait_for(
                        provider.execute_paginate(config, context), timeout=timeout
                    )

                else:
                    raise WorkflowExecutionError(
                        f"Unknown step command: {step.command}", step_id=step.id
                    )

            except asyncio.TimeoutError:
                if attempt < retries:
                    self.logger.warning(
                        f"Step {step.id} timed out (attempt {attempt + 1}/{retries + 1}), retrying..."
                    )
                    continue
                else:
                    raise WorkflowExecutionError(
                        f"Step {step.id} timed out after {retries + 1} attempts",
                        step_id=step.id,
                    )

            except Exception as e:
                if attempt < retries:
                    self.logger.warning(
                        f"Step {step.id} failed (attempt {attempt + 1}/{retries + 1}): {e}, retrying..."
                    )
                    await asyncio.sleep(1)  # Brief delay before retry
                    continue
                else:
                    raise WorkflowExecutionError(
                        f"Step {step.id} failed after {retries + 1} attempts: {e}",
                        step_id=step.id,
                        original_error=e,
                    )

    async def _validate_workflow_logic(self, workflow: Workflow) -> None:
        """Validate workflow business logic."""
        # Check that workflow has at least one init step
        init_steps = [step for step in workflow.steps if step.command == "init"]
        if not init_steps:
            raise WorkflowValidationError("Workflow must have at least one 'init' step")

        # Check that init step comes first
        if workflow.steps[0].command != "init":
            raise WorkflowValidationError("First step must be 'init'")

        # Check step dependencies
        has_init = False
        for step in workflow.steps:
            if step.command == "init":
                has_init = True
            elif step.command in ["discover", "extract", "paginate"]:
                if not has_init:
                    raise WorkflowValidationError(
                        f"Step '{step.id}' ({step.command}) requires an 'init' step before it"
                    )

    async def _validate_provider_availability(self, workflow: Workflow) -> None:
        """Validate that required providers are available."""
        # Check scraping provider
        available_scraping = self.provider_factory.registry.list_scraping_providers()
        if workflow.scraping.provider not in available_scraping:
            raise WorkflowValidationError(
                f"Scraping provider '{workflow.scraping.provider}' not available. "
                f"Available: {available_scraping}"
            )

        # Check storage provider
        available_storage = self.provider_factory.registry.list_storage_providers()
        if workflow.storage.provider not in available_storage:
            raise WorkflowValidationError(
                f"Storage provider '{workflow.storage.provider}' not available. "
                f"Available: {available_storage}"
            )

    async def _validate_workflow_steps(self, workflow: Workflow) -> None:
        """Validate individual workflow steps."""
        step_ids = set()

        for step in workflow.steps:
            # Check for duplicate step IDs
            if step.id in step_ids:
                raise WorkflowValidationError(f"Duplicate step ID: {step.id}")
            step_ids.add(step.id)

            # Validate step configuration based on command
            try:
                if step.command == "init":
                    # Local folder imports
                    from ..models.workflow_step import InitStepConfig

                    InitStepConfig(**step.config)
                elif step.command == "discover":
                    # Local folder imports
                    from ..models.workflow_step import DiscoverStepConfig

                    DiscoverStepConfig(**step.config)
                elif step.command == "extract":
                    # Local folder imports
                    from ..models.workflow_step import ExtractStepConfig

                    ExtractStepConfig(**step.config)
                elif step.command == "paginate":
                    # Local folder imports
                    from ..models.workflow_step import PaginateStepConfig

                    PaginateStepConfig(**step.config)
            except Exception as e:
                raise WorkflowValidationError(
                    f"Invalid configuration for step '{step.id}': {e}"
                )

    async def _apply_post_processing(
        self, data: List[DataElement], post_processing_steps
    ) -> List[DataElement]:
        """Apply post-processing steps to extracted data."""
        processed_data = data.copy()

        for step in post_processing_steps:
            step_type = step.type
            config = step.config

            try:
                # Use the new processor system
                processor = create_post_processor(step_type, config)
                initial_count = len(processed_data)
                processed_data = processor.process(processed_data)
                final_count = len(processed_data)

                self.logger.info(
                    f"Applied {step_type} post-processing: {initial_count} -> {final_count} items"
                )

            except ValueError as e:
                self.logger.warning(f"Unknown post-processing step type '{step_type}': {e}")
                continue
            except Exception as e:
                self.logger.error(f"Error in {step_type} post-processing: {e}")
                continue

        return processed_data

