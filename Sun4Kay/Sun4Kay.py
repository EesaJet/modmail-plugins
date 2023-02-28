from discord.ext import commands

class Kay(commands.Cog):
    """Reacts with a banana emoji if someone says banana."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if "KAY" in message.content.upper():
            await message.add_reaction("KAYA:813843744385269762")
            
    @commands.Cog.listener()
    async def on_message(self, message):
        if "APPLE" in message.content.upper():
            await message.add_reaction("APPLE")
            
    @commands.Cog.listener()
    async def on_message(self, message):
        if "IPHONE" in message.content.upper():
            await message.add_reaction("APPLE")


async def setup(bot):
    await bot.add_cog(Kay(bot))
