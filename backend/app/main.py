import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.catalog import router as catalog_router
from app.api.health import router as health_router
from app.api.keys import router as keys_router
from app.api.servers import router as servers_router
from app.api.users import router as users_router
from app.config import settings
from app.mcp.connection_manager import connection_manager
from app.mcp.proxy import router as mcp_proxy_router
from app.models.database import async_session_factory, engine
from app.services.catalog_service import seed_catalog
from app.services.health_service import start_health_scheduler, stop_health_scheduler

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting MCP Router...")

    # Run Alembic migrations (in production, run separately; here we seed catalog)
    async with async_session_factory() as session:
        await seed_catalog(session)

    # Start background tasks
    connection_manager.start()
    start_health_scheduler()

    logger.info("MCP Router started successfully")
    yield

    # Shutdown
    logger.info("Shutting down MCP Router...")
    stop_health_scheduler()
    await connection_manager.stop()
    await engine.dispose()
    logger.info("MCP Router shut down")


app = FastAPI(
    title="MCP Router",
    description="A centralized MCP gateway that aggregates multiple MCP servers.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(servers_router)
app.include_router(keys_router)
app.include_router(catalog_router)
app.include_router(health_router)
app.include_router(mcp_proxy_router)
