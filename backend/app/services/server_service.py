import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import (
    McpServerORM,
    ServerApiKeyORM,
    ServerCreate,
    ServerUpdate,
    UserServerORM,
)
from app.services.vault import encrypt_value


async def create_server(
    session: AsyncSession,
    user_id: uuid.UUID,
    data: ServerCreate,
) -> McpServerORM:
    server = McpServerORM(
        name=data.name,
        description=data.description,
        transport_type=data.transport_type,
        url=data.url,
        command=data.command,
        args=data.args or [],
        env_vars=data.env_vars or {},
        headers=data.headers or {},
        is_catalog=False,
        created_by=user_id,
    )
    session.add(server)
    await session.flush()

    user_server = UserServerORM(user_id=user_id, server_id=server.id, is_enabled=True)
    session.add(user_server)
    await session.commit()
    await session.refresh(server)
    return server


async def get_user_servers(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> list[tuple[McpServerORM, bool]]:
    stmt = (
        select(McpServerORM, UserServerORM.is_enabled)
        .join(UserServerORM, UserServerORM.server_id == McpServerORM.id)
        .where(UserServerORM.user_id == user_id)
        .order_by(McpServerORM.name)
    )
    result = await session.execute(stmt)
    return [(row[0], row[1]) for row in result.all()]


async def get_server_by_id(
    session: AsyncSession,
    server_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Optional[tuple[McpServerORM, bool]]:
    stmt = (
        select(McpServerORM, UserServerORM.is_enabled)
        .join(UserServerORM, UserServerORM.server_id == McpServerORM.id)
        .where(UserServerORM.user_id == user_id, McpServerORM.id == server_id)
    )
    result = await session.execute(stmt)
    row = result.first()
    if row:
        return (row[0], row[1])
    return None


async def update_server(
    session: AsyncSession,
    server_id: uuid.UUID,
    data: ServerUpdate,
) -> Optional[McpServerORM]:
    result = await session.execute(select(McpServerORM).where(McpServerORM.id == server_id))
    server = result.scalar_one_or_none()
    if not server:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(server, key, value)

    await session.commit()
    await session.refresh(server)
    return server


async def delete_server(
    session: AsyncSession,
    server_id: uuid.UUID,
    user_id: uuid.UUID,
) -> bool:
    # Remove user_server link
    stmt = select(UserServerORM).where(
        UserServerORM.user_id == user_id,
        UserServerORM.server_id == server_id,
    )
    result = await session.execute(stmt)
    user_server = result.scalar_one_or_none()
    if not user_server:
        return False

    await session.delete(user_server)

    # Remove associated API keys for this user+server
    key_stmt = select(ServerApiKeyORM).where(
        ServerApiKeyORM.user_id == user_id,
        ServerApiKeyORM.server_id == server_id,
    )
    key_result = await session.execute(key_stmt)
    for key in key_result.scalars().all():
        await session.delete(key)

    # If no other users reference this non-catalog server, delete the server itself
    server_result = await session.execute(select(McpServerORM).where(McpServerORM.id == server_id))
    server = server_result.scalar_one_or_none()
    if server and not server.is_catalog:
        remaining = await session.execute(
            select(UserServerORM).where(UserServerORM.server_id == server_id)
        )
        if not remaining.scalars().first():
            await session.delete(server)

    await session.commit()
    return True


async def toggle_server(
    session: AsyncSession,
    server_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Optional[bool]:
    stmt = select(UserServerORM).where(
        UserServerORM.user_id == user_id,
        UserServerORM.server_id == server_id,
    )
    result = await session.execute(stmt)
    user_server = result.scalar_one_or_none()
    if not user_server:
        return None

    user_server.is_enabled = not user_server.is_enabled
    await session.commit()
    return user_server.is_enabled


async def set_api_keys(
    session: AsyncSession,
    server_id: uuid.UUID,
    user_id: uuid.UUID,
    keys: list[dict[str, str]],
) -> None:
    for key_data in keys:
        key_name = key_data["key_name"]
        value = key_data["value"]

        stmt = select(ServerApiKeyORM).where(
            ServerApiKeyORM.user_id == user_id,
            ServerApiKeyORM.server_id == server_id,
            ServerApiKeyORM.key_name == key_name,
        )
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.encrypted_value = encrypt_value(value)
        else:
            api_key = ServerApiKeyORM(
                user_id=user_id,
                server_id=server_id,
                key_name=key_name,
                encrypted_value=encrypt_value(value),
            )
            session.add(api_key)

    await session.commit()


async def get_api_key_names(
    session: AsyncSession,
    server_id: uuid.UUID,
    user_id: uuid.UUID,
) -> list[ServerApiKeyORM]:
    stmt = select(ServerApiKeyORM).where(
        ServerApiKeyORM.user_id == user_id,
        ServerApiKeyORM.server_id == server_id,
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def delete_api_key(
    session: AsyncSession,
    server_id: uuid.UUID,
    user_id: uuid.UUID,
    key_name: str,
) -> bool:
    stmt = select(ServerApiKeyORM).where(
        ServerApiKeyORM.user_id == user_id,
        ServerApiKeyORM.server_id == server_id,
        ServerApiKeyORM.key_name == key_name,
    )
    result = await session.execute(stmt)
    key = result.scalar_one_or_none()
    if not key:
        return False

    await session.delete(key)
    await session.commit()
    return True
