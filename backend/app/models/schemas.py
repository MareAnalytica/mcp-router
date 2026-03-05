import uuid
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# SQLAlchemy ORM Models
# ---------------------------------------------------------------------------


class UserORM(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    user_servers: Mapped[list["UserServerORM"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    api_keys: Mapped[list["ServerApiKeyORM"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class McpServerORM(Base):
    __tablename__ = "mcp_servers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    transport_type: Mapped[str] = mapped_column(String(20), nullable=False)
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    command: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    args: Mapped[Optional[dict]] = mapped_column(JSONB, default=list)
    env_vars: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    headers: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    is_catalog: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    catalog_slug: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    icon_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    user_servers: Mapped[list["UserServerORM"]] = relationship(back_populates="server", cascade="all, delete-orphan")
    api_keys: Mapped[list["ServerApiKeyORM"]] = relationship(back_populates="server", cascade="all, delete-orphan")
    health_checks: Mapped[list["HealthCheckORM"]] = relationship(back_populates="server", cascade="all, delete-orphan")


class UserServerORM(Base):
    __tablename__ = "user_servers"
    __table_args__ = (UniqueConstraint("user_id", "server_id", name="uq_user_server"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    server_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("mcp_servers.id"), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    custom_config: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    user: Mapped["UserORM"] = relationship(back_populates="user_servers")
    server: Mapped["McpServerORM"] = relationship(back_populates="user_servers")


class ServerApiKeyORM(Base):
    __tablename__ = "server_api_keys"
    __table_args__ = (UniqueConstraint("user_id", "server_id", "key_name", name="uq_user_server_key"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    server_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("mcp_servers.id"), nullable=False)
    key_name: Mapped[str] = mapped_column(String(100), nullable=False)
    encrypted_value: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    user: Mapped["UserORM"] = relationship(back_populates="api_keys")
    server: Mapped["McpServerORM"] = relationship(back_populates="api_keys")


class HealthCheckORM(Base):
    __tablename__ = "health_checks"
    __table_args__ = (Index("ix_health_server_checked", "server_id", "checked_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    server_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("mcp_servers.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    response_time_ms: Mapped[Optional[int]] = mapped_column(nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    server: Mapped["McpServerORM"] = relationship(back_populates="health_checks")


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------


# -- Auth --

class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    username: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# -- MCP Servers --

class ServerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    transport_type: str = Field(pattern=r"^(sse|streamable_http|stdio)$")
    url: Optional[str] = None
    command: Optional[str] = None
    args: Optional[list[str]] = None
    env_vars: Optional[dict[str, str]] = None
    headers: Optional[dict[str, str]] = None


class ServerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    transport_type: Optional[str] = Field(None, pattern=r"^(sse|streamable_http|stdio)$")
    url: Optional[str] = None
    command: Optional[str] = None
    args: Optional[list[str]] = None
    env_vars: Optional[dict[str, str]] = None
    headers: Optional[dict[str, str]] = None


class ServerResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    transport_type: str
    url: Optional[str]
    command: Optional[str]
    args: Optional[list[str]]
    env_vars: Optional[dict[str, str]]
    headers: Optional[dict[str, str]]
    is_catalog: bool
    catalog_slug: Optional[str]
    icon_url: Optional[str]
    category: Optional[str]
    is_enabled: Optional[bool] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# -- API Keys --

class ApiKeySet(BaseModel):
    keys: list[dict[str, str]]  # [{"key_name": "...", "value": "..."}]


class ApiKeyResponse(BaseModel):
    key_name: str
    created_at: datetime

    model_config = {"from_attributes": True}


# -- Health --

class HealthCheckResponse(BaseModel):
    server_id: uuid.UUID
    server_name: str
    status: str
    response_time_ms: Optional[int]
    error_message: Optional[str]
    checked_at: datetime

    model_config = {"from_attributes": True}


# -- Catalog --

class CatalogEntryResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    transport_type: str
    catalog_slug: Optional[str]
    icon_url: Optional[str]
    category: Optional[str]
    env_vars: Optional[dict[str, str]]
    is_enabled_by_user: bool = False

    model_config = {"from_attributes": True}
