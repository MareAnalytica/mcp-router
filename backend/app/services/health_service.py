import asyncio
import logging
import shutil
import time

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import distinct, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.database import async_session_factory
from app.models.schemas import HealthCheckORM, McpServerORM, UserServerORM

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _check_stdio_server(server: McpServerORM) -> tuple[str, str | None]:
    """Check a STDIO MCP server by spawning the process and verifying it starts."""
    cmd = (server.command or "").split()[0] if server.command else ""
    if not cmd:
        return "unhealthy", "No command configured"

    if shutil.which(cmd) is None:
        return "unhealthy", f"Command '{cmd}' not found in PATH"

    # Attempt to actually spawn the process to verify the MCP server package loads.
    # We send a JSON-RPC initialize request and check for any response.
    full_args = [cmd] + (server.args or [])
    try:
        proc = await asyncio.create_subprocess_exec(
            *full_args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Send a minimal JSON-RPC initialize request
        init_request = (
            b'{"jsonrpc":"2.0","id":1,"method":"initialize",'
            b'"params":{"protocolVersion":"2024-11-05",'
            b'"capabilities":{},"clientInfo":{"name":"health-check","version":"1.0"}}}\n'
        )
        proc.stdin.write(init_request)
        await proc.stdin.drain()

        # Wait for up to 15 seconds for any response (process starting + npm install can be slow)
        try:
            stdout = await asyncio.wait_for(proc.stdout.readline(), timeout=15.0)
            # Any non-empty response means the server started successfully
            if stdout and len(stdout.strip()) > 0:
                proc.kill()
                await proc.wait()
                return "healthy", None
            else:
                proc.kill()
                await proc.wait()
                stderr = await proc.stderr.read()
                err_text = stderr.decode(errors="replace")[:300] if stderr else "No response from server"
                return "unhealthy", err_text
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return "unhealthy", "Server did not respond within 15s (may need API keys or package install)"

    except FileNotFoundError:
        return "unhealthy", f"Command '{cmd}' not found"
    except Exception as e:
        return "error", str(e)[:300]


async def _check_server(session: AsyncSession, server: McpServerORM) -> None:
    start = time.monotonic()
    check_status = "healthy"
    error_message = None

    try:
        if server.transport_type == "stdio":
            check_status, error_message = await _check_stdio_server(server)
        elif server.transport_type in ("sse", "streamable_http"):
            import httpx
            async with httpx.AsyncClient(timeout=settings.UPSTREAM_TIMEOUT_SECONDS) as client:
                resp = await client.get(server.url or "", follow_redirects=True)
                if resp.status_code >= 500:
                    check_status = "unhealthy"
                    error_message = f"HTTP {resp.status_code}"
    except Exception as e:
        check_status = "error"
        error_message = str(e)[:500]

    elapsed_ms = int((time.monotonic() - start) * 1000)

    check = HealthCheckORM(
        server_id=server.id,
        status=check_status,
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
