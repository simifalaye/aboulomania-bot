import asyncio
import datetime
import random
import calendar
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
        self.autodraw_tasks = {}

    """
    Helper Methods
    """

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

        async def draw(l: list[entriesdb.RespEntry]) -> entriesdb.RespEntry | None:
            if not l:
                await channel.send("No more entries to draw from.")
                return None
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
                # RULE: If a user wins, their entries are removed from the draw_list
                # RULE: Each unique pick can only win once so remove other entries from the draw_list
                l[:] = [e for e in l if e.user_id != winner.user_id and e.name != winner.name]
                # Output winner
                await channel.send('**Winner is "{}"** entered by {}.'.format(winner.name, user.mention))
                return winner
            # Handle error
            await channel.send('Unable to draw a winner. Something went wrong')
            logger.error('Error drawing winner (winner, user): ({}, {})'.format(winner, user))
            return None

        # Notify channel
        await channel.send('**Running the draw and selecting two winners**:')
        # Read all entries
        entries = await entriesdb.read_all_entries_for_guild(guild.id)
        if not entries:
            await channel.send('No entries found. Please enter some first with "!draw_enter".')
            return
        # RULE: First choice gets two entries into the draw, second gets one
        draw_list = []
        for entry in entries:
            if entry.first:
                draw_list.extend([entry, entry])
            else:
                draw_list.append(entry)
        # Draw two winners and clean up
        winner1 = await draw(draw_list)
        winner2 = await draw(draw_list)
        if winner1 or winner2:
            # Add entries into the history table
            for entry in entries:
                did_win = False
                if entry == winner1 or entry == winner2:
                    did_win = True
                await entryhistdb.create_entry_hist(entry.name, did_win, entry.guild_id, entry.user_id)
            # Delete all entries for guild
            await entriesdb.delete_all_entries_for_guild(guild.id)

    async def autodraw(self, guild: guildsdb.RespGuild):
        """Run the autodraw on schedule

        Args:
            guild: the guild db tuple
        """
        try:
            # Wait till bot is ready
            await self.bot.wait_until_ready()
            # Run while bot is still up
            while not self.bot.is_closed():
                # Calculate when the next run should be based on the autodraw schedule
                now = datetime.datetime.now(self.timezone)
                task_time = now + datetime.timedelta((guild.autodraw_weekday - now.weekday()) % 7)
                task_time = task_time.replace(hour=guild.autodraw_hour, minute=0, second=0, microsecond=0)
                if task_time < datetime.datetime.now(self.timezone): # If day has already pass, move one week forward
                    task_time += datetime.timedelta(weeks=1)
                # Sleep till the next run time
                logger.info(f'Autodraw for guild ({guild.id}), scheduled for {task_time.strftime("%A, %d %B %Y %H:%M:%S")}')
                await asyncio.sleep((task_time - datetime.datetime.now(self.timezone)).total_seconds())
                # Check if bot is still in guild, if not remove it from db (guild must have not been removed from db)
                guildobj = discord.utils.get(self.bot.guilds, id=guild.id)
                if not guildobj:
                    logger.info("Deleting old, invalid guild: {}".format(guild.id))
                    await guildsdb.delete_one_guild(guild.id)
                    return
                # Run draw on guild if channel is set
                if guild.channel_id > 0:
                    logger.info("Running autodraw for guild: {}".format(guild.id))
                    await self.run_draw(guild.id, guild.channel_id)
                else:
                    logger.info("Can't run autodraw for guild: {}. Channel not set yet".format(guild.id))
        except Exception as e:
            logger.debug("Autodraw task exception: {}".format(e))
            return

    async def start_autodraw(self, guild: guildsdb.RespGuild):
        """Start autodraw task for guild making sure to stop previous task first

        Args:
            guild: guild to start
        """
        # Stop first
        await self.stop_autodraw(guild.id)
        # Check if guild is configured for autodraw
        if guild.channel_id > 0 and guild.autodraw_weekday > 0 and guild.autodraw_hour > 0:
            logger.info("Starting auto draw task for guild: {}".format(guild.id))
            self.autodraw_tasks[guild.id] = self.bot.loop.create_task(self.autodraw(guild))

    async def stop_autodraw(self, guild_id: int):
        """Stop autodraw task for guild

        Args:
            guild: guild to stop
        """
        if guild_id in self.autodraw_tasks and self.autodraw_tasks[guild_id] is not None:
            logger.info("Stopping auto draw task for guild: {}".format(guild_id))
            self.autodraw_tasks[guild_id].cancel()
            self.autodraw_tasks[guild_id] = None

    async def cog_unload(self) -> None:
        """ Cog builtin function that runs when cog is unload """
        if self.autodraw_tasks:
            for guild_id, task in self.autodraw_tasks.items():
                if task is not None:
                    await self.stop_autodraw(guild_id)

    """
    Listeners
    """

    @commands.Cog.listener()
    async def on_ready(self):
        """ Cog builtin that runs when the cog is ready """
        # Add separate task for each guild
        guilds = await guildsdb.read_all_guilds()
        if guilds:
            for guild in guilds:
                await self.start_autodraw(guild)

    """
    Commands
    """

    @commands.hybrid_command(
        name="draw_listen",
        description="(Admin) Choose this channel as the listening channel for draw commands."
    )
    @checks.is_admin()
    @checks.in_guild()
    async def draw_listen(self, ctx: Context) -> None:
        if not ctx.guild:
            await ctx.send('Something went wrong. Try again later.')
            return

        # Create or update guild
        if await guildsdb.guild_exists(ctx.guild.id):
            await guildsdb.update_one_guild(ctx.guild.id, ctx.channel.id, None, None)
        else:
            await guildsdb.create_one_guild(ctx.guild.id, ctx.channel.id, -1, -1)

        guild = await guildsdb.read_one_guild(ctx.guild.id)
        if guild:
            # Success
            await self.start_autodraw(guild)
            await ctx.send('Successfully set this channel as listening channel.')
        else:
            # Failed
            await ctx.send('Unable to set this channel as listening channel. Try again.')


    @commands.hybrid_command(
        name="draw_auto_enable",
        description="(Admin) Enable autodraw weekly run (ex. !draw_auto_enable <weekday(0-6)> <hour(0-23>)."
    )
    @checks.is_admin()
    @checks.in_guild()
    async def draw_auto_enable(self, ctx: Context, weekday: int, hour: int) -> None:
        if not ctx.guild:
            await ctx.send('Something went wrong. Try again later.')
            return
        if weekday < 0 or weekday > 6 or hour < 0 or hour > 23:
            await ctx.send('<weekday> must be 0-6 and <hour> must be 0-23')
            return

        # Create or update guild
        if await guildsdb.guild_exists(ctx.guild.id):
            await guildsdb.update_one_guild(ctx.guild.id, None, weekday, hour)
        else:
            await guildsdb.create_one_guild(ctx.guild.id, -1, weekday, hour)

        guild = await guildsdb.read_one_guild(ctx.guild.id)
        if guild:
            # Success
            await self.start_autodraw(guild)
            await ctx.send('Successfully enabled the autodraw to run every {} at {} ({} timezone)'.format(
                calendar.day_name[weekday], f"{hour%12 or 12} {'AM' if hour < 12 else 'PM'}", app_config["timezone"]))
        else:
            # Failed
            await ctx.send('Unable to set autodraw schedule. Try again.')

    @commands.hybrid_command(
        name="draw_auto_disable",
        description="(Admin) Disable autodraw"
    )
    @checks.is_admin()
    @checks.in_guild()
    async def draw_auto_disable(self, ctx: Context) -> None:
        if not ctx.guild:
            await ctx.send('Something went wrong. Try again later.')
            return

        # Create or update guild
        if await guildsdb.guild_exists(ctx.guild.id):
            await guildsdb.update_one_guild(ctx.guild.id, None, -1, -1)
        else:
            await guildsdb.create_one_guild(ctx.guild.id, -1, -1, -1)

        guild = await guildsdb.read_one_guild(ctx.guild.id)
        if guild:
            # Success
            await self.stop_autodraw(guild.id)
            await ctx.send('Successfully disabled autodraw.')
        else:
            # Failed
            await ctx.send('Unable to disable autodraw. Try again.')

    @commands.hybrid_command(
        name="draw_list",
        description="List the entries in the draw for the week."
    )
    @checks.in_channel()
    @checks.in_guild()
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
    @checks.in_channel()
    @checks.in_guild()
    async def draw_enter(self, ctx: Context, choice1: str, choice2: str) -> None:
        if not ctx.guild or not ctx.author:
            await ctx.send('Something went wrong. Try again later.')
            return

        err_msg = "Unable to create the draw entry. Please try again."
        # Create user if not exists
        if not await usersdb.user_exists(ctx.author.id):
            if not await usersdb.create_one_user(ctx.author.id):
                await ctx.send(err_msg)
                return
        # Create enrollment if not exists
        if not await enrollmentsdb.enrollment_exists(ctx.guild.id, ctx.author.id):
            if not await enrollmentsdb.create_one_enrollment(ctx.guild.id, ctx.author.id):
                await ctx.send(err_msg)
                return
        # Remove old entries
        if not await entriesdb.delete_all_entries_for_user_in_guild(ctx.guild.id, ctx.author.id):
            await ctx.send(err_msg)
            return
        # Create new entries (set all entries to lowercase for matching entries later)
        if not await entriesdb.create_one_entry(choice1.lower(), True, ctx.guild.id, ctx.author.id) or \
                not await entriesdb.create_one_entry(choice2.lower(), False, ctx.guild.id, ctx.author.id):
            await ctx.send(err_msg)
            return

        # Success
        await ctx.send('{} has entered their picks into the draw: "**{}**" and "**{}**".'.format(
            ctx.author.mention, choice1, choice2))

    @commands.hybrid_command(
        name="draw_leave",
        description="Leave the draw (remove your entries)."
    )
    @checks.in_channel()
    @checks.in_guild()
    async def draw_leave(self, ctx: Context) -> None:
        if not ctx.guild or not ctx.author:
            await ctx.send('Something went wrong. Try again later.')
            return

        await entriesdb.delete_all_entries_for_user_in_guild(ctx.guild.id, ctx.author.id)
        await ctx.send('Removed your entries from the draw.')

    @commands.hybrid_command(
        name="draw_now",
        description="(Admin) Immediately run the draw for the current entries."
    )
    @checks.is_admin()
    @checks.in_channel()
    @checks.in_guild()
    async def draw_now(self, ctx: Context) -> None:
        if not ctx.guild or not ctx.channel:
            await ctx.send('Something went wrong. Try again later.')
            return

        await self.run_draw(ctx.guild.id, ctx.channel.id)

    @commands.hybrid_command(
        name="draw_user_stats",
        description="Print the draw stats for each user."
    )
    @checks.in_channel()
    @checks.in_guild()
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
                datetime_objects = [parser.parse(x.created_at) for x in entries if x.won]
                last_win_str = ""
                if datetime_objects:
                    last_win = max(datetime_objects)
                    last_win_str = last_win.strftime("%m/%d/%Y")
                # summary
                embed.add_field(
                        name=name,
                        value=f"Wins: {wins}\nFavorite: {most_common_entry} ({most_common_count})\nLast win date: {last_win_str}",
                        inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="draw_entry_stats",
        description="Print the draw stats for each entry."
    )
    @checks.in_channel()
    @checks.in_guild()
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
                    value=f"Wins: {wins}\nBiggest fan: {username} ({most_picked_by_count})\nLast pick date: {last_win_str}",
                    inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Draw(bot))
