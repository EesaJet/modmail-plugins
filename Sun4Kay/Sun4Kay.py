from discord.ext import commands

class Kay(commands.Cog):
    """Reacts with a banana emoji if someone says banana."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
      
        exempt_words = ["SUNDAY", "SUNBURY"]
      
        if "KAY" in message.content.upper() and not message.author.bot:
            await message.add_reaction("KAYA:813843744385269762")
        if "SUN" in message.content.upper() and not message.author.bot and all(exemption not in message.content.upper() for exemption in exempt_words):
            await message.channel.send("Here comes the sun!")
            await message.channel.send("<a:KayA:813843744385269762>")
        if "MELLOW" in message.content.upper() and not message.author.bot:
            await message.channel.send("STOP IT MELLOW!")
            await message.channel.send(":black_cat:")

async def setup(bot):
    await bot.add_cog(Kay(bot))
