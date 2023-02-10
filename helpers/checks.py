import os
import json
from typing import Callable, TypeVar

import discord
from discord.ext import commands

from exceptions import *
from helpers import db

T = TypeVar("T")

def channel_set() -> Callable[[T], T]:
    async def predicate(ctx: commands.Context) -> bool:
        if ctx.guild:
            entry = await db.read_one_server_config(ctx.guild.id)
            if entry:
                channel = discord.utils.get(ctx.guild.text_channels, id=entry.channel_id)
                if channel and channel.id == ctx.channel.id:
                    return True
        await ctx.send("Bot has not been configured to listen to this channel. See '!draw_listen'")
        return False

    return commands.check(predicate)

def is_owner() -> Callable[[T], T]:
    async def predicate(ctx: commands.Context) -> bool:
        with open(f"{os.path.realpath(os.path.dirname(__file__))}/../config.json") as file:
            data = json.load(file)
        if ctx.author.id not in data["owners"]:
            raise UserNotOwner
        return True

    return commands.check(predicate)

def is_admin() -> Callable[[T], T]:
    async def predicate(ctx: commands.Context) -> bool:
        if not ctx.author.guild_permissions.administrator:
            raise UserNotAdmin
        return True

    return commands.check(predicate)
