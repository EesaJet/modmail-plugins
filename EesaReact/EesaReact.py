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
        exempt_words = ["SUNDAY"]

        if "EESA" in message.content.upper():
            await message.add_reaction("✈️")
        if "SHIT" in message.content.upper():
            await message.add_reaction("💩")
        if "DAFFY" in message.content.upper():
            await message.add_reaction("👑")
        if "SHANIE" in message.content.upper():
            await message.add_reaction("🌸")
        if "MIKE" in message.content.upper():
            await message.add_reaction("CANTERBURY:1097286182527828109")
        if "JONATHAN" in message.content.upper():
            await message.add_reaction("JONATHAN:1080274489465651283")
        if "KAY" in message.content.upper() and not message.author.bot:
            await message.add_reaction("🌸")
        if "SUN" in message.content.upper() and not message.author.bot and all(
                exemption not in message.content.upper() for exemption in exempt_words):
            await message.channel.send("Here comes the sun!")
            await message.channel.send("<a:KayA:813843744385269762>")
        if "MELLOW" in message.content.upper() and not message.author.bot:
            await message.channel.send("STOP IT MELLOW!")
            await message.channel.send(":black_cat:")
        if "BREAKDATE" in message.content.upper() and not message.author.bot:
            await message.channel.send("ROTOXIC HAVE DONE A BREAKDATE! :boom:")
            await message.channel.send("https://tenor.com/view/roblox-developer-crash-gif-24842627")
        if "STUDIO" in message.content.upper() and message.channel.id == 455189806180466701 and not message.author.bot:
            await message.channel.send("\"Fucking Studio 😡\" ~ Kay 2024")

async def setup(bot):
    await bot.add_cog(Eesa(bot))
