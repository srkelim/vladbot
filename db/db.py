import os
import asyncpg
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
SCHEMA_PATH = Path(__file__).parent / "schema.sql"

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(DATABASE_URL)

        schema = SCHEMA_PATH.read_text(encoding="utf-8")

        async with self.pool.acquire() as conn:
            await conn.execute(schema)

        print("database is ok")