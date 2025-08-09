"""Piccolo configuration file for CellophoneMail."""

from piccolo.conf.apps import AppRegistry
from piccolo.engine.postgres import PostgresEngine
from piccolo.engine.sqlite import SQLiteEngine
import os

# Determine database type from DATABASE_URL
database_url = os.environ.get("DATABASE_URL", "sqlite:///./test.db")

if database_url.startswith("postgresql"):
    # Parse PostgreSQL connection
    # postgresql://user:pass@host:port/db -> PostgresEngine config
    if "+asyncpg" in database_url:
        database_url = database_url.replace("+asyncpg", "")
    
    # Extract components
    import re
    match = re.match(r"postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)", database_url)
    if match:
        user, password, host, port, database = match.groups()
        DB = PostgresEngine(
            config={
                "database": database,
                "user": user,
                "password": password,
                "host": host,
                "port": int(port),
            }
        )
    else:
        # Fallback to SQLite for development
        DB = SQLiteEngine(path="./test.db")
else:
    # SQLite configuration
    if database_url.startswith("sqlite:///"):
        db_path = database_url.replace("sqlite:///", "")
    elif database_url.startswith("sqlite+aiosqlite:///"):
        db_path = database_url.replace("sqlite+aiosqlite:///", "")
    else:
        db_path = "./test.db"
    
    DB = SQLiteEngine(path=db_path)

# App registry for migrations
APP_REGISTRY = AppRegistry(
    apps=[
        "cellophanemail.models.piccolo_app",
    ]
)