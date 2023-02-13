import os
import platform
import subprocess
import datetime
import calendar

import pytz
import discord
from discord.ext import commands
from discord.ext.commands import Context

from helpers import checks
from helpers.config import config as app_config

class General(commands.Cog, name="general"):
    def __init__(self, bot):
        self.bot = bot
        self.timezone = pytz.timezone(app_config["timezone"])
        self.start_time = datetime.datetime.now(self.timezone)

    async def check_git_dirty_status(self) -> tuple[bool, str]:
        """Check whether the code running is the same as the remote code on github

        Returns:
            (True if clean, message)
        """
        # Get the current working directory
        current_working_directory = os.getcwd()
        # Get the source directory of the currently running script
        source_directory = os.path.dirname(os.path.abspath(__file__))
        # Change to the source directory
        os.chdir(source_directory)
        # Get the output of the Git command to check if the repository is clean
        git_status = subprocess.run(['git', 'status', '--porcelain'], stdout=subprocess.PIPE).stdout.decode().strip()
        # If the repository is not clean, stop
        if git_status:
            os.chdir(current_working_directory)
            return (False, 'The Git repository is not clean.')
        # Get the current branch of the repository
        current_branch = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], stdout=subprocess.PIPE).stdout.decode().strip()
        # Get the remote main branch of the repository
        remote_main_branch = subprocess.run(['git', 'ls-remote', '--heads', 'origin', current_branch], stdout=subprocess.PIPE).stdout.decode().strip().split()[0]
        # Get the SHA-1 hash of the current branch and the remote main branch
        current_commit = subprocess.run(['git', 'rev-parse', 'HEAD'], stdout=subprocess.PIPE).stdout.decode().strip()
        remote_main_commit = subprocess.run(['git', 'rev-parse', remote_main_branch], stdout=subprocess.PIPE).stdout.decode().strip()
        # Compare the SHA-1 hash of the current branch and the remote main branch
        if current_commit != remote_main_commit:
            os.chdir(current_working_directory)
            return (False, 'The local Git repository is not up-to-date with the remote main branch.')

        # Return to the previous working directory
        os.chdir(current_working_directory)
        return (True, 'The local Git repository is up-to-date with the remote main branch.')

    """
    Commands
    """

    @commands.hybrid_command(
        name="help",
        description="List all commands the bot has loaded."
    )
    async def help(self, ctx: Context) -> None:
        prefix = app_config["prefix"]
        embed = discord.Embed(
            title="AboulomaniaBot Help", description="List of available commands:", color=0x9C84EF)
        for i in self.bot.cogs:
            cog = self.bot.get_cog(i.lower())
            commands = cog.get_commands()
            data = []
            for command in commands:
                description = command.description.partition('\n')[0]
                data.append(f"{prefix}{command.name} - {description}")
            help_text = "\n".join(data)
            embed.add_field(name=i.capitalize(),
                            value=f'```{help_text}```', inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="info",
        description="(Admin) Get some information about the bot.",
    )
    @checks.is_admin()
    async def info(self, ctx: Context) -> None:
        # Uptime
        now = datetime.datetime.now(self.timezone)
        delta = now - self.start_time
        seconds = delta.days * 24 * 3600 + delta.seconds
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        # Git dirty status
        git_dirty_status = await self.check_git_dirty_status()
        git_dirty_status = git_dirty_status[1]
        # Autodraw day
        autodraw_hour = app_config["autodraw_hour"]
        autodraw = "Every {} at {}".format(
                calendar.day_name[app_config["autodraw_weekday"]],
                f"{autodraw_hour%12 or 12} {'AM' if autodraw_hour < 12 else 'PM'}")

        embed = discord.Embed(
            description="Bot info",
            color=0x9C84EF
        )
        embed.set_author(
            name="Bot Information"
        )
        embed.add_field(
            name="Uptime:",
            value = '{} days, {} hours, {} minutes, {} seconds'.format(
                days, hours, minutes, seconds),
            inline=True
        )
        embed.add_field(
            name="Python Version:",
            value=f"{platform.python_version()}",
            inline=True
        )
        embed.add_field(
            name="Discord API Version:",
            value=f"discord.py API version: {discord.__version__}",
            inline = True
        )
        embed.add_field(
            name="Git dirty status:",
            value=git_dirty_status,
            inline = True
        )
        embed.add_field(
            name="Bot timezone:",
            value=app_config["timezone"],
            inline = True
        )
        embed.add_field(
            name="Autodraw Schedule:",
            value=autodraw,
            inline = True
        )
        embed.set_footer(
            text=f"Requested by {ctx.author}"
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="invite",
        description="Get the invite link of the bot to be able to invite it.",
    )
    async def invite(self, ctx: Context) -> None:
        embed = discord.Embed(
            description=f"Invite me by clicking [here](https://discordapp.com/oauth2/authorize?&client_id={app_config['application_id']}&scope=bot+applications.commands&permissions={app_config['permissions']}).",
            color=0xD75BF4
        )
        try:
            await ctx.author.send(embed=embed)
            await ctx.send("I sent you a private message!")
        except discord.Forbidden:
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(General(bot))
