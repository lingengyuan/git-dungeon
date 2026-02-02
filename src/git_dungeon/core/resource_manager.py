"""Resource management for performance and safety."""

from __future__ import annotations

import gc
import os
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Callable, Optional

from git_dungeon.config import GameConfig
from git_dungeon.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class ResourceStats:
    """Resource usage statistics."""

    memory_mb: float = 0
    cpu_percent: float = 0
    active_operations: int = 0
    cached_items: int = 0
    last_gc_time: float = 0


class ResourceManager:
    """Manager for system resources and limits."""

    def __init__(self, config: Optional[GameConfig] = None):
        """Initialize resource manager.

        Args:
            config: Game configuration
        """
        self.config = config or GameConfig()
        self._memory_limit = self.config.max_memory_mb * 1024 * 1024  # Convert to bytes
        self._active_operations: list[str] = []
        self._operation_counts: dict[str, int] = {}
        self._start_time = time.time()

    @property
    def stats(self) -> ResourceStats:
        """Get current resource statistics."""
        import psutil

        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()

        return ResourceStats(
            memory_mb=memory_info.rss / (1024 * 1024),  # type: ignore[assignment]
            cpu_percent=process.cpu_percent(),  # type: ignore[assignment]
            active_operations=len(self._active_operations),
            cached_items=self._operation_counts.get("cache_hits", 0),
            last_gc_time=self._last_gc_time,
        )

    def check_memory(self) -> bool:
        """Check if memory usage is within limits.

        Returns:
            True if within limits, False if over
        """
        stats = self.stats
        return bool(stats.memory_mb < self.config.max_memory_mb)

    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        return self.stats.memory_mb

    @contextmanager
    def track_operation(self, operation_name: str):
        """Context manager to track an operation.

        Usage:
            with resource_manager.track_operation("git_parse"):
                # Do work
                pass
        """
        self._active_operations.append(operation_name)
        self._operation_counts[operation_name] = (
            self._operation_counts.get(operation_name, 0) + 1
        )
        start_time = time.time()

        try:
            yield self
        finally:
            self._active_operations.remove(operation_name)
            duration = time.time() - start_time
            if duration > 1.0:  # Log slow operations
                logger.debug(f"Operation {operation_name} took {duration:.2f}s")

    def force_garbage_collection(self) -> None:
        """Force garbage collection if memory is high."""
        self._last_gc_time = time.time()
        gc.collect()

    def cleanup_cache(self) -> None:
        """Clean up caches to free memory."""
        # This can be extended to clean specific caches
        self.force_garbage_collection()

    def check_operation_allowed(self, operation: str) -> bool:
        """Check if an operation is allowed based on limits.

        Args:
            operation: Operation name

        Returns:
            True if operation can proceed
        """
        # Check concurrent operations
        if len(self._active_operations) >= 10:
            logger.warning("Too many concurrent operations")
            return False

        # Check operation-specific limits
        op_count = self._operation_counts.get(operation, 0)
        if operation == "git_parse" and op_count > self.config.max_commits:
            logger.warning(f"Too many git parse operations: {op_count}")
            return False

        return True  # type: ignore[return-value]

    def record_metric(self, metric: str, value: float) -> None:
        """Record a performance metric.

        Args:
            metric: Metric name
            value: Metric value
        """
        # In a full implementation, this would send to a metrics system
        logger.debug(f"Metric: {metric} = {value}")  # type: ignore[return-value]
        """Record a performance metric.

        Args:
            metric: Metric name
            value: Metric value
        """
        # In a full implementation, this would send to a metrics system
        logger.debug(f"Metric: {metric} = {value}")

    def get_uptime(self) -> float:
        """Get uptime in seconds."""
        return time.time() - self._start_time

    def should_auto_save(self, turn_number: int) -> bool:
        """Check if auto-save should trigger.

        Args:
            turn_number: Current turn number

        Returns:
            True if should auto-save
        """
        if not self.config.auto_save:
            return False
        return turn_number % self.config.auto_save_interval == 0


class ChunkedLoader:
    """Loader that processes data in chunks for large datasets."""

    def __init__(
        self,
        chunk_size: Optional[int] = None,
        on_progress: Optional[Callable[[float], None]] = None,
    ):
        """Initialize chunked loader.

        Args:
            chunk_size: Size of each chunk
            on_progress: Progress callback (0.0 to 1.0)
        """
        import psutil

        self.chunk_size = chunk_size or 100
        self.on_progress = on_progress
        self.psutil = psutil

    def load_large_dataset(
        self,
        data_source: list,
        process_item: Callable,
        max_items: Optional[int] = None,
    ) -> list:
        """Load and process a large dataset in chunks.

        Args:
            data_source: Source data to process
            process_item: Function to process each item
            max_items: Maximum items to process

        Returns:
            List of processed results
        """
        results: list = []
        total_items = min(len(data_source), max_items or len(data_source))

        if total_items == 0:
            return results

        for i, item in enumerate(data_source[:total_items]):
            # Check memory before processing
            process = self.psutil.Process(os.getpid())
            if process.memory_info().rss > 500 * 1024 * 1024:  # 500MB limit
                logger.warning("Memory limit approaching, stopping chunked load")
                break

            try:
                result = process_item(item)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing item {i}: {e}")

            # Yield to event loop periodically
            if (i + 1) % self.chunk_size == 0:
                if self.on_progress:
                    self.on_progress((i + 1) / total_items)

        if self.on_progress:
            self.on_progress(1.0)

        return results


class TimeoutError(Exception):
    """Exception raised when an operation times out."""

    pass


class OperationTimeout:
    """Context manager for operation timeouts."""

    def __init__(self, timeout_seconds: float):
        """Initialize timeout.

        Args:
            timeout_seconds: Maximum time allowed
        """
        self.timeout_seconds = timeout_seconds

    def __enter__(self) -> "OperationTimeout":
        """Start tracking time."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Check if operation timed out."""
        if time.time() - self.start_time > self.timeout_seconds:
            raise TimeoutError(
                f"Operation timed out after {self.timeout_seconds} seconds"
            )


# Import at module level
_last_gc_time = 0.0
