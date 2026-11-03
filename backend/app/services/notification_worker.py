"""
Notification worker - background task for processing notification outbox.
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from app.infrastructure.config import get_settings
from app.infrastructure.database import db_manager
from app.infrastructure.logging import get_logger
from app.services.notification_service import NotificationService

logger = get_logger(__name__)


class NotificationWorker:
    """Background worker for processing notification outbox."""

    def __init__(
        self,
        poll_interval_seconds: int = 30,
        batch_size: int = 50,
        max_concurrent: int = 10,
    ):
        self.poll_interval = poll_interval_seconds
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        self._semaphore: Optional[asyncio.Semaphore] = None
        self.stats = {
            "cycles": 0,
            "total_processed": 0,
            "total_sent": 0,
            "total_errors": 0,
            "last_cycle": None,
        }

    async def start(self) -> None:
        """Start the worker."""
        if self._running:
            logger.warning("Notification worker already running")
            return

        # Initialize database if not already
        if db_manager._engine is None:
            db_manager.initialize()

        self._running = True
        self._shutdown_event.clear()
        self._semaphore = asyncio.Semaphore(self.max_concurrent)
        self._task = asyncio.create_task(self._run_loop())
        logger.info(
            "notification_worker_started",
            poll_interval=self.poll_interval,
            batch_size=self.batch_size,
            max_concurrent=self.max_concurrent,
        )

    async def stop(self, timeout: float = 30.0) -> None:
        """Stop the worker gracefully."""
        if not self._running:
            return

        logger.info("notification_worker_stopping")
        self._running = False
        self._shutdown_event.set()

        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=timeout)
            except asyncio.TimeoutError:
                logger.warning("notification_worker_stop_timeout")
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass

        logger.info("notification_worker_stopped")

    async def _run_loop(self) -> None:
        """Main worker loop."""
        while self._running:
            try:
                cycle_start = datetime.now(timezone.utc)
                await self._process_batch()
                self.stats["cycles"] += 1
                self.stats["last_cycle"] = cycle_start.isoformat()

                # Wait for next cycle or shutdown
                try:
                    await asyncio.wait_for(
                        self._shutdown_event.wait(),
                        timeout=self.poll_interval,
                    )
                    # Shutdown event was set
                    break
                except asyncio.TimeoutError:
                    # Normal timeout, continue to next cycle
                    pass

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("notification_worker_cycle_error", error=str(e))
                self.stats["total_errors"] += 1
                # Brief pause before retry
                await asyncio.sleep(5)

    async def _process_batch(self) -> None:
        """Process a batch of notifications."""
        async with db_manager.session() as session:
            service = NotificationService(session)
            result = await service.process_pending_notifications(batch_size=self.batch_size)

            self.stats["total_processed"] += result.get("processed", 0)
            self.stats["total_sent"] += result.get("sent", 0)

            if result.get("processed", 0) > 0:
                logger.info(
                    "notification_worker_batch_complete",
                    **result,
                )

    def get_stats(self) -> dict:
        """Get worker statistics."""
        return self.stats.copy()


# Global worker instance
_worker: Optional[NotificationWorker] = None


async def get_notification_worker() -> NotificationWorker:
    """Get or create the global notification worker."""
    global _worker
    if _worker is None:
        settings = get_settings()
        _worker = NotificationWorker(
            poll_interval_seconds=30,
            batch_size=50,
            max_concurrent=10,
        )
    return _worker


async def start_notification_worker() -> None:
    """Start the global notification worker."""
    worker = await get_notification_worker()
    await worker.start()


async def stop_notification_worker() -> None:
    """Stop the global notification worker."""
    global _worker
    if _worker:
        await _worker.stop()
        _worker = None


@asynccontextmanager
async def notification_worker_lifespan():
    """Lifespan context manager for FastAPI integration."""
    await start_notification_worker()
    try:
        yield
    finally:
        await stop_notification_worker()
