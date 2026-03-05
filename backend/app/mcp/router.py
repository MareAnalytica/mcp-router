import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.mcp.aggregator import aggregator
from app.mcp.connection_manager import connection_manager

logger = logging.getLogger(__name__)


async def route_tool_call(
    db_session: AsyncSession,
    user_id: uuid.UUID,
    namespaced_tool_name: str,
    arguments: dict,
) -> dict:
    """Route a tool call to the correct upstream MCP server."""
    _, tool_map = await aggregator.get_tools(db_session, user_id)

    mapping = tool_map.get(namespaced_tool_name)
    if not mapping:
        return {
            "isError": True,
            "content": [{"type": "text", "text": f"Unknown tool: {namespaced_tool_name}"}],
        }

    try:
        session = await connection_manager.get_session(db_session, user_id, mapping.server_id)
        result = await session.call_tool(mapping.original_name, arguments)

        content = []
        for item in result.content:
            if hasattr(item, "text"):
                content.append({"type": "text", "text": item.text})
            elif hasattr(item, "data"):
                content.append({"type": "image", "data": item.data, "mimeType": getattr(item, "mimeType", "image/png")})
            else:
                content.append({"type": "text", "text": str(item)})

        return {
            "isError": result.isError if hasattr(result, "isError") else False,
            "content": content,
        }
    except Exception as e:
        logger.exception("Tool call failed: %s on server %s", namespaced_tool_name, mapping.server_name)
        return {
            "isError": True,
            "content": [{"type": "text", "text": f"Error calling tool: {e}"}],
        }


async def route_resource_read(
    db_session: AsyncSession,
    user_id: uuid.UUID,
    uri: str,
) -> dict:
    """Route a resource read to the correct upstream server."""
    resources = await aggregator.get_resources(db_session, user_id)

    target = None
    for r in resources:
        if r.get("uri") == uri or r.get("_original_uri") == uri:
            target = r
            break

    if not target:
        return {"contents": []}

    server_id = uuid.UUID(target["_server_id"])
    original_uri = target.get("_original_uri", uri)

    try:
        session = await connection_manager.get_session(db_session, user_id, server_id)
        result = await session.read_resource(original_uri)

        contents = []
        for item in result.contents:
            content_dict: dict = {"uri": str(item.uri)}
            if hasattr(item, "text"):
                content_dict["text"] = item.text
            if hasattr(item, "blob"):
                content_dict["blob"] = item.blob
            if hasattr(item, "mimeType"):
                content_dict["mimeType"] = item.mimeType
            contents.append(content_dict)

        return {"contents": contents}
    except Exception as e:
        logger.exception("Resource read failed: %s", uri)
        return {"contents": []}


async def route_prompt_get(
    db_session: AsyncSession,
    user_id: uuid.UUID,
    namespaced_prompt_name: str,
    arguments: dict | None = None,
) -> dict:
    """Route a prompt/get to the correct upstream server."""
    prompts = await aggregator.get_prompts(db_session, user_id)

    target = None
    for p in prompts:
        if p["name"] == namespaced_prompt_name:
            target = p
            break

    if not target:
        return {"description": "", "messages": []}

    server_id = uuid.UUID(target["_server_id"])
    original_name = target["_original_name"]

    try:
        session = await connection_manager.get_session(db_session, user_id, server_id)
        result = await session.get_prompt(original_name, arguments or {})

        messages = []
        for msg in result.messages:
            msg_dict: dict = {"role": msg.role}
            if hasattr(msg.content, "text"):
                msg_dict["content"] = {"type": "text", "text": msg.content.text}
            else:
                msg_dict["content"] = {"type": "text", "text": str(msg.content)}
            messages.append(msg_dict)

        return {
            "description": result.description or "",
            "messages": messages,
        }
    except Exception as e:
        logger.exception("Prompt get failed: %s", namespaced_prompt_name)
        return {"description": "", "messages": []}
