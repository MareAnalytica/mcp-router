import logging
import re
import time
import uuid

from mcp import ClientSession
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.mcp.connection_manager import connection_manager
from app.models.schemas import McpServerORM, UserServerORM

logger = logging.getLogger(__name__)


def _sanitize_name(name: str) -> str:
    """Convert a server name to a safe prefix for tool namespacing."""
    return re.sub(r"[^a-z0-9]", "_", name.lower()).strip("_")


class ToolMapping:
    def __init__(self, server_id: uuid.UUID, server_name: str, original_name: str):
        self.server_id = server_id
        self.server_name = server_name
        self.original_name = original_name


class Aggregator:
    def __init__(self) -> None:
        # Per-user cache: user_id -> {tools, resources, prompts, tool_map, timestamp}
        self._cache: dict[uuid.UUID, dict] = {}
        self._cache_ttl = 300  # 5 minutes

    def invalidate_user_cache(self, user_id: uuid.UUID) -> None:
        self._cache.pop(user_id, None)

    async def get_tools(
        self,
        db_session: AsyncSession,
        user_id: uuid.UUID,
    ) -> tuple[list[dict], dict[str, ToolMapping]]:
        cache = self._cache.get(user_id)
        if cache and (time.monotonic() - cache["timestamp"]) < self._cache_ttl:
            return cache["tools"], cache["tool_map"]

        tools, tool_map = await self._refresh_tools(db_session, user_id)
        return tools, tool_map

    async def get_resources(
        self,
        db_session: AsyncSession,
        user_id: uuid.UUID,
    ) -> list[dict]:
        cache = self._cache.get(user_id)
        if cache and (time.monotonic() - cache["timestamp"]) < self._cache_ttl:
            return cache.get("resources", [])

        await self._refresh_tools(db_session, user_id)
        cache = self._cache.get(user_id)
        return cache.get("resources", []) if cache else []

    async def get_prompts(
        self,
        db_session: AsyncSession,
        user_id: uuid.UUID,
    ) -> list[dict]:
        cache = self._cache.get(user_id)
        if cache and (time.monotonic() - cache["timestamp"]) < self._cache_ttl:
            return cache.get("prompts", [])

        await self._refresh_tools(db_session, user_id)
        cache = self._cache.get(user_id)
        return cache.get("prompts", []) if cache else []

    async def _refresh_tools(
        self,
        db_session: AsyncSession,
        user_id: uuid.UUID,
    ) -> tuple[list[dict], dict[str, ToolMapping]]:
        # Get user's enabled servers
        stmt = (
            select(McpServerORM, UserServerORM)
            .join(UserServerORM, UserServerORM.server_id == McpServerORM.id)
            .where(UserServerORM.user_id == user_id, UserServerORM.is_enabled.is_(True))
        )
        result = await db_session.execute(stmt)
        rows = result.all()

        all_tools: list[dict] = []
        tool_map: dict[str, ToolMapping] = {}
        all_resources: list[dict] = []
        all_prompts: list[dict] = []

        for server, user_server in rows:
            prefix = _sanitize_name(server.name)

            try:
                session: ClientSession = await connection_manager.get_session(
                    db_session, user_id, server.id
                )

                # Fetch tools
                try:
                    tools_result = await session.list_tools()
                    for tool in tools_result.tools:
                        namespaced = f"{prefix}__{tool.name}"
                        tool_dict = {
                            "name": namespaced,
                            "description": tool.description or "",
                            "inputSchema": tool.inputSchema if hasattr(tool, "inputSchema") else {},
                        }
                        all_tools.append(tool_dict)
                        tool_map[namespaced] = ToolMapping(
                            server_id=server.id,
                            server_name=server.name,
                            original_name=tool.name,
                        )
                except Exception:
                    logger.exception("Failed to list tools from server %s", server.name)

                # Fetch resources
                try:
                    resources_result = await session.list_resources()
                    for resource in resources_result.resources:
                        resource_dict = {
                            "uri": str(resource.uri),
                            "name": f"{prefix}__{resource.name}" if resource.name else str(resource.uri),
                            "description": resource.description or "",
                            "mimeType": resource.mimeType if hasattr(resource, "mimeType") else None,
                            "_server_id": str(server.id),
                            "_original_uri": str(resource.uri),
                        }
                        all_resources.append(resource_dict)
                except Exception:
                    logger.debug("Failed to list resources from server %s (may not support resources)", server.name)

                # Fetch prompts
                try:
                    prompts_result = await session.list_prompts()
                    for prompt in prompts_result.prompts:
                        prompt_dict = {
                            "name": f"{prefix}__{prompt.name}",
                            "description": prompt.description or "",
                            "arguments": [
                                {"name": arg.name, "description": arg.description or "", "required": arg.required}
                                for arg in (prompt.arguments or [])
                            ],
                            "_server_id": str(server.id),
                            "_original_name": prompt.name,
                        }
                        all_prompts.append(prompt_dict)
                except Exception:
                    logger.debug("Failed to list prompts from server %s (may not support prompts)", server.name)

            except Exception:
                logger.exception("Failed to connect to server %s for user %s", server.name, user_id)

        self._cache[user_id] = {
            "tools": all_tools,
            "tool_map": tool_map,
            "resources": all_resources,
            "prompts": all_prompts,
            "timestamp": time.monotonic(),
        }

        logger.info(
            "Aggregated for user %s: %d tools, %d resources, %d prompts",
            user_id, len(all_tools), len(all_resources), len(all_prompts),
        )
        return all_tools, tool_map


# Global singleton
aggregator = Aggregator()
