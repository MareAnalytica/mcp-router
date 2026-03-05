import logging
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.mcp.connection_manager import connection_manager
from app.models.schemas import (
    ServerCreate,
    ServerResponse,
    ServerUpdate,
    UserORM,
)
from app.services.server_service import (
    create_server,
    delete_server,
    get_server_by_id,
    get_user_servers,
    toggle_server,
    update_server,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/servers", tags=["servers"])


@router.get("", response_model=list[ServerResponse])
async def list_servers(
    user: UserORM = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    servers = await get_user_servers(session, user.id)
    result = []
    for server, is_enabled in servers:
        resp = ServerResponse.model_validate(server)
        resp.is_enabled = is_enabled
        result.append(resp)
    return result


@router.post("", response_model=ServerResponse, status_code=status.HTTP_201_CREATED)
async def add_server(
    data: ServerCreate,
    user: UserORM = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    server = await create_server(session, user.id, data)
    resp = ServerResponse.model_validate(server)
    resp.is_enabled = True
    return resp


@router.get("/{server_id}", response_model=ServerResponse)
async def get_server(
    server_id: uuid.UUID,
    user: UserORM = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    result = await get_server_by_id(session, server_id, user.id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")

    server, is_enabled = result
    resp = ServerResponse.model_validate(server)
    resp.is_enabled = is_enabled
    return resp


@router.patch("/{server_id}", response_model=ServerResponse)
async def edit_server(
    server_id: uuid.UUID,
    data: ServerUpdate,
    user: UserORM = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    # Verify user has access
    result = await get_server_by_id(session, server_id, user.id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")

    server = await update_server(session, server_id, data)
    resp = ServerResponse.model_validate(server)
    resp.is_enabled = result[1]
    return resp


@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_server(
    server_id: uuid.UUID,
    user: UserORM = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    deleted = await delete_server(session, server_id, user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")


@router.post("/{server_id}/toggle")
async def toggle(
    server_id: uuid.UUID,
    user: UserORM = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    new_state = await toggle_server(session, server_id, user.id)
    if new_state is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")
    return {"is_enabled": new_state}


@router.post("/{server_id}/test")
async def test_connection(
    server_id: uuid.UUID,
    user: UserORM = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Test an actual MCP connection: connect, initialize, list tools, then disconnect."""
    result = await get_server_by_id(session, server_id, user.id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")

    server, _ = result
    start = time.monotonic()
    try:
        mcp_session = await connection_manager.get_session(session, user.id, server_id)
        tools_result = await mcp_session.list_tools()
        elapsed_ms = int((time.monotonic() - start) * 1000)

        tool_names = [t.name for t in tools_result.tools]
        return {
            "status": "ok",
            "server_name": server.name,
            "transport_type": server.transport_type,
            "response_time_ms": elapsed_ms,
            "tools_count": len(tool_names),
            "tools": tool_names[:50],  # cap at 50 for readability
        }
    except BaseException as e:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        logger.exception("Connection test failed for server %s (user %s)", server_id, user.id)
        # Tear down the broken connection so next attempt starts fresh
        try:
            await connection_manager.disconnect_user_server(user.id, server_id)
        except Exception:
            pass
        return {
            "status": "error",
            "server_name": server.name,
            "transport_type": server.transport_type,
            "response_time_ms": elapsed_ms,
            "tools_count": 0,
            "tools": [],
            "error": str(e)[:500],
        }
