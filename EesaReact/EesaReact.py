from discord.ext import commands
from datetime import datetime, timedelta
import math
import json
import random
import discord

class Eesa(commands.Cog):
    """Reacts with a banana emoji if someone says banana."""

    def __init__(self, bot):
        self.bot = bot
        self.timer_file = "timers.json"
        self.timers = self.load_timers()
        
    message_counter = {}

    @commands.Cog.listener()
    async def on_message(self, message):
        
        if "EESA" in message.content.upper():
            await message.add_reaction("✈️")
        elif "SHIT" in message.content.upper():
            await message.add_reaction("💩")
        elif "THAMES" in message.content.upper():
            await message.add_reaction("⛵")
        elif "PHOTO" in message.content.upper():
            await message.add_reaction("📸")
        elif "JAY" in message.content.upper():
            await message.add_reaction("OLDMAN:1080268375911059517")
        elif "ETHAN" in message.content.upper():
            await message.add_reaction("KNIGHT:1080268333976391780")
        elif "DAFFY" in message.content.upper():
            await message.add_reaction("👑")
        elif "SHANIE" in message.content.upper():
            await message.add_reaction("🌸")
        elif "MIKE" in message.content.upper():
            await message.add_reaction("CANTERBURY:1097286182527828109")
        elif "JONATHAN" in message.content.upper():
            await message.add_reaction("JONATHAN:1080274489465651283")

    @commands.command()
    async def say(self, ctx, *, message):
        await ctx.send(message)
        await ctx.message.delete()

    def load_timers(self):
        try:
            with open(self.timer_file, "r") as f:
                timers = json.load(f)
        except FileNotFoundError:
            return {}
        else:
            # Convert stored timestamps to datetime objects
            for user_id, timestamp in timers.items():
                timers[user_id] = datetime.fromisoformat(timestamp)
            return timers

    def save_timers(self):
        # Convert datetime objects to ISO formatted strings for JSON serialization
        timers = {str(user_id): timestamp.isoformat() for user_id, timestamp in self.timers.items()}
        with open(self.timer_file, "w") as f:
            json.dump(timers, f)

    @commands.command()
    async def start(self, ctx):
        """Starts a personal stopwatch for the user."""
        if str(ctx.author.id) in self.timers:
            await ctx.send("You already have a stopwatch running.")
            return

        self.timers[str(ctx.author.id)] = datetime.now()
        self.save_timers()
        await ctx.send("Stopwatch started.")

    @commands.command()
    async def stop(self, ctx):
        """Stops the user's personal stopwatch."""
        if str(ctx.author.id) not in self.timers:
            await ctx.send("You don't have a stopwatch running.")
            return

        elapsed_time = datetime.now() - self.timers[str(ctx.author.id)]
        elapsed_seconds = math.ceil(elapsed_time.total_seconds())
        hours, remainder = divmod(elapsed_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        del self.timers[str(ctx.author.id)]
        self.save_timers()
        elapsed_time_str = f"{hours} Hours {minutes} Minutes {seconds} Seconds"
        await ctx.send(f"Stopwatch stopped. Elapsed time: {elapsed_time_str}")

    @commands.command()
    async def time(self, ctx):
        """Displays the user's elapsed stopwatch time."""
        if str(ctx.author.id) not in self.timers:
            await ctx.send("You don't have a stopwatch running.")
            return

        elapsed_time = datetime.now() - self.timers[str(ctx.author.id)]
        elapsed_seconds = math.ceil(elapsed_time.total_seconds())
        hours, remainder = divmod(elapsed_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        elapsed_time_str = f"{hours} Hours {minutes} Minutes {seconds} Seconds"
        await ctx.send(f"Elapsed time: {elapsed_time_str}")


    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Gives a specified role to the new member."""
        role_id = 1002600411099828326 # Replace with the ID of the role you want to give to new members
        role = member.guild.get_role(role_id)
        if role is None:
            return
        else:
            await member.add_roles(role)

    @commands.command()
    async def giverole(self, ctx, role_name: str):
        """Gives everyone a specified role."""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role is None:
            await ctx.send(f"Role {role_name} does not exist.")
        else:
            for member in ctx.guild.members:
                await member.add_roles(role)
            await ctx.send(f"Role {role_name} has been given to everyone.")
      
async def setup(bot):
    await bot.add_cog(Eesa(bot))
