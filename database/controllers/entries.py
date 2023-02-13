from collections import namedtuple

import aiosqlite

from helpers.logger import logger
from helpers.db import DATABASE_PATH

"""
Response Types
"""

RespEntry = namedtuple('RespEntry', 'name first guild_id user_id')

"""
Functions
"""

async def create_one_entry(
        name: str,
        first: bool,
        guild_id: int,
        user_id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute(
                    "INSERT INTO entries(name, first, guild_id, user_id) VALUES (?, ?, ?, ?)",
                    (name, first and 1 or 0, guild_id, user_id,))
            await db.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False

async def read_all_entries() -> list[RespEntry] | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            rows = await db.execute("SELECT name, first, guild_id, user_id FROM entries")
            async with rows as cursor:
                result = await cursor.fetchall()
                result_list = []
                for row in result:
                    result_list.append(RespEntry(row[0], bool(row[1]), row[2], row[3]))
                return result_list
        except Exception as e:
            logger.error(e)
            return None

async def read_all_entries_for_guild(guild_id: int) -> list[RespEntry] | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            rows = await db.execute(
                    "SELECT name, first, guild_id, user_id FROM entries WHERE guild_id=?",
                    (guild_id,))
            async with rows as cursor:
                result = await cursor.fetchall()
                result_list = []
                for row in result:
                    result_list.append(RespEntry(row[0], bool(row[1]), row[2], row[3]))
                return result_list
        except Exception as e:
            logger.error(e)
            return None

async def read_all_entries_for_user_in_guild(guild_id: int, user_id: int) -> list[RespEntry] | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            rows = await db.execute(
                    "SELECT name, first, guild_id, user_id FROM entries WHERE guild_id=? AND user_id=?",
                    (guild_id, user_id,))
            async with rows as cursor:
                result = await cursor.fetchall()
                result_list = []
                for row in result:
                    result_list.append(RespEntry(row[0], bool(row[1]), row[2], row[3]))
                return result_list
        except Exception as e:
            logger.error(e)
            return None

async def delete_all_entries() -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute("PRAGMA foreign_keys = ON")
            await db.execute("DELETE FROM entries")
            await db.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False

async def delete_all_entries_for_user_in_guild(guild_id: int, user_id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute("PRAGMA foreign_keys = ON")
            await db.execute("DELETE FROM entries WHERE guild_id=? AND user_id=?", (guild_id, user_id,))
            await db.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False

