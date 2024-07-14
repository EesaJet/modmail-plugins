from discord.ext import commands, tasks
import pytz
import math
import json
import discord

class Eesa(commands.Cog):
    """Reacts with specific emojis and manages deadlines."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if "EESA" in message.content.upper():
            await message.add_reaction("✈️")
        elif "SHIT" in message.content.upper():
            await message.add_reaction("💩")
        elif "DAFFY" in message.content.upper():
            await message.add_reaction("👑")
        elif "SHANIE" in message.content.upper():
            await message.add_reaction("🌸")
        elif "MIKE" in message.content.upper():
            await message.add_reaction("CANTERBURY:1097286182527828109")
        elif "JONATHAN" in message.content.upper():
            await message.add_reaction("JONATHAN:1080274489465651283")

async def setup(bot):
    await bot.add_cog(Eesa(bot))
