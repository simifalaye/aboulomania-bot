import calendar

import pytz
import discord
from discord.ext import commands
from discord.ext.commands import Context

import database.controllers.guilds as guildsdb
from helpers import checks
from helpers.config import config as app_config

class General(commands.Cog, name="general"):
    def __init__(self, bot):
        self.bot = bot
        self.timezone = pytz.timezone(app_config["timezone"])

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
                data.append(f'**{prefix}{command.name}** - {description}')
            help_text = '\n'.join(data)
            embed.add_field(name=f'__{i.capitalize()}__',
                            value=f'{help_text}', inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="info",
        description="(Admin) Get some information about the bot.",
    )
    async def info(self, ctx: Context) -> None:
        if not ctx.guild:
            await ctx.send('Something went wrong. Try again later.')
            return

        # Autodraw day
        autodraw = "Not scheduled."
        guild = await guildsdb.read_one_guild(ctx.guild.id)
        if guild:
            autodraw_weekday = guild.autodraw_weekday
            autodraw_hour = guild.autodraw_hour
            if autodraw_weekday > 0 and autodraw_hour > 0:
                autodraw = "Every {} at {}".format(
                        calendar.day_name[autodraw_weekday],
                        f"{autodraw_hour%12 or 12} {'AM' if autodraw_hour < 12 else 'PM'}")

        embed = discord.Embed(
            description="Bot info",
            color=0x9C84EF
        )
        embed.set_author(
            name="Bot Information"
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
    @checks.is_admin()
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
