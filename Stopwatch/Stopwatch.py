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
            await ctx.send("You already have a stopwatch running.")
            return

        self.timers[ctx.author.id] = datetime.datetime.now()
        await ctx.send("Stopwatch started.")

    @commands.command()
    async def stop(self, ctx):
        """Stops the user's personal stopwatch."""
        if ctx.author.id not in self.timers:
            await ctx.send("You don't have a stopwatch running.")
            return

        elapsed_time = datetime.datetime.now() - self.timers[ctx.author.id]
        del self.timers[ctx.author.id]
        await ctx.send(f"Stopwatch stopped. Elapsed time: {elapsed_time}")

    @commands.command()
    async def time(self, ctx):
        """Displays the user's elapsed stopwatch time."""
        if ctx.author.id not in self.timers:
            await ctx.send("You don't have a stopwatch running.")
            return

        elapsed_time = datetime.datetime.now() - self.timers[ctx.author.id]
        await ctx.send(f"Elapsed time: {elapsed_time}")

def setup(bot):
    bot.add_cog(Stopwatch(bot))
