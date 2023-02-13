from collections import namedtuple

import aiosqlite

from helpers.logger import logger
from helpers.db import DATABASE_PATH

"""
Response Types
"""

RespEntryHist = namedtuple('RespEntryHist', 'name won guild_id user_id created_at')

"""
Functions
"""

async def create_entry_hist(
        name: str,
        won: bool,
        guild_id: int,
        user_id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute(
                    "INSERT INTO entry_hist(name, won, guild_id, user_id) VALUES (?, ?, ?, ?)",
                    (name, won and 1 or 0, guild_id, user_id,))
            await db.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False

async def read_all_entry_hist() -> list[RespEntryHist] | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            rows = await db.execute("SELECT name, won, guild_id, user_id, created_at FROM entry_hist")
            async with rows as cursor:
                result = await cursor.fetchall()
                result_list = []
                for row in result:
                    result_list.append(RespEntryHist(row[0], bool(row[1]), row[2], row[3], row[4]))
                return result_list
        except Exception as e:
            logger.error(e)
            return None

async def read_all_entry_hist_for_guild(guild_id: int) -> list[RespEntryHist] | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            rows = await db.execute(
                    "SELECT name, won, guild_id, user_id, created_at FROM entry_hist WHERE guild_id=?",
                    (guild_id,))
            async with rows as cursor:
                result = await cursor.fetchall()
                result_list = []
                for row in result:
                    result_list.append(RespEntryHist(row[0], bool(row[1]), row[2], row[3], row[4]))
                return result_list
        except Exception as e:
            logger.error(e)
            return None

async def read_all_entry_hist_for_user_in_guild(guild_id: int, user_id: int) -> list[RespEntryHist] | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            rows = await db.execute(
                    "SELECT name, won, guild_id, user_id, created_at FROM entry_hist WHERE guild_id=? AND user_id=?",
                    (guild_id, user_id,))
            async with rows as cursor:
                result = await cursor.fetchall()
                result_list = []
                for row in result:
                    result_list.append(RespEntryHist(row[0], bool(row[1]), row[2], row[3], row[4]))
                return result_list
        except Exception as e:
            logger.error(e)
            return None

async def delete_all_entry_hist() -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute("PRAGMA foreign_keys = ON")
            await db.execute("DELETE FROM entry_hist")
            await db.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False

async def delete_all_entry_hist_for_user_in_guild(guild_id: int, user_id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute("PRAGMA foreign_keys = ON")
            await db.execute("DELETE FROM entry_hist WHERE guild_id=? AND user_id=?", (guild_id, user_id,))
            await db.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False


