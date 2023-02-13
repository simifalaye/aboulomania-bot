import asyncio
import datetime
import random
from collections import defaultdict, Counter
from dateutil import parser

import pytz
import discord
from discord.ext import commands
from discord.ext.commands import Context

import database.controllers.guilds as guildsdb
import database.controllers.entries as entriesdb
import database.controllers.entry_hist as entryhistdb
import database.controllers.users as usersdb
import database.controllers.enrollments as enrollmentsdb
from helpers import checks
from helpers.logger import logger
from helpers.config import config as app_config

class Draw(commands.Cog, name="draw"):
    def __init__(self, bot):
        self.bot = bot
        self.timezone = pytz.timezone(app_config["timezone"])
        # TODO: Make auto draw times configurable per guild
        self.autodraw_weekday = app_config["autodraw_weekday"]
        self.autodraw_hour = app_config["autodraw_hour"]
        self.task = None

    """
    Helper Methods
    """

    def cog_unload(self) -> None:
        """ Cog builtin function that runs when cog is unload """
        if self.task:
            logger.info("Stopping auto draw task")
            self.task.cancel()

    async def run_draw(self, guild_id: int, channel_id: int):
        """Run draw and output results to channel

        Args:
            guild_id: server to output to
            channel_id: channel to output to
        """
        # Get guild and channel objects
        guild = discord.utils.get(self.bot.guilds, id=guild_id)
        if not guild:
            logger.error("Unable to find guild for guild id '{}'".format(guild_id))
            return
        channel = discord.utils.get(guild.text_channels, id=channel_id)
        if not channel:
            logger.error("Unable to find channel for channel id '{}'".format(channel_id))
            return

        async def draw(entries: list[entriesdb.RespEntry]) -> bool:
            # Combine all entries into one list
            draw_list = []
            for entry in entries:
                if entry.first:
                    draw_list.extend([entry, entry])
                else:
                    draw_list.append(entry)
            # Print list of entries being selected from
            list_str=""
            for i, item in enumerate(draw_list, start=1):
                user = discord.utils.get(guild.members, id=int(item.user_id))
                if user:
                    list_str += f"{i}. {item.name} ({user.name})\n"
            embed = discord.Embed(title="Selecting winner from list", description=list_str, color=0x00ff00)
            await channel.send(embed=embed)
            # Select winner
            winner = random.choice(draw_list)
            user = discord.utils.get(guild.members, id=int(winner.user_id))
            if winner and user:
                # Remove winner from entry list
                entries.remove(winner)
                # Add entry to history table
                await entryhistdb.create_entry_hist(winner.name, True, winner.guild_id, winner.user_id)
                # Remove entry from entries table
                await entriesdb.delete_all_entries_for_user_in_guild(winner.guild_id, winner.user_id)
                # Output winner
                await channel.send('**Winner is "{}"** entered by {}.'.format(winner.name, user.mention))
                return True
            return False

        # Notify channel
        await channel.send('**Running the draw**:')
        # Read all entries
        entries = await entriesdb.read_all_entries_for_guild(guild.id)
        if not entries:
            await channel.send('No entries found. Please enter some first with "!draw_enter".')
            return
        # Draw two winners
        await draw(entries)
        if entries:
            await draw(entries)
        else:
            await channel.send('No more entries left for second draw.')

        # Delete all other entries, winners have been selected for this draw
        for entry in entries:
            # Add entry to history table
            await entryhistdb.create_entry_hist(entry.name, False, entry.guild_id, entry.user_id)
            # Remove entry from entries table
            await entriesdb.delete_all_entries_for_user_in_guild(entry.guild_id, entry.user_id)

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
                task_time = now + datetime.timedelta((self.autodraw_weekday - now.weekday()) % 7)
                task_time = task_time.replace(hour=self.autodraw_hour, minute=3, second=0, microsecond=0)
                if task_time < datetime.datetime.now(self.timezone):
                    task_time += datetime.timedelta(weeks=1)
                logger.info(f'Autodraw scheduled for {task_time.strftime("%A, %d %B %Y %H:%M:%S")}')
                await asyncio.sleep((task_time - datetime.datetime.now()).total_seconds())

                # Run draw on all guilds
                logger.info("Running autodraw")
                guilds = await guildsdb.read_all_guilds()
                if guilds:
                    logger.info("Found guilds, running draw on each")
                    for guild in guilds:
                        if guild.channel_id > 0:
                            await self.run_draw(guild.id, guild.channel_id)

        self.task = self.bot.loop.create_task(scheduled_task())

    """
    Commands
    """

    @commands.hybrid_command(
        name="draw_listen",
        description="(Admin) Choose this channel as the listening channel for draw commands."
    )
    @checks.is_admin()
    async def draw_listen(self, ctx: Context) -> None:
        if not ctx.guild:
            await ctx.send('Something went wrong. Try again later.')
            return

        # Create or update guild
        res = False
        if await guildsdb.guild_exists(ctx.guild.id):
            res = await guildsdb.update_one_guild(ctx.guild.id, ctx.channel.id, None, None)
        else:
            res = await guildsdb.create_one_guild(
                    ctx.guild.id, ctx.channel.id, app_config["autodraw_weekday"], app_config["autodraw_hour"])
        # Respond
        if res:
            await ctx.send('Successfully set this channel as listening channel.')
        else:
            await ctx.send('Unable to set this channel as listening channel. Try again.')

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
        entries = await entriesdb.read_all_entries_for_guild(ctx.guild.id)
        if not entries:
            await ctx.send('No entries found. Please enter some first with "!draw_enter".')
            return
        # Group entries by user
        user_entries = defaultdict(list)
        for entry in entries:
            user_entries[entry.user_id].append(entry)
        # Print draw entries table
        embed = discord.Embed(title="Draw Entries", color=0x00ff00)
        for user_id, entries in user_entries.items():
            user = discord.utils.get(ctx.guild.members, id=int(user_id))
            if user:
                name = user.name
                first_choice = next((x.name for x in entries if x.first), "")
                second_choice = next((x.name for x in entries if not x.first), "")
                embed.add_field(name=name, value=f"1: {first_choice}\n2: {second_choice}", inline=True)
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
        err_msg = "Unable to create the draw entry. Please try again."

        # Create or update user
        if not await usersdb.user_exists(ctx.author.id):
            if not await usersdb.create_one_user(ctx.author.id):
                await ctx.send(err_msg)
                return
        # Create enrollment
        if not await enrollmentsdb.enrollment_exists(ctx.guild.id, ctx.author.id):
            if not await enrollmentsdb.create_one_enrollment(ctx.guild.id, ctx.author.id):
                await ctx.send(err_msg)
                return
        # Remove old entries
        if not await entriesdb.delete_all_entries_for_user_in_guild(ctx.guild.id, ctx.author.id):
            await ctx.send(err_msg)
            return
        # Create new entries
        if not await entriesdb.create_one_entry(choice1.lower(), True, ctx.guild.id, ctx.author.id) or \
                not await entriesdb.create_one_entry(choice2.lower(), False, ctx.guild.id, ctx.author.id):
            await ctx.send(err_msg)
            return

        # Success
        await ctx.send('{} has entered their picks into the draw: "**{}**" and "**{}**".'.format(
            ctx.author.mention, choice1, choice2))


    @commands.hybrid_command(
        name="draw_now",
        description="(Admin) Immediately run the draw for the current entries."
    )
    @checks.is_admin()
    @checks.channel_set()
    async def draw_now(self, ctx: Context) -> None:
        if not ctx.guild or not ctx.channel:
            await ctx.send('Something went wrong. Try again later.')
            return

        await self.run_draw(ctx.guild.id, ctx.channel.id)

    @commands.hybrid_command(
        name="draw_user_stats",
        description="Print the draw stats for each user."
    )
    @checks.channel_set()
    async def draw_user_stats(self, ctx: Context) -> None:
        if not ctx.guild:
            await ctx.send('Something went wrong. Try again later.')
            return

        # Read all entries history
        entry_hist = await entryhistdb.read_all_entry_hist_for_guild(ctx.guild.id)
        if not entry_hist:
            await ctx.send('No user stats found. Please run a draw first with "!draw_now".')
            return
        # Group entries by user
        user_entry_hist = defaultdict(list)
        for entry in entry_hist:
            user_entry_hist[entry.user_id].append(entry)
        # Print stats
        embed = discord.Embed(title="Historical User Stats", color=0x00ff00)
        for user_id, entries in user_entry_hist.items():
            user = discord.utils.get(ctx.guild.members, id=int(user_id))
            if user:
                # name
                name = user.name
                # wins
                wins = len([e for e in entries if e.won])
                # most common picks
                counter = Counter([entry.name for entry in entries])
                most_common_entry, most_common_count = counter.most_common(1)[0]
                # last win date
                datetime_objects = [parser.parse(x.created_at) for x in entries]
                last_win = max(datetime_objects)
                last_win_str = last_win.strftime("%m/%d/%Y")
                # summary
                embed.add_field(
                        name=name,
                        value=f"Wins: {wins}\nFavorite: {most_common_entry} ({most_common_count})\nLast win: {last_win_str}",
                        inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="draw_entry_stats",
        description="Print the draw stats for each entry."
    )
    @checks.channel_set()
    async def draw_entry_stats(self, ctx: Context) -> None:
        if not ctx.guild:
            await ctx.send('Something went wrong. Try again later.')
            return

        # Read all entries history
        entry_hist = await entryhistdb.read_all_entry_hist_for_guild(ctx.guild.id)
        if not entry_hist:
            await ctx.send('No user stats found. Please run a draw first with "!draw_now".')
            return
        # Group entries by entry name
        entry_name_hist = defaultdict(list)
        for entry in entry_hist:
            entry_name_hist[entry.name].append(entry)
        # Print stats
        embed = discord.Embed(title="Historical Entry Stats", color=0x00ff00)
        for name, entries in entry_name_hist.items():
            # most picked by user
            counter = Counter([entry.user_id for entry in entries])
            most_picked_by, most_picked_by_count = counter.most_common(1)[0]
            username = ""
            user = discord.utils.get(ctx.guild.members, id=int(most_picked_by))
            if user:
                username = user.name
            # wins
            wins = len([e for e in entries if e.won])
            # last picked date
            datetime_objects = [parser.parse(x.created_at) for x in entries]
            last_win = max(datetime_objects)
            last_win_str = last_win.strftime("%m/%d/%Y")
            # summary
            embed.add_field(
                    name=name,
                    value=f"Wins: {wins}\nBiggest fan: {username} ({most_picked_by_count})\nLast win: {last_win_str}",
                    inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Draw(bot))
