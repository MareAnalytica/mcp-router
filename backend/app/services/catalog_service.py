import json
import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import McpServerORM

logger = logging.getLogger(__name__)

CATALOG_PATH = Path(__file__).parent.parent / "catalog" / "built_in.json"


async def seed_catalog(session: AsyncSession) -> None:
    if not CATALOG_PATH.exists():
        logger.warning("Catalog file not found at %s", CATALOG_PATH)
        return

    with open(CATALOG_PATH) as f:
        entries = json.load(f)

    for entry in entries:
        slug = entry["catalog_slug"]
        result = await session.execute(select(McpServerORM).where(McpServerORM.catalog_slug == slug))
        existing = result.scalar_one_or_none()

        if existing:
            existing.name = entry["name"]
            existing.description = entry.get("description")
            existing.transport_type = entry["transport_type"]
            existing.url = entry.get("url")
            existing.command = entry.get("command")
            existing.args = entry.get("args", [])
            existing.env_vars = entry.get("env_vars", {})
            existing.icon_url = entry.get("icon_url")
            existing.category = entry.get("category")
        else:
            server = McpServerORM(
                name=entry["name"],
                description=entry.get("description"),
                transport_type=entry["transport_type"],
                url=entry.get("url"),
                command=entry.get("command"),
                args=entry.get("args", []),
                env_vars=entry.get("env_vars", {}),
                headers=entry.get("headers", {}),
                is_catalog=True,
                catalog_slug=slug,
                icon_url=entry.get("icon_url"),
                category=entry.get("category"),
            )
            session.add(server)

    await session.commit()
    logger.info("Catalog seeded with %d entries", len(entries))
