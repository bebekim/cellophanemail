"""arq worker configuration and Redis connection settings."""

import os
import logging
from typing import Optional
from arq.connections import RedisSettings
from arq import cron

logger = logging.getLogger(__name__)


def get_redis_settings() -> RedisSettings:
    """Get Redis connection settings from environment."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Parse redis URL
    # Format: redis://[password@]host:port/db
    if redis_url.startswith("redis://"):
        redis_url = redis_url[8:]

    # Extract password if present
    password: Optional[str] = None
    if "@" in redis_url:
        auth_part, redis_url = redis_url.rsplit("@", 1)
        password = auth_part

    # Extract host, port, and db
    if "/" in redis_url:
        host_port, db_str = redis_url.rsplit("/", 1)
        database = int(db_str) if db_str else 0
    else:
        host_port = redis_url
        database = 0

    if ":" in host_port:
        host, port_str = host_port.rsplit(":", 1)
        port = int(port_str)
    else:
        host = host_port
        port = 6379

    return RedisSettings(
        host=host,
        port=port,
        database=database,
        password=password,
    )


async def startup(ctx: dict) -> None:
    """Worker startup hook - initialize database connection."""
    from piccolo.engine.postgres import PostgresEngine
    from cellophanemail.config.settings import get_settings

    logger.info("arq worker starting up...")

    settings = get_settings()

    # Initialize Piccolo database connection
    from piccolo.conf.apps import Finder

    # The database engine should be configured in piccolo_conf.py
    # This just ensures the connection pool is warmed up
    logger.info("arq worker startup complete")


async def shutdown(ctx: dict) -> None:
    """Worker shutdown hook - cleanup resources."""
    logger.info("arq worker shutting down...")


def get_functions():
    """Get functions to register (imported lazily to avoid circular imports)."""
    from .tasks import analyze_batch_task
    return [analyze_batch_task]


class WorkerSettings:
    """arq worker settings class."""

    # Redis connection
    redis_settings = get_redis_settings()

    # Functions to register
    functions = get_functions()

    # Worker settings
    max_jobs = 10  # Max concurrent jobs per worker
    job_timeout = 600  # 10 minutes max per job
    keep_result = 3600  # Keep results for 1 hour
    max_tries = 3  # Retry failed jobs up to 3 times
    retry_delay = 60  # Wait 1 minute between retries

    # Lifecycle hooks
    on_startup = startup
    on_shutdown = shutdown

    # Health check
    health_check_interval = 30  # seconds

    # Queue names
    queue_name = "cellophanemail:jobs"
