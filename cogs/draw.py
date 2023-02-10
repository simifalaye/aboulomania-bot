import asyncio
import datetime
import random

import pytz
import discord
from discord.ext import commands
from discord.ext.commands import Context
from tabulate import tabulate

from helpers import db, checks
from helpers.logger import logger
from helpers.config import config as app_config

time = datetime.time(hour=2, minute=43, tzinfo=pytz.timezone('Canada/Saskatchewan'))

class Draw(commands.Cog, name="draw"):
    def __init__(self, bot):
        self.bot = bot
        self.timezone = pytz.timezone(app_config["timezone"])
        self.channel = None
        self.task = None

    async def start_auto_draw(self) -> None:
        self.task = self.bot.loop.create_task(self.auto_draw())

    def cog_unload(self) -> None:
        if self.task:
            logger.info("Stopping auto draw task")
            self.task.cancel()

    async def run_draw(self, server_id: int, channel_id: str) -> None:
        async def update_winner(server_id, entry: db.DrawEntry):
            found = await db.read_one_draw_stat(server_id, entry.user_id)
            if not found:
                await db.create_draw_stat(server_id, entry.user_id, self.timezone)
            await db.update_draw_stat_win(server_id, entry.user_id, self.timezone)

        guild = discord.utils.get(self.bot.guilds, id=server_id)
        if not guild:
            logger.error("Unable to find guild for guild id '{}'".format(server_id))
            return
        channel = discord.utils.get(guild.text_channels, id=channel_id)
        if not channel:
            logger.error("Unable to find channel for channel id '{}'".format(channel_id))
            return

        # Notify channel
        now = datetime.datetime.now(self.timezone)
        await channel.send('Running the draw for ' + now.strftime("%d/%m/%Y") + ':')

        # Gather entries
        entries = await db.read_all_draw_entries_for_server(server_id)
        if not entries:
            await channel.send('No entries found. Please enter some first with "!draw_enter"')
            return

        found_winners = False
        response = '**The winners are**:\n'
        # Select first winner and remove their selections
        entry1 = random.choice(entries)
        choice1 = random.choice([entry1.first_choice, entry1.first_choice, entry1.second_choice])
        user1 = discord.utils.get(guild.members, id=int(entry1.user_id))
        if user1 and choice1:
            found_winners = True
            response += '    - "**{}**" entered by {}\n'.format(choice1, user1.mention)
            entries.remove(entry1)
            await update_winner(server_id, entry1)
        # Select second winner if there are more
        if entries:
            entry2 = random.choice(entries)
            choice2 = random.choice([entry2.first_choice, entry2.first_choice, entry2.second_choice])
            user2 = discord.utils.get(guild.members, id=int(entry2.user_id))
            if user2 and choice2:
                found_winners = True
                response += '    - "**{}**" entered by {}'.format(choice2, user2.mention)
            await update_winner(server_id, entry2)

        # Success
        await channel.send(response)
        if found_winners:
            await db.delete_all_entries_for_server(server_id)

    async def auto_draw(self) -> None:
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

    @commands.Cog.listener()
    async def on_ready(self):
        await self.start_auto_draw()

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
        config = await db.read_one_server_config(server_id)
        if config:
            if not await db.update_server_config(server_id, channel_id):
                await ctx.send('Unable to set this channel as listening channel. Try again later')
                return
        else:
            if not await db.create_server_config(server_id, channel_id):
                await ctx.send('Unable to set this channel as listening channel. Try again later')
                return

        self.channel = ctx.channel
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
        entries = await db.read_all_draw_entries_for_server(server_id)
        if not entries:
            await ctx.send('No entries found. Please enter some first with "!draw_enter"')
            return

        # Success
        lines = []
        for entry in entries:
            user = discord.utils.get(ctx.guild.members, id=int(entry.user_id))
            if user:
                lines.append('{}\'s picks were: "**{}**" and "**{}**"'.format(
                    user.name, entry.first_choice, entry.second_choice))
        response = '**The entries so far are**:\n' + '\n'.join(['    - {}'.format(line) for line in lines])
        await ctx.send(response)

    @commands.hybrid_command(
        name="draw_enter",
        description="Enter the draw"
    )
    @checks.channel_set()
    async def draw_enter(self, ctx: Context, choice1: str, choice2: str) -> None:
        if not ctx.guild or not ctx.author:
            await ctx.send('Something went wrong. Try again later')
            return

        server_id = ctx.guild.id
        user_id = ctx.author.id
        entry = await db.read_one_draw_entry(server_id, user_id)
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
        description="Print the stats for the server"
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

        # Success
        table = []
        headers = ["Users", "Number of wins", "Last win date"]
        for stat in stats:
            user = discord.utils.get(ctx.guild.members, id=int(stat.user_id))
            if user:
                table.append([user.name, stat.num_wins, stat.last_win_date])
        response = tabulate(table, headers, tablefmt="fancy_grid")
        await ctx.send("```\n" + response + "\n```")

async def setup(bot):
    await bot.add_cog(Draw(bot))
