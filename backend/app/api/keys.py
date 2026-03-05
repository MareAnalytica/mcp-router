import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.schemas import ApiKeyResponse, ApiKeySet, UserORM
from app.services.server_service import delete_api_key, get_api_key_names, get_server_by_id, set_api_keys

router = APIRouter(prefix="/api/servers/{server_id}/keys", tags=["keys"])


@router.get("", response_model=list[ApiKeyResponse])
async def list_keys(
    server_id: uuid.UUID,
    user: UserORM = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    result = await get_server_by_id(session, server_id, user.id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")

    keys = await get_api_key_names(session, server_id, user.id)
    return keys


@router.put("")
async def upsert_keys(
    server_id: uuid.UUID,
    data: ApiKeySet,
    user: UserORM = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    result = await get_server_by_id(session, server_id, user.id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")

    await set_api_keys(session, server_id, user.id, data.keys)
    return {"status": "ok"}


@router.delete("/{key_name}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_key(
    server_id: uuid.UUID,
    key_name: str,
    user: UserORM = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    deleted = await delete_api_key(session, server_id, user.id, key_name)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Key not found")
