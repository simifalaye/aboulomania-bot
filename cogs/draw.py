import asyncio
import datetime
import random

import pytz
import discord
from discord.ext import commands
from discord.ext.commands import Context

from helpers import db, checks
from helpers.logger import logger
from helpers.config import config as app_config

class Draw(commands.Cog, name="draw"):
    def __init__(self, bot):
        self.bot = bot
        self.timezone = pytz.timezone(app_config["timezone"])
        # TODO: Make auto draw times configurable per server
        self.auto_draw_weekday = app_config["auto_draw_weekday"]
        self.auto_draw_hour = app_config["auto_draw_hour"]
        self.task = None

    """
    Helper Methods
    """

    def cog_unload(self) -> None:
        """ Cog builtin function that runs when cog is unload """
        if self.task:
            logger.info("Stopping auto draw task")
            self.task.cancel()

    async def run_draw(self, server_id: int, channel_id: int):
        """Run draw and output results to channel

        Args:
            server_id: server to output to
            channel_id: channel to output to
        """
        # Get guild and channel objects
        guild = discord.utils.get(self.bot.guilds, id=server_id)
        if not guild:
            logger.error("Unable to find guild for guild id '{}'".format(server_id))
            return
        channel = discord.utils.get(guild.text_channels, id=channel_id)
        if not channel:
            logger.error("Unable to find channel for channel id '{}'".format(channel_id))
            return

        async def draw() -> bool:
            # Gather entries
            entries = await db.read_all_draw_entries_for_server(server_id)
            if not entries:
                return False
            # First choice gets two entries
            selection_list = sorted(
                    [(x.user_id, x.first_choice) for x in entries] * 2 + \
                            [(x.user_id, x.second_choice) for x in entries])
            # Print list of entries being selected from
            list_str=""
            for i, item in enumerate(selection_list, start=1):
                user = discord.utils.get(guild.members, id=int(item[0]))
                if user:
                    list_str += f"{i}. {item[1]} ({user.name})\n"
            embed = discord.Embed(title="Selecting winner from list", description=list_str, color=0x00ff00)
            await channel.send(embed=embed)
            # Select winner
            winner = random.choice(selection_list)
            user = discord.utils.get(guild.members, id=int(winner[0]))
            if winner and user:
                # Remove winner from entry list
                await db.delete_draw_entry(server_id, winner[0])
                # Update stats
                stat = await db.read_draw_stat(server_id, winner[0])
                if not stat:
                    await db.create_draw_stat(server_id, winner[0], self.timezone)
                await db.update_draw_stat_win(server_id, winner[0], self.timezone)
                # Output winner
                await channel.send('**Winner is "{}"** entered by {}.'.format(winner[1], user.mention))
                return True
            return False

        # Notify channel
        now = datetime.datetime.now(self.timezone)
        await channel.send('**Running the draw for {}**:'.format(now.strftime("%d/%m/%Y")))

        # Draw two winners
        if not await draw():
            await channel.send('No entries to draw from. Please enter some first with "!draw_enter".')
            return
        if not await draw():
            await channel.send('No more entries left for second draw.')

        # Delete all other entries, winners have been selected for this draw
        await db.delete_all_entries_for_server(server_id)

    """
    Listeners
    """

    @commands.Cog.listener()
    async def on_ready(self):
        """ Cog builtin that runs when the cog is ready """
        async def scheduled_task():
            await self.bot.wait_until_ready()
            while not self.bot.is_closed():
                # Sleep till next run
                now = datetime.datetime.now(self.timezone)
                task_time = now + datetime.timedelta((self.auto_draw_weekday - now.weekday()) % 7)
                task_time = task_time.replace(hour=self.auto_draw_hour, minute=3, second=0, microsecond=0)
                if task_time < datetime.datetime.now(self.timezone):
                    task_time += datetime.timedelta(weeks=1)
                logger.info(f'Autodraw scheduled for {task_time.strftime("%A, %d %B %Y %H:%M:%S")}')
                await asyncio.sleep((task_time - datetime.datetime.now()).total_seconds())

                # Run draw on all servers
                logger.info("Running autodraw")
                server_configs = await db.read_all_server_configs()
                if server_configs:
                    logger.info("Found servers, running draw on each")
                    for server_config in server_configs:
                        await self.run_draw(server_config.server_id, server_config.channel_id)

        self.task = self.bot.loop.create_task(scheduled_task())

    """
    Commands
    """

    @commands.hybrid_command(
        name="draw_listen",
        description="Choose this channel as the listening channel for draw commands."
    )
    @checks.is_admin()
    async def draw_listen(self, ctx: Context) -> None:
        if not ctx.guild:
            await ctx.send('Something went wrong. Try again later.')
            return

        server_id = ctx.guild.id
        channel_id = ctx.channel.id
        # Create or update server config
        config = await db.read_server_config(server_id)
        if config:
            if not await db.update_server_config(server_id, channel_id):
                await ctx.send('Unable to set this channel as listening channel. Try again later.')
                return
        else:
            if not await db.create_server_config(server_id, channel_id):
                await ctx.send('Unable to set this channel as listening channel. Try again later.')
                return

        await ctx.send('Successfully set this channel as listening channel.')

    @commands.hybrid_command(
        name="draw_list",
        description="List the entries in the draw for the week."
    )
    @checks.channel_set()
    async def draw_list(self, ctx: Context) -> None:
        if not ctx.guild:
            await ctx.send('Something went wrong. Try again later.')
            return

        # Read all entries
        entries = await db.read_all_draw_entries_for_server(ctx.guild.id)
        if not entries:
            await ctx.send('No entries found. Please enter some first with "!draw_enter".')
            return
        # Print draw entries table
        embed = discord.Embed(title="Draw Entries", color=0x00ff00)
        for entry in entries:
            user = discord.utils.get(ctx.guild.members, id=int(entry.user_id))
            if user:
                name = user.name
                first_choice = entry.first_choice
                second_choice = entry.second_choice
                embed.add_field(name=name, value=f"Choice 1: {first_choice}\nChoice 2: {second_choice}", inline=True)
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="draw_enter",
        description="Enter the draw (ex. !draw_enter <choice1> <choice2>)."
    )
    @checks.channel_set()
    async def draw_enter(self, ctx: Context, choice1: str, choice2: str) -> None:
        if not ctx.guild or not ctx.author:
            await ctx.send('Something went wrong. Try again later.')
            return

        server_id = ctx.guild.id
        user_id = ctx.author.id
        # Create or update a draw entry (each user only gets one entry)
        entry = await db.read_draw_entry(server_id, user_id)
        if entry:
            await db.update_draw_entry(server_id, user_id, choice1, choice2)
        else:
            if not await db.create_draw_entry(server_id, user_id, choice1, choice2):
                await ctx.send('Unable to create the draw entry. Please try again.')

        # Success
        response = '{} has entered their picks into the draw: "**{}**" and "**{}**".'.format(
                ctx.author.mention, choice1, choice2)
        await ctx.send(response)


    @commands.hybrid_command(
        name="draw_now",
        description="Immediately run the draw for the current entries."
    )
    @checks.is_admin()
    @checks.channel_set()
    async def draw_now(self, ctx: Context) -> None:
        if not ctx.guild or not ctx.channel:
            await ctx.send('Something went wrong. Try again later.')
            return

        await self.run_draw(ctx.guild.id, ctx.channel.id)

    @commands.hybrid_command(
        name="draw_stats",
        description="Print the draw stats for each user."
    )
    @checks.channel_set()
    async def draw_stats(self, ctx: Context) -> None:
        if not ctx.guild:
            await ctx.send('Something went wrong. Try again later.')
            return

        server_id = ctx.guild.id
        stats = await db.read_all_draw_stats_for_server(server_id)
        if not stats:
            await ctx.send('No stats found. Please run a draw first with "!draw_now".')
            return

        # Generate draw stats table and output
        embed = discord.Embed(title="Historical Draw Stats", color=0x00ff00)
        for stat in stats:
            user = discord.utils.get(ctx.guild.members, id=int(stat.user_id))
            if user:
                name = user.name
                wins = stat.num_wins
                last_win = stat.last_win_date
                last_win = last_win.split(' ', 1)[0]
                embed.add_field(name=name, value=f"Wins: {wins}\nLast Win: {last_win}", inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Draw(bot))
