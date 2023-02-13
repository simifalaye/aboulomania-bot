from collections import namedtuple

import aiosqlite

from helpers.logger import logger
from helpers.db import DATABASE_PATH

"""
Response Types
"""

RespGuild = namedtuple('RespGuild', 'id channel_id autodraw_weekday autodraw_hour')

"""
Functions
"""

async def guild_exists(id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            cursor = await db.cursor()
            await cursor.execute("SELECT 1 FROM guilds WHERE id=?", (id,))
            return await cursor.fetchone() is not None
        except Exception as e:
            logger.error(e)
            return False

async def create_one_guild(
        id: int,
        channel_id: int,
        autodraw_weekday: int,
        autodraw_hour: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute(
                    "INSERT INTO guilds(id, channel_id, autodraw_weekday, autodraw_hour) VALUES (?, ?, ?, ?)",
                    (id, channel_id, autodraw_weekday, autodraw_hour,))
            await db.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False

async def read_all_guilds() -> list[RespGuild] | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            rows = await db.execute("SELECT id, channel_id, autodraw_weekday, autodraw_hour FROM guilds")
            async with rows as cursor:
                result = await cursor.fetchall()
                result_list = []
                for row in result:
                    result_list.append(RespGuild(row[0], row[1], row[2], row[3]))
                return result_list
        except Exception as e:
            logger.error(e)
            return None

async def read_one_guild(id: int) -> RespGuild | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            rows = await db.execute(
                    "SELECT id, channel_id, autodraw_weekday, autodraw_hour FROM guilds WHERE id=?",
                    (id,))
            async with rows as cursor:
                row = await cursor.fetchone()
                if row:
                    return RespGuild(row[0], row[1], row[2], row[3])
                return None
        except Exception as e:
            logger.error(e)
            return None

async def update_one_guild(
        id: int,
        channel_id: int | None,
        autodraw_weekday: int | None,
        autodraw_hour: int | None) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            sql = "UPDATE guilds SET "
            updates = []
            params = []
            if channel_id is not None:
                updates.append("channel_id=?")
                params.append(channel_id)
            if autodraw_weekday is not None:
                updates.append("autodraw_weekday=?")
                params.append(autodraw_weekday)
            if autodraw_hour is not None:
                updates.append("autodraw_hour=?")
                params.append(autodraw_hour)
            sql +=', '.join(updates)
            sql += " WHERE id=?"
            params.append(id)
            print(sql, params, params)

            await db.execute(sql, tuple(params))
            await db.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False

async def delete_all_guilds() -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute("PRAGMA foreign_keys = ON")
            await db.execute("DELETE FROM guilds")
            await db.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False

async def delete_one_guild(id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute("PRAGMA foreign_keys = ON")
            await db.execute("DELETE FROM guilds WHERE id=?", (id,))
            await db.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False
