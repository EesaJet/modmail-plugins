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
            message = await ctx.send("You already have a stopwatch running.")
            return message

        self.timers[ctx.author.id] = datetime.datetime.now()
        message = await ctx.send("Stopwatch started.")
        return message

    @commands.command()
    async def stop(self, ctx):
        """Stops the user's personal stopwatch."""
        if ctx.author.id not in self.timers:
            message = await ctx.send("You don't have a stopwatch running.")
            return message

        elapsed_time = datetime.datetime.now() - self.timers[ctx.author.id]
        del self.timers[ctx.author.id]
        message = await ctx.send(f"Stopwatch stopped. Elapsed time: {elapsed_time}")
        return message

    @commands.command()
    async def time(self, ctx):
        """Displays the user's elapsed stopwatch time."""
        if ctx.author.id not in self.timers:
            message = await ctx.send("You don't have a stopwatch running.")
            return message

        elapsed_time = datetime.datetime.now() - self.timers[ctx.author.id]
        message = await ctx.send(f"Elapsed time: {elapsed_time}")
        return message

def setup(bot):
    bot.add_cog(Stopwatch(bot))
