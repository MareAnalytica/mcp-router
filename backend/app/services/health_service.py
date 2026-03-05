import logging
import time

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import distinct, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.database import async_session_factory
from app.models.schemas import HealthCheckORM, McpServerORM, UserServerORM

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _check_server(session: AsyncSession, server: McpServerORM) -> None:
    start = time.monotonic()
    status = "healthy"
    error_message = None

    try:
        if server.transport_type == "stdio":
            # For STDIO, we can only verify the command exists; full check needs user keys
            import shutil
            cmd = (server.command or "").split()[0] if server.command else ""
            if cmd and shutil.which(cmd) is None:
                status = "unhealthy"
                error_message = f"Command '{cmd}' not found in PATH"
        elif server.transport_type in ("sse", "streamable_http"):
            import httpx
            async with httpx.AsyncClient(timeout=settings.UPSTREAM_TIMEOUT_SECONDS) as client:
                resp = await client.get(server.url or "", follow_redirects=True)
                if resp.status_code >= 500:
                    status = "unhealthy"
                    error_message = f"HTTP {resp.status_code}"
    except Exception as e:
        status = "error"
        error_message = str(e)[:500]

    elapsed_ms = int((time.monotonic() - start) * 1000)

    check = HealthCheckORM(
        server_id=server.id,
        status=status,
        response_time_ms=elapsed_ms,
        error_message=error_message,
    )
    session.add(check)


async def run_health_checks() -> None:
    async with async_session_factory() as session:
        # Find all servers that have at least one enabled user_server
        stmt = (
            select(McpServerORM)
            .where(
                McpServerORM.id.in_(
                    select(distinct(UserServerORM.server_id)).where(UserServerORM.is_enabled.is_(True))
                )
            )
        )
        result = await session.execute(stmt)
        servers = result.scalars().all()

        for server in servers:
            try:
                await _check_server(session, server)
            except Exception:
                logger.exception("Health check failed for server %s", server.id)

        await session.commit()
        logger.info("Health checks completed for %d servers", len(servers))


def start_health_scheduler() -> None:
    scheduler.add_job(
        run_health_checks,
        "interval",
        seconds=settings.HEALTH_CHECK_INTERVAL_SECONDS,
        id="health_checks",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Health check scheduler started (interval=%ds)", settings.HEALTH_CHECK_INTERVAL_SECONDS)


def stop_health_scheduler() -> None:
    scheduler.shutdown(wait=False)
    logger.info("Health check scheduler stopped")
