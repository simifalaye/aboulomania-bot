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

        async def draw():
            # Gather entries
            entries = await db.read_all_draw_entries_for_server(server_id)
            if not entries:
                await channel.send('No more entries. Please enter some first with "!draw_enter"')
                return

            response = ""
            # Add entries
            entries_str = await self.list_draw_entries(server_id)
            if entries_str:
                response += 'Selecting entries from list:\n' + entries_str + '\n'
            # Select winner
            entry = random.choice(entries)
            choice = random.choice([entry.first_choice, entry.first_choice, entry.second_choice])
            user = discord.utils.get(guild.members, id=int(entry.user_id))
            if user and choice:
                # Add winner text
                response += '**Winner is {}** entered by {}\n'.format(choice, user.mention)
                # Remove winner from entry list
                await db.delete_draw_entry(entry.server_id, entry.user_id)
                # Update stats
                stat = await db.read_draw_stat(server_id, entry.user_id)
                if not stat:
                    await db.create_draw_stat(server_id, entry.user_id, self.timezone)
                await db.update_draw_stat_win(server_id, entry.user_id, self.timezone)
                # Send output
                await channel.send(response)

        # Notify channel
        now = datetime.datetime.now(self.timezone)
        await channel.send('**Running the draw for {}**:'.format(now.strftime("%d/%m/%Y")))

        # Draw two winners
        await draw()
        await draw()

        # Delete all other entries, winners have been selected for this draw
        await db.delete_all_entries_for_server(server_id)

    async def list_draw_entries(self, server_id: int) -> str | None:
        """Get a list of draw entries for the server and the users that entered them

        Args:
            server_id: server to output to

        Returns:
            The entry list for the server, one for each line
        """
        # Get guild object
        guild = discord.utils.get(self.bot.guilds, id=server_id)
        if not guild:
            logger.error("Unable to find guild for guild id '{}'".format(server_id))
            return None
        # Read all entries
        entries = await db.read_all_draw_entries_for_server(server_id)
        if not entries:
            return 'No entries found. Please enter some first with "!draw_enter"'
        # Generate return string
        lines = []
        for entry in entries:
            user = discord.utils.get(guild.members, id=int(entry.user_id))
            if user:
                lines.append('{}\'s picks were: "**{}**" and "**{}**"'.format(
                    user.name, entry.first_choice, entry.second_choice))
        return '\n'.join(['    - {}'.format(line) for line in lines])

    async def auto_draw(self) -> None:
        """ Autodraw task that will run the draw every week at the configure day/time """
        await self.bot.wait_until_ready()
        logger.info("Starting auto draw task")
        while not self.bot.is_closed():
            now = datetime.datetime.now(self.timezone)
            # If it's 7pm on a Wednesday
            if now.weekday() == app_config["auto_draw_weekday"] and \
                    now.hour == app_config["auto_draw_hour"] and now.minute == 0:
                # Run draw on all servers
                server_configs = await db.read_all_server_configs()
                if server_configs:
                    logger.info("Running auto draw for all servers")
                    for server_config in server_configs:
                        await self.run_draw(server_config.server_id, server_config.channel_id)
            await asyncio.sleep(60)

    """
    Listeners
    """

    @commands.Cog.listener()
    async def on_ready(self):
        """ Cog builtin that runs when the cog is ready """
        self.task = self.bot.loop.create_task(self.auto_draw())

    """
    Commands
    """

    @commands.hybrid_command(
        name="draw_listen",
        description="Choose this channel as the listening channel for draw commands"
    )
    @checks.is_admin()
    async def draw_listen(self, ctx: Context) -> None:
        if not ctx.guild:
            await ctx.send('Something went wrong. Try again later')
            return

        server_id = ctx.guild.id
        channel_id = ctx.channel.id
        # Create or update server config
        config = await db.read_server_config(server_id)
        if config:
            if not await db.update_server_config(server_id, channel_id):
                await ctx.send('Unable to set this channel as listening channel. Try again later')
                return
        else:
            if not await db.create_server_config(server_id, channel_id):
                await ctx.send('Unable to set this channel as listening channel. Try again later')
                return

        await ctx.send('Successfully set this channel as listening channel')

    @commands.hybrid_command(
        name="draw_list",
        description="List the entries in the draw for the week"
    )
    @checks.channel_set()
    async def draw_list(self, ctx: Context) -> None:
        if not ctx.guild:
            await ctx.send('Something went wrong. Try again later')
            return

        server_id = ctx.guild.id
        response = await self.list_draw_entries(server_id)
        if response:
            await ctx.send('**Draw entries**:\n' + response)

    @commands.hybrid_command(
        name="draw_enter",
        description="Enter the draw (ex. !draw_enter <choice1> <choice2>)"
    )
    @checks.channel_set()
    async def draw_enter(self, ctx: Context, choice1: str, choice2: str) -> None:
        if not ctx.guild or not ctx.author:
            await ctx.send('Something went wrong. Try again later')
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
        response = '{} has entered their picks into the draw: "**{}**" and "**{}**"'.format(
                ctx.author.mention, choice1, choice2)
        await ctx.send(response)


    @commands.hybrid_command(
        name="draw_now",
        description="Immediately run the draw for the current entries and remove them afterwards"
    )
    @checks.is_admin()
    @checks.channel_set()
    async def draw_now(self, ctx: Context) -> None:
        if not ctx.guild or not ctx.channel:
            await ctx.send('Something went wrong. Try again later')
            return

        await self.run_draw(ctx.guild.id, ctx.channel.id)

    @commands.hybrid_command(
        name="draw_stats",
        description="Print the draw stats for the server"
    )
    @checks.channel_set()
    async def draw_stats(self, ctx: Context) -> None:
        if not ctx.guild:
            await ctx.send('Something went wrong. Try again later')
            return

        server_id = ctx.guild.id
        stats = await db.read_all_draw_stats_for_server(server_id)
        if not stats:
            await ctx.send('No stats found. Please run a draw first with "!draw_now"')
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
