import logging
import uuid
from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from app.mcp.transports.base import BaseTransport

logger = logging.getLogger(__name__)


class STDIOTransport(BaseTransport):
    def __init__(self, server_id: uuid.UUID, user_id: uuid.UUID):
        super().__init__(server_id, user_id)
        self._exit_stack: AsyncExitStack | None = None

    @property
    def transport_type(self) -> str:
        return "stdio"

    async def connect(
        self,
        command: str,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> ClientSession:
        self._exit_stack = AsyncExitStack()
        await self._exit_stack.__aenter__()

        server_params = StdioServerParameters(
            command=command,
            args=args or [],
            env=env,
        )

        transport = await self._exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        read_stream, write_stream = transport

        session = await self._exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        await session.initialize()

        self._session = session
        logger.info("STDIO transport connected for server=%s user=%s (cmd=%s)", self.server_id, self.user_id, command)
        return session

    async def disconnect(self) -> None:
        if self._exit_stack:
            await self._exit_stack.aclose()
            self._exit_stack = None
        self._session = None
        logger.info("STDIO transport disconnected for server=%s user=%s", self.server_id, self.user_id)

    def is_connected(self) -> bool:
        return self._session is not None and self._exit_stack is not None
