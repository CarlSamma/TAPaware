"""Database initialization utility script.

Run this script to create the SQLite database and all tables.
Usage: python scripts/setup_db.py
"""

import asyncio
import os
import sys

# Add src to path so we can import tap
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from tap.config import get_settings
from tap.db import Database


async def main() -> None:
    """Initialize the database with all tables."""
    settings = get_settings()
    print(f"Initializing database at: {settings.db_path}")

    db = Database(settings.db_path)
    await db.initialize()

    stats = await db.get_stats()
    print(f"Database initialized successfully!")
    print(f"  Tables created: tweets, nodes, properties, metaphor_layers, aliases, other_user_intel")
    print(f"  Current stats: {stats}")

    await db.close()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())