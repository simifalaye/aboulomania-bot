import os
import platform
import subprocess
import datetime

import pytz
import discord
from discord.ext import commands
from discord.ext.commands import Context

from helpers import checks
from helpers.logger import logger, LOG_FILE_NAME
from helpers.config import config as app_config

MAX_LOG_LINES = 50

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

    @commands.hybrid_command(
        name="owner_show_logs",
        description="Show the latest bot logs (!owner_show_logs <num_lines>).",
    )
    @checks.is_owner()
    async def owner_show_logs(self, ctx: Context, num_lines: int) -> None:
        if num_lines > MAX_LOG_LINES:
            await ctx.send('Can only show up to a maximum of {} lines.'.format(MAX_LOG_LINES))
            return

        current_directory = os.path.dirname(os.path.abspath(__file__))
        log_file = os.path.join(current_directory, "..", LOG_FILE_NAME)
        try:
            with open(log_file, 'r') as file:
                lines = file.readlines()
                last_lines = lines[-num_lines:]
                output = ""
                lines_per_chunk = 10
                for i, line in enumerate(last_lines, start=1):
                    # Send output in 5 line chucks (discord message content limitation)
                    output += f'{line.strip()}\n'
                    if i % lines_per_chunk == 0:
                        await ctx.send(f'```{output}```')
                        output = ""
                # Send the last lines if there are more
                if output:
                    await ctx.send(f'```{output}```')
        except FileNotFoundError as e:
            logger.error(e)
            await ctx.send("File not found!")
        except Exception as e:
            logger.error(e)
            await ctx.send("An error occurred while reading the file.")

async def setup(bot):
    await bot.add_cog(Owner(bot))
