from discord.ext import commands
from datetime import datetime, timedelta
import math

class Eesa(commands.Cog):
    """Reacts with a banana emoji if someone says banana."""

    def __init__(self, bot):
        self.bot = bot
        self.timers = {}

    @commands.Cog.listener()
    async def on_message(self, message):
        if "EESA" in message.content.upper():
            await message.add_reaction("\N{AIRPLANE}")
        elif "SHIT" in message.content.upper():
            await message.add_reaction("SHIT:1080259762266050670")
        elif "THAMES" in message.content.upper():
            await message.add_reaction("\N{SAILBOAT}")
        elif "PHOTO" in message.content.upper():
            await message.add_reaction("\N{CAMERA}")
        elif "JAY" in message.content.upper():
            await message.add_reaction("OLDMAN:1080268375911059517")
        elif "ETHAN" in message.content.upper():
            await message.add_reaction("KNIGHT:1080268333976391780")
        elif "DAFFY" in message.content.upper():
            await message.add_reaction("\N{CROWN}")
        elif "MICKEY" in message.content.upper():
            await message.add_reaction('\N{MILITARY_MEDAL}')

    @commands.command()
    async def say(self, ctx, *, message):
        await ctx.send(message)
        await ctx.message.delete()

    @commands.command()
    async def start(self, ctx):
        """Starts a personal stopwatch for the user."""
        if ctx.author.id in self.timers:
            await ctx.send("You already have a stopwatch running.")
            return

        self.timers[ctx.author.id] = datetime.now()
        await ctx.send("Stopwatch started.")

    @commands.command()
    async def stop(self, ctx):
        """Stops the user's personal stopwatch."""
        if ctx.author.id not in self.timers:
            await ctx.send("You don't have a stopwatch running.")
            return

        elapsed_time = datetime.now() - self.timers[ctx.author.id]
        elapsed_seconds = math.ceil(elapsed_time.total_seconds())
        hours, remainder = divmod(elapsed_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        del self.timers[ctx.author.id]
        elapsed_time_str = f"{hours} Hours {minutes} Minutes {seconds} Seconds"
        await ctx.send(f"Stopwatch stopped. Elapsed time: {elapsed_time_str}")

    @commands.command()
    async def time(self, ctx):
        """Displays the user's elapsed stopwatch time."""
        if ctx.author.id not in self.timers:
            await ctx.send("You don't have a stopwatch running.")
            return

        elapsed_time = datetime.now() - self.timers[ctx.author.id]
        elapsed_seconds = math.ceil(elapsed_time.total_seconds())
        hours, remainder = divmod(elapsed_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        elapsed_time_str = f"{hours} Hours {minutes} Minutes {seconds} Seconds"
        await ctx.send(f"Elapsed time: {elapsed_time_str}")

      
async def setup(bot):
    await bot.add_cog(Eesa(bot))
