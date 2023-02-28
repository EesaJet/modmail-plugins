from discord.ext import commands

class Kay(commands.Cog):
    """Reacts with a banana emoji if someone says banana."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if "KAY" in message.content.upper():
            await message.add_reaction("\N{KAY:890012337912811601}")




async def setup(bot):
    await bot.add_cog(Kay(bot))
