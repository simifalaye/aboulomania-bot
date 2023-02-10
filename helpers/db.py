import os
import datetime
from collections import namedtuple

import aiosqlite

from helpers.logger import logger

DATABASE_PATH = f"{os.path.realpath(os.path.dirname(__file__))}/../database/database.db"

async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        with open(f"{os.path.realpath(os.path.dirname(__file__))}/../database/schema.sql") as file:
            await db.executescript(file.read())
        await db.commit()

"""
server_configs
"""
ServerConfig = namedtuple('ServerConfig', 'server_id channel_id')

async def create_server_config(server_id: int, channel_id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute(
                    "INSERT INTO server_configs(server_id, channel_id) VALUES (?, ?)",
                    (server_id, channel_id,))
            await db.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False

async def read_all_server_configs() -> list[ServerConfig] | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            rows = await db.execute("SELECT server_id, channel_id FROM server_configs")
            async with rows as cursor:
                result = await cursor.fetchall()
                result_list = []
                for row in result:
                    result_list.append(ServerConfig(row[0], row[1]))
                return result_list
        except Exception as e:
            logger.error(e)
            return None

async def read_one_server_config(server_id: int) -> ServerConfig | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            rows = await db.execute(
                    "SELECT server_id, channel_id FROM server_configs WHERE server_id=?",
                    (server_id,))
            async with rows as cursor:
                row = await cursor.fetchone()
                if row:
                    return ServerConfig(row[0], row[1])
                return None
        except Exception as e:
            logger.error(e)
            return None

async def update_server_config(server_id: int, channel_id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute(
                    "UPDATE server_configs SET channel_id=? WHERE server_id=?",
                    (channel_id, server_id,))
            await db.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False

async def delete_all_server_configs() -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute("DELETE FROM server_configs")
            await db.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False

async def delete_one_server_config(server_id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute("DELETE FROM server_configs WHERE server_id=?", (server_id,))
            await db.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False

"""
draw_entries
"""
DrawEntry = namedtuple('DrawEntry', 'server_id user_id first_choice second_choice')

async def create_draw_entry(server_id: int, user_id: int,
                            first_choice: str, second_choice: str) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute(
                    "INSERT INTO draw_entries(server_id, user_id, first_choice, second_choice) VALUES (?, ?, ?, ?)",
                    (server_id, user_id, first_choice, second_choice,))
            await db.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False

async def read_all_draw_entries() -> list[DrawEntry] | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            rows = await db.execute("SELECT server_id, user_id, first_choice, second_choice FROM draw_entries")
            async with rows as cursor:
                result = await cursor.fetchall()
                result_list = []
                for row in result:
                    result_list.append(DrawEntry(row[0], row[1], row[2], row[3]))
                return result_list
        except Exception as e:
            logger.error(e)
            return None

async def read_all_draw_entries_for_server(server_id: int) -> list[DrawEntry] | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            rows = await db.execute("SELECT server_id, user_id, first_choice, second_choice FROM draw_entries WHERE server_id=?", (server_id,))
            async with rows as cursor:
                result = await cursor.fetchall()
                result_list = []
                for row in result:
                    result_list.append(DrawEntry(row[0], row[1], row[2], row[3]))
                return result_list
        except Exception as e:
            logger.error(e)
            return None

async def read_one_draw_entry(server_id: int, user_id: int) -> DrawEntry | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            rows = await db.execute(
                    "SELECT server_id, user_id, first_choice, second_choice FROM draw_entries WHERE server_id=? AND user_id=?",
                    (server_id, user_id,))
            async with rows as cursor:
                row = await cursor.fetchone()
                if row:
                    return DrawEntry(row[0], row[1], row[2], row[3])
                return None
        except Exception as e:
            logger.error(e)
            return None

async def update_draw_entry(server_id: int, user_id: int,
                            first_choice: str, second_choice: str) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute(
                    "UPDATE draw_entries SET user_id=?, first_choice=?, second_choice=? WHERE server_id=?",
                    (user_id, first_choice, second_choice, server_id,))
            await db.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False

async def delete_all_draw_entries() -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute("DELETE FROM draw_entries")
            await db.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False

async def delete_all_entries_for_server(server_id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute("DELETE FROM draw_entries WHERE server_id=?", (server_id,))
            await db.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False
"""
draw_stats
"""
DrawStats = namedtuple('DrawStats', 'server_id user_id num_wins last_win_date')

async def create_draw_stat(server_id: int, user_id: int, timezone: datetime.tzinfo) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            now = datetime.datetime.now(timezone)
            await db.execute(
                    "INSERT INTO draw_stats(server_id, user_id, num_wins, last_win_date) VALUES (?, ?, ?, ?)",
                    (server_id, user_id, 0, now,))
            await db.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False

async def read_all_draw_stats() -> list[DrawStats] | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            rows = await db.execute("SELECT server_id, user_id, num_wins, last_win_date FROM draw_stats")
            async with rows as cursor:
                result = await cursor.fetchall()
                result_list = []
                for row in result:
                    result_list.append(DrawStats(row[0], row[1], row[2], row[3]))
                return result_list
        except Exception as e:
            logger.error(e)
            return None

async def read_all_draw_stats_for_server(server_id: int) -> list[DrawStats] | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            rows = await db.execute("SELECT server_id, user_id, num_wins, last_win_date FROM draw_stats WHERE server_id=?", (server_id,))
            async with rows as cursor:
                result = await cursor.fetchall()
                result_list = []
                for row in result:
                    result_list.append(DrawStats(row[0], row[1], row[2], row[3]))
                return result_list
        except Exception as e:
            logger.error(e)
            return None

async def read_one_draw_stat(server_id: int, user_id: int) -> DrawStats | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            rows = await db.execute(
                    "SELECT server_id, user_id, first_choice, second_choice FROM draw_stats WHERE server_id=? AND user_id=?", (server_id, user_id,))
            async with rows as cursor:
                row = await cursor.fetchone()
                if row:
                    return DrawStats(row[0], row[1], row[2], row[3])
                return None
        except Exception as e:
            logger.error(e)
            return None

async def update_draw_stat_win(server_id: int, user_id: int, timezone: datetime.tzinfo) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            rows = await db.execute(
                    "SELECT num_wins FROM draw_stats WHERE server_id=? AND user_id=?", (server_id, user_id,))
            async with rows as cursor:
                row = await cursor.fetchone()
                if row:
                    now = datetime.datetime.now(timezone)
                    num_wins = row[0] + 1
                    await db.execute(
                        "UPDATE draw_stats SET num_wins=?, last_win_date=? WHERE server_id=? AND user_id=?",
                        (num_wins, now, server_id, user_id,))
                    await db.commit()
                    return True
                return False
        except Exception as e:
            logger.error(e)
            return False

async def delete_all_draw_stats() -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute("DELETE FROM draw_stats")
            await db.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False

async def delete_all_stats_for_server(server_id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute("DELETE FROM draw_stats WHERE server_id=?", (server_id,))
            await db.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False
