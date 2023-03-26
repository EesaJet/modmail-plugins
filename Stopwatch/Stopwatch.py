import discord
from discord.ext import commands
import time

class Stopwatch(commands.Cog):
    """Starts a stopwatch on a command and counts upwards until the same user stops it."""

    def __init__(self, bot):
        self.bot = bot
        self.timers = {}

    @commands.command()
    async def start(self, ctx):
        """Starts a personal stopwatch for the user who calls the command."""
        if ctx.author.id in self.timers:
            await ctx.send("You already have a stopwatch running!")
            return

        self.timers[ctx.author.id] = time.time()
        await ctx.send("Stopwatch started.")

    @commands.command()
    async def stop(self, ctx):
        """Stops the personal stopwatch for the user who calls the command and displays the final time in hours and minutes."""
        if ctx.author.id not in self.timers:
            await ctx.send("You don't have a stopwatch running!")
            return

        elapsed_time = time.time() - self.timers[ctx.author.id]
        del self.timers[ctx.author.id]

        # Convert elapsed time from seconds to hours and minutes
        hours, rem = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(rem, 60)

        await ctx.send(f"Stopwatch stopped. Time elapsed: {int(hours):02d}:{int(minutes):02d}:{seconds:.2f}")

async def setup(bot):
    bot.add_cog(Stopwatch(bot))
