import datetime

from discord.ext import commands

class Stopwatch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.timers = {936757902369251339}

    @commands.command()
    async def start(self, ctx):
        """Starts a personal stopwatch for the user."""

        started = "Stopwatch started."
        message = await ctx.send(started)
        return message

def setup(bot):
    bot.add_cog(Stopwatch(bot))
