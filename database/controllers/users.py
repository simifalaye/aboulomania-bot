from collections import namedtuple

import aiosqlite

from helpers.logger import logger
from helpers.db import DATABASE_PATH

"""
Response Types
"""

RespUser = namedtuple('RespUser', 'id')

"""
Functions
"""

async def user_exists(id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            cursor = await db.cursor()
            await cursor.execute("SELECT 1 FROM users WHERE id=?", (id,))
            return await cursor.fetchone() is not None
        except Exception as e:
            logger.error(e)
            return False

async def create_one_user(id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute("INSERT INTO users(id) VALUES (?)", (id,))
            await db.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False

async def read_all_users() -> list[RespUser] | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            rows = await db.execute("SELECT id FROM users")
            async with rows as cursor:
                result = await cursor.fetchall()
                result_list = []
                for row in result:
                    result_list.append(RespUser(row[0]))
                return result_list
        except Exception as e:
            logger.error(e)
            return None

async def read_one_user(id: int) -> RespUser | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            rows = await db.execute("SELECT id FROM users WHERE id=?", (id,))
            async with rows as cursor:
                row = await cursor.fetchone()
                if row:
                    return RespUser(row[0])
                return None
        except Exception as e:
            logger.error(e)
            return None

async def delete_all_users() -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute("PRAGMA foreign_keys = ON")
            await db.execute("DELETE FROM users")
            await db.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False

async def delete_one_user(id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute("PRAGMA foreign_keys = ON")
            await db.execute("DELETE FROM users WHERE id=?", (id,))
            await db.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False
