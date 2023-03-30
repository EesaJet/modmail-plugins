from discord.ext import commands
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import math
import discord

class Eesa(commands.Cog):
    """Reacts with a banana emoji if someone says banana."""

    def __init__(self, bot):
        self.bot = bot
        self.mongo_uri = mongo_uri
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client["stopwatch_db"]
        self.col = self.db["stopwatch_col"]

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
        elif "MICHAEL" in message.content.upper():
            await message.add_reaction("🏅")
        elif "SHANIE" in message.content.upper():
            await message.add_reaction("🌸")

    @commands.command()
    async def say(self, ctx, *, message):
        await ctx.send(message)
        await ctx.message.delete()

    @commands.command()
    async def start(self, ctx):
        """Starts a personal stopwatch for the user."""
        user_id = ctx.author.id
        stopwatch_data = self.col.find_one({"user_id": user_id})
        if stopwatch_data:
            await ctx.send("You already have a stopwatch running.")
            return

        start_time = datetime.now(timezone.utc)
        stopwatch_data = {"user_id": user_id, "start_time": start_time}
        self.col.insert_one(stopwatch_data)
        await ctx.send("Stopwatch started.")

    @commands.command()
    async def stop(self, ctx):
        """Stops the user's personal stopwatch."""
        user_id = ctx.author.id
        stopwatch_data = self.col.find_one({"user_id": user_id})
        if not stopwatch_data:
            await ctx.send("You don't have a stopwatch running.")
            return

        start_time = stopwatch_data["start_time"]
        end_time = datetime.now(timezone.utc)
        elapsed_time = end_time - start_time
        elapsed_seconds = math.ceil(elapsed_time.total_seconds())
        hours, remainder = divmod(elapsed_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        elapsed_time_str = f"{hours} Hours {minutes} Minutes {seconds} Seconds"

        self.col.delete_one({"user_id": user_id})
        await ctx.send(f"Stopwatch stopped. Elapsed time: {elapsed_time_str}")

    @commands.command()
    async def time(self, ctx):
        """Displays the user's elapsed stopwatch time."""
        user_id = ctx.author.id
        stopwatch_data = self.col.find_one({"user_id": user_id})
        if not stopwatch_data:
            await ctx.send("You don't have a stopwatch running.")
            return

        start_time = stopwatch_data["start_time"]
        end_time = datetime.now(timezone.utc)
        elapsed_time = end_time - start_time
        elapsed_seconds = math.ceil(elapsed_time.total_seconds())
        hours, remainder = divmod(elapsed_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        elapsed_time_str = f"{hours} Hours {minutes} Minutes {seconds} Seconds"

        await ctx.send(f"Elapsed time: {elapsed_time_str}")

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
