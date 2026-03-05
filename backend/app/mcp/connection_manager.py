import asyncio
import logging
import os
import time
import uuid
from typing import Any

from mcp import ClientSession
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.mcp.transports.base import BaseTransport
from app.mcp.transports.sse import SSETransport
from app.mcp.transports.stdio import STDIOTransport
from app.mcp.transports.streamable_http import StreamableHTTPTransport
from app.models.schemas import McpServerORM, ServerApiKeyORM
from app.services.vault import decrypt_value

logger = logging.getLogger(__name__)


class _Connection:
    def __init__(self, transport: BaseTransport, session: ClientSession):
        self.transport = transport
        self.session = session
        self.last_used = time.monotonic()

    def touch(self) -> None:
        self.last_used = time.monotonic()


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[tuple[uuid.UUID, uuid.UUID], _Connection] = {}
        self._locks: dict[tuple[uuid.UUID, uuid.UUID], asyncio.Lock] = {}
        self._cleanup_task: asyncio.Task | None = None

    def start(self) -> None:
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self) -> None:
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        for key in list(self._connections.keys()):
            await self._disconnect(key)
        logger.info("ConnectionManager stopped, all connections closed")

    async def get_session(
        self,
        db_session: AsyncSession,
        user_id: uuid.UUID,
        server_id: uuid.UUID,
    ) -> ClientSession:
        key = (user_id, server_id)

        if key not in self._locks:
            self._locks[key] = asyncio.Lock()

        async with self._locks[key]:
            conn = self._connections.get(key)
            if conn and conn.transport.is_connected():
                conn.touch()
                return conn.session

            # Need to establish a new connection
            if conn:
                await self._disconnect(key)

            return await self._connect(db_session, user_id, server_id)

    async def disconnect_user_server(self, user_id: uuid.UUID, server_id: uuid.UUID) -> None:
        key = (user_id, server_id)
        if key in self._locks:
            async with self._locks[key]:
                await self._disconnect(key)

    async def _connect(
        self,
        db_session: AsyncSession,
        user_id: uuid.UUID,
        server_id: uuid.UUID,
    ) -> ClientSession:
        key = (user_id, server_id)

        # Load server config
        result = await db_session.execute(select(McpServerORM).where(McpServerORM.id == server_id))
        server = result.scalar_one_or_none()
        if not server:
            raise ValueError(f"Server {server_id} not found")

        # Load and decrypt user's API keys
        keys_result = await db_session.execute(
            select(ServerApiKeyORM).where(
                ServerApiKeyORM.user_id == user_id,
                ServerApiKeyORM.server_id == server_id,
            )
        )
        api_keys = {k.key_name: decrypt_value(k.encrypted_value) for k in keys_result.scalars().all()}

        # Create transport
        transport: BaseTransport
        if server.transport_type == "sse":
            transport = SSETransport(server_id, user_id)
            # Inject API keys as headers
            headers = dict(server.headers or {})
            for key_name, key_value in api_keys.items():
                headers[key_name] = key_value
            session = await transport.connect(url=server.url, headers=headers)

        elif server.transport_type == "streamable_http":
            transport = StreamableHTTPTransport(server_id, user_id)
            headers = dict(server.headers or {})
            for key_name, key_value in api_keys.items():
                headers[key_name] = key_value
            session = await transport.connect(url=server.url, headers=headers)

        elif server.transport_type == "stdio":
            transport = STDIOTransport(server_id, user_id)
            # Inject API keys as environment variables
            env = dict(os.environ)
            env.update(api_keys)
            session = await transport.connect(
                command=server.command or "",
                args=server.args or [],
                env=env,
            )
        else:
            raise ValueError(f"Unknown transport type: {server.transport_type}")

        self._connections[key] = _Connection(transport, session)
        logger.info("Connection established: user=%s server=%s transport=%s", user_id, server_id, server.transport_type)
        return session

    async def _disconnect(self, key: tuple[uuid.UUID, uuid.UUID]) -> None:
        conn = self._connections.pop(key, None)
        if conn:
            try:
                await conn.transport.disconnect()
            except Exception:
                logger.exception("Error disconnecting transport for key=%s", key)

    async def _cleanup_loop(self) -> None:
        while True:
            await asyncio.sleep(60)
            now = time.monotonic()
            idle_timeout = settings.CONNECTION_IDLE_TIMEOUT_SECONDS

            for key in list(self._connections.keys()):
                conn = self._connections.get(key)
                if conn and (now - conn.last_used) > idle_timeout:
                    logger.info("Evicting idle connection: %s", key)
                    await self._disconnect(key)


# Global singleton
connection_manager = ConnectionManager()
