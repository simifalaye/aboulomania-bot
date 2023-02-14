from typing import Callable, TypeVar

import discord
from discord.ext import commands

import database.controllers.guilds as guildsdb
from exceptions import *
from helpers.config import config as app_config

T = TypeVar("T")

def channel_set() -> Callable[[T], T]:
    """Checks to see if request is comming from the configured listening channel

    Returns:
        True if it is the correct channel
    """
    async def predicate(ctx: commands.Context) -> bool:
        if ctx.guild:
            entry = await guildsdb.read_one_guild(ctx.guild.id)
            if entry:
                channel = discord.utils.get(ctx.guild.text_channels, id=entry.channel_id)
                if channel and channel.id == ctx.channel.id:
                    return True
        raise ChannelNotSet

    return commands.check(predicate)

def in_guild() -> Callable[[T], T]:
    """Checks to see if request is comming from a guild channel an not DMs

    Returns:
        True if it is coming from a guild channel
    """
    async def predicate(ctx: commands.Context) -> bool:
        if not ctx.guild:
            raise NotInGuild
        return True

    return commands.check(predicate)

def is_owner() -> Callable[[T], T]:
    """Checks to see if user is an owner

    Returns:
        True if user is an owner
    """
    async def predicate(ctx: commands.Context) -> bool:
        if ctx.author.id not in app_config["owners"]:
            raise UserNotOwner
        return True

    return commands.check(predicate)

def is_admin() -> Callable[[T], T]:
    """Checks to see if user is an administrator

    Returns:
        True if user is an administrator
    """
    async def predicate(ctx: commands.Context) -> bool:
        if not ctx.author.guild_permissions.administrator:
            raise UserNotAdmin
        return True

    return commands.check(predicate)
