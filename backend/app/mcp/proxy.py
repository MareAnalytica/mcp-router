import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.mcp.aggregator import aggregator
from app.mcp.router import route_prompt_get, route_resource_read, route_tool_call
from app.models.schemas import UserORM
from app.services.auth_service import decode_token

logger = logging.getLogger(__name__)

router = APIRouter(tags=["mcp-proxy"])


def _jsonrpc_error(req_id, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def _jsonrpc_result(req_id, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


@router.post("/api/mcp")
async def mcp_streamable_http(
    request: Request,
    user: UserORM = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Streamable HTTP MCP endpoint. Accepts JSON-RPC requests from AI agents."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(_jsonrpc_error(None, -32700, "Parse error"), status_code=400)

    # Handle batch requests
    if isinstance(body, list):
        results = []
        for item in body:
            result = await _handle_jsonrpc(item, user, session)
            if result is not None:
                results.append(result)
        return JSONResponse(results if results else None, status_code=200 if results else 204)

    result = await _handle_jsonrpc(body, user, session)
    if result is None:
        return JSONResponse(None, status_code=204)  # Notification
    return JSONResponse(result)


async def _handle_jsonrpc(body: dict, user: UserORM, session: AsyncSession) -> dict | None:
    req_id = body.get("id")
    method = body.get("method", "")
    params = body.get("params", {})

    # Notifications (no id) don't get a response
    if req_id is None and method not in ("initialize",):
        return None

    try:
        if method == "initialize":
            return _jsonrpc_result(req_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": False},
                    "resources": {"subscribe": False, "listChanged": False},
                    "prompts": {"listChanged": False},
                },
                "serverInfo": {
                    "name": "mcp-router",
                    "version": "1.0.0",
                },
            })

        elif method == "notifications/initialized":
            return None

        elif method == "tools/list":
            tools, _ = await aggregator.get_tools(session, user.id)
            return _jsonrpc_result(req_id, {"tools": tools})

        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            result = await route_tool_call(session, user.id, tool_name, arguments)
            return _jsonrpc_result(req_id, result)

        elif method == "resources/list":
            resources = await aggregator.get_resources(session, user.id)
            # Strip internal fields
            clean = [
                {k: v for k, v in r.items() if not k.startswith("_")}
                for r in resources
            ]
            return _jsonrpc_result(req_id, {"resources": clean})

        elif method == "resources/read":
            uri = params.get("uri", "")
            result = await route_resource_read(session, user.id, uri)
            return _jsonrpc_result(req_id, result)

        elif method == "prompts/list":
            prompts = await aggregator.get_prompts(session, user.id)
            clean = [
                {k: v for k, v in p.items() if not k.startswith("_")}
                for p in prompts
            ]
            return _jsonrpc_result(req_id, {"prompts": clean})

        elif method == "prompts/get":
            prompt_name = params.get("name", "")
            arguments = params.get("arguments", {})
            result = await route_prompt_get(session, user.id, prompt_name, arguments)
            return _jsonrpc_result(req_id, result)

        elif method == "ping":
            return _jsonrpc_result(req_id, {})

        else:
            return _jsonrpc_error(req_id, -32601, f"Method not found: {method}")

    except Exception as e:
        logger.exception("Error handling MCP method %s", method)
        return _jsonrpc_error(req_id, -32603, f"Internal error: {e}")
