from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.schemas import (
    CatalogEntryResponse,
    McpServerORM,
    UserORM,
    UserServerORM,
)

router = APIRouter(prefix="/api/catalog", tags=["catalog"])


@router.get("", response_model=list[CatalogEntryResponse])
async def list_catalog(
    search: str | None = None,
    category: str | None = None,
    user: UserORM = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    stmt = select(McpServerORM).where(McpServerORM.is_catalog.is_(True))

    if search:
        stmt = stmt.where(McpServerORM.name.ilike(f"%{search}%"))
    if category:
        stmt = stmt.where(McpServerORM.category == category)

    stmt = stmt.order_by(McpServerORM.name)
    result = await session.execute(stmt)
    servers = result.scalars().all()

    # Check which catalog items the user has enabled
    user_server_stmt = select(UserServerORM.server_id).where(UserServerORM.user_id == user.id)
    user_result = await session.execute(user_server_stmt)
    enabled_ids = {row[0] for row in user_result.all()}

    entries = []
    for server in servers:
        entry = CatalogEntryResponse.model_validate(server)
        entry.is_enabled_by_user = server.id in enabled_ids
        entries.append(entry)

    return entries


@router.get("/{slug}", response_model=CatalogEntryResponse)
async def get_catalog_entry(
    slug: str,
    user: UserORM = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    result = await session.execute(select(McpServerORM).where(McpServerORM.catalog_slug == slug))
    server = result.scalar_one_or_none()
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Catalog entry not found")

    user_server_stmt = select(UserServerORM).where(
        UserServerORM.user_id == user.id, UserServerORM.server_id == server.id
    )
    user_result = await session.execute(user_server_stmt)
    is_enabled = user_result.scalar_one_or_none() is not None

    entry = CatalogEntryResponse.model_validate(server)
    entry.is_enabled_by_user = is_enabled
    return entry


@router.post("/{slug}/enable", status_code=status.HTTP_201_CREATED)
async def enable_catalog_entry(
    slug: str,
    user: UserORM = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    result = await session.execute(select(McpServerORM).where(McpServerORM.catalog_slug == slug))
    server = result.scalar_one_or_none()
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Catalog entry not found")

    # Check if already enabled
    existing = await session.execute(
        select(UserServerORM).where(UserServerORM.user_id == user.id, UserServerORM.server_id == server.id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Server already enabled")

    user_server = UserServerORM(user_id=user.id, server_id=server.id, is_enabled=True)
    session.add(user_server)
    await session.commit()

    return {
        "server_id": str(server.id),
        "required_env_vars": server.env_vars or {},
        "message": f"'{server.name}' enabled. Please set required API keys.",
    }
