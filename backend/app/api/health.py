from fastapi import APIRouter, Depends
from sqlalchemy import desc, distinct, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.schemas import HealthCheckORM, HealthCheckResponse, McpServerORM, UserORM, UserServerORM

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_probe():
    return {"status": "ok"}


@router.get("/api/health/servers", response_model=list[HealthCheckResponse])
async def server_health(
    user: UserORM = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    # Get user's enabled servers
    user_server_stmt = (
        select(UserServerORM.server_id)
        .where(UserServerORM.user_id == user.id, UserServerORM.is_enabled.is_(True))
    )
    user_result = await session.execute(user_server_stmt)
    server_ids = [row[0] for row in user_result.all()]

    if not server_ids:
        return []

    # Get the latest health check for each server
    results = []
    for sid in server_ids:
        stmt = (
            select(HealthCheckORM, McpServerORM.name)
            .join(McpServerORM, McpServerORM.id == HealthCheckORM.server_id)
            .where(HealthCheckORM.server_id == sid)
            .order_by(desc(HealthCheckORM.checked_at))
            .limit(1)
        )
        result = await session.execute(stmt)
        row = result.first()
        if row:
            check, server_name = row
            results.append(
                HealthCheckResponse(
                    server_id=check.server_id,
                    server_name=server_name,
                    status=check.status,
                    response_time_ms=check.response_time_ms,
                    error_message=check.error_message,
                    checked_at=check.checked_at,
                )
            )
        else:
            # No health check yet -- return unknown
            server_result = await session.execute(select(McpServerORM.name).where(McpServerORM.id == sid))
            name = server_result.scalar() or "Unknown"
            from datetime import datetime, timezone
            results.append(
                HealthCheckResponse(
                    server_id=sid,
                    server_name=name,
                    status="unknown",
                    response_time_ms=None,
                    error_message=None,
                    checked_at=datetime.now(timezone.utc),
                )
            )

    return results
