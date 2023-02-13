import os

import aiosqlite


DATABASE_PATH = f"{os.path.realpath(os.path.dirname(__file__))}/../database/database.db"

async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Load schema
        with open(f"{os.path.realpath(os.path.dirname(__file__))}/../database/schema.sql") as file:
            await db.executescript(file.read())
        await db.commit()
