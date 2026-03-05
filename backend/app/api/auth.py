from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.schemas import (
    RefreshRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserORM,
    UserResponse,
)
from app.services.auth_service import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class MCPTokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int | None = None  # None means non-expiring


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, session: AsyncSession = Depends(get_db)):
    existing = await session.execute(
        select(UserORM).where((UserORM.email == data.email) | (UserORM.username == data.username))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email or username already registered")

    count_result = await session.execute(select(func.count()).select_from(UserORM))
    user_count = count_result.scalar() or 0
    role = "admin" if user_count == 0 else "user"

    user = UserORM(
        email=data.email,
        username=data.username,
        hashed_password=hash_password(data.password),
        role=role,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(UserORM).where(UserORM.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

    return TokenResponse(
        access_token=create_access_token(str(user.id), user.role),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, session: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(data.refresh_token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    import uuid

    user_id = payload.get("sub")
    result = await session.execute(select(UserORM).where(UserORM.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return TokenResponse(
        access_token=create_access_token(str(user.id), user.role),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(user: UserORM = Depends(get_current_user)):
    return user


@router.post("/mcp-token", response_model=MCPTokenResponse)
async def generate_mcp_token(
    user: UserORM = Depends(get_current_user),
):
    """
    Generate a non-expiring MCP access token for use in mcp.json configuration.
    
    This token does not expire and can be used to authenticate MCP clients.
    You can regenerate tokens at any time from the UI if needed.
    """
    # Generate a non-expiring token
    token = create_access_token(str(user.id), user.role, no_expiry=True)
    
    return MCPTokenResponse(
        access_token=token,
        token_type="Bearer",
        expires_in=None  # Non-expiring
    )
