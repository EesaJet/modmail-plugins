import datetime

from discord.ext import commands

class Stopwatch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.timers = {}

    @commands.command()
    async def start(self, ctx):
        """Starts a personal stopwatch for the user."""
        if ctx.author.id in self.timers:
            arm = "You already have a stopwatch running."
            message = await ctx.send(arm)
            return message

        self.timers[ctx.author.id] = datetime.datetime.now()
        started = "Stopwatch started."
        message = await ctx.send(started)
        return message

def setup(bot):
    bot.add_cog(Stopwatch(bot))
