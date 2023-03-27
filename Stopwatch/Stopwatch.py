from discord.ext import commands
import datetime

class Stopwatch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def start(self, ctx, *, message):

        started = "Stopwatch started."
        await ctx.send(started)

def setup(bot):
    bot.add_cog(Stopwatch(bot))
