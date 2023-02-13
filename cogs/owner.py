import os
import platform
import subprocess
import datetime

import pytz
import discord
from discord.ext import commands
from discord.ext.commands import Context

from helpers import checks
from helpers.config import config as app_config

class Owner(commands.Cog, name="owner"):
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
        name="owner_info",
        description="Get some additional information about the bot.",
    )
    @checks.is_owner()
    async def owner_info(self, ctx: Context) -> None:
        if not ctx.guild:
            await ctx.send('Something went wrong. Try again later.')
            return

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
        embed.set_footer(
            text=f"Requested by {ctx.author}"
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Owner(bot))
