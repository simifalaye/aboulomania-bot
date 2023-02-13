from collections import namedtuple

import aiosqlite

from helpers.logger import logger
from helpers.db import DATABASE_PATH

"""
Response Types
"""

RespEnrollment = namedtuple('RespEnrollment', 'guild_id user_id')

"""
Functions
"""

async def enrollment_exists(guild_id: int, user_id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            cursor = await db.cursor()
            await cursor.execute("SELECT 1 FROM enrollments WHERE guild_id=? AND user_id=?", (guild_id, user_id))
            return await cursor.fetchone() is not None
        except Exception as e:
            logger.error(e)
            return False

async def create_one_enrollment(guild_id: int, user_id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute(
                    "INSERT INTO enrollments(guild_id, user_id) VALUES (?, ?)",
                    (guild_id, user_id,))
            await db.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False

async def read_all_enrollments() -> list[RespEnrollment] | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            rows = await db.execute("SELECT guild_id, user_id FROM enrollments")
            async with rows as cursor:
                result = await cursor.fetchall()
                result_list = []
                for row in result:
                    result_list.append(RespEnrollment(row[0], row[1]))
                return result_list
        except Exception as e:
            logger.error(e)
            return None

async def read_one_enrollment(guild_id: int, user_id: int) -> RespEnrollment | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            rows = await db.execute(
                    "SELECT guild_id, user_id FROM enrollments WHERE guild_id=? AND user_id=?",
                    (guild_id, user_id,))
            async with rows as cursor:
                row = await cursor.fetchone()
                if row:
                    return RespEnrollment(row[0], row[1])
                return None
        except Exception as e:
            logger.error(e)
            return None

async def delete_all_enrollments() -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute("PRAGMA foreign_keys = ON")
            await db.execute("DELETE FROM enrollments")
            await db.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False

async def delete_one_enrollment(guild_id: int, user_id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute("PRAGMA foreign_keys = ON")
            await db.execute("DELETE FROM enrollments WHERE guild_id=? AND user_id=?", (guild_id, user_id,))
            await db.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False

