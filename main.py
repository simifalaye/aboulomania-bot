import asyncio
import os
import platform

import discord
from discord.ext import commands
from discord.ext.commands import Bot, Context

import exceptions
import database.controllers.guilds as guildsdb
from helpers import db
from helpers.logger import logger
from helpers.config import config as app_config

"""
Setup bot intents
https://discordpy.readthedocs.io/en/latest/intents.html
https://discordpy.readthedocs.io/en/latest/intents.html#privileged-intents
"""
# Use default
intents = discord.Intents.default()
# Add privileged intents (MUST be enable in discord dev portal)
intents.message_content = True
intents.members = True

"""
Setup bot client
"""
bot = Bot(command_prefix=commands.when_mentioned_or(
    app_config["prefix"]),
    intents=intents,
    help_command=None)

# Events
# ======

@bot.event
async def on_ready() -> None:
    logger.info(f"Logged in as {bot.user}")
    logger.info(f"discord.py API version: {discord.__version__}")
    logger.info(f"Python version: {platform.python_version()}")
    logger.info(
        f"Running on: {platform.system()} {platform.release()} ({os.name})")

@bot.event
async def on_guild_join(guild: discord.Guild) -> None:
    if not await guildsdb.guild_exists(guild.id):
        logger.info("Adding guild to db: {}:{}".format(guild.id, guild.name))
        await guildsdb.create_one_guild(guild.id, -1, -1, -1)

@bot.event
async def on_guild_remove(guild: discord.Guild) -> None:
    logger.info("Deleting guild from db: {}:{}".format(guild.id, guild.name))
    await guildsdb.delete_one_guild(guild.id)

@bot.event
async def on_message(message: discord.Message) -> None:
    if message.author == bot.user or message.author.bot:
        return
    await bot.process_commands(message)

@bot.event
async def on_command_completion(ctx: Context) -> None:
    if not ctx.command:
        return
    full_command_name = ctx.command.qualified_name
    split = full_command_name.split(" ")
    executed_command = str(split[0])
    if ctx.guild is not None:
        logger.info(
            f"Executed {executed_command} command in {ctx.guild.name} (ID: {ctx.guild.id}) by {ctx.author} (ID: {ctx.author.id})")
    else:
        logger.info(
            f"Executed {executed_command} command by {ctx.author} (ID: {ctx.author.id}) in DMs")

@bot.event
async def on_command_error(ctx: Context, error) -> None:
    if isinstance(error, exceptions.NotInChannel):
        """
        @checks.in_channel() check.
        """
        embed = discord.Embed(
            description="Bot has not been configured to listen to this channel. See '!draw_listen'",
            color=0xE02B2B
        )
        await ctx.send(embed=embed)
    elif isinstance(error, exceptions.NotInGuild):
        """
        @checks.in_guild() check.
        """
        embed = discord.Embed(
            description="This command is only available in a server channel!",
            color=0xE02B2B
        )
        await ctx.send(embed=embed)
    elif isinstance(error, exceptions.UserNotOwner):
        """
        @checks.is_owner() check.
        """
        embed = discord.Embed(
            description="You are not the owner of the bot!",
            color=0xE02B2B
        )
        await ctx.send(embed=embed)
        guild_name = ctx.guild and ctx.guild.name or ""
        guild_id = ctx.guild and ctx.guild.id or ""
        logger.warning(
            f"{ctx.author} (ID: A non-owner user {ctx.author.id}) tried to execute an owner only command in the guild {guild_name} (ID: {guild_id}).")
    elif isinstance(error, exceptions.UserNotAdmin):
        """
        @checks.is_admin() check.
        """
        embed = discord.Embed(
            description="You are not an admin!",
            color=0xE02B2B
        )
        await ctx.send(embed=embed)
        guild_name = ctx.guild and ctx.guild.name or ""
        guild_id = ctx.guild and ctx.guild.id or ""
        logger.warning(
                f"{ctx.author} (ID: A non-admin user {ctx.author.id}) tried to execute an admin only command in the guild {guild_name} (ID: {guild_id}).")
    elif isinstance(error, commands.CommandOnCooldown):
        minutes, seconds = divmod(error.retry_after, 60)
        hours, minutes = divmod(minutes, 60)
        hours = hours % 24
        embed = discord.Embed(
            description=f"**Please slow down** - You can use this command again in {f'{round(hours)} hours' if round(hours) > 0 else ''} {f'{round(minutes)} minutes' if round(minutes) > 0 else ''} {f'{round(seconds)} seconds' if round(seconds) > 0 else ''}.",
            color=0xE02B2B
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            description="You are missing the permission(s) `" + ", ".join(
                error.missing_permissions) + "` to execute this command!",
            color=0xE02B2B
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.BotMissingPermissions):
        embed = discord.Embed(
            description="I am missing the permission(s) `" + ", ".join(
                error.missing_permissions) + "` to fully perform this command!",
            color=0xE02B2B
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            title="Error!",
            # We need to capitalize because the command arguments have no capital letter in the code.
            description=str(error).capitalize(),
            color=0xE02B2B
        )
        await ctx.send(embed=embed)
    else:
        raise error

# Functions
# =========

async def load_cogs() -> None:
    for file in os.listdir(f"{os.path.realpath(os.path.dirname(__file__))}/cogs"):
        if file.endswith(".py"):
            extension = file[:-3]
            try:
                await bot.load_extension(f"cogs.{extension}")
                logger.info(f"Loaded extension '{extension}'")
            except Exception as e:
                exception = f"{type(e).__name__}: {e}"
                logger.error(
                    f"Failed to load extension {extension}\n{exception}")

# Main
# ====

asyncio.run(db.init_db())
asyncio.run(load_cogs())
bot.run(app_config["token"])
