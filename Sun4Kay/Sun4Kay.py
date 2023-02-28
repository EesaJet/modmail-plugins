from discord.ext import commands

class Banana(commands.Cog):
    """Reacts with a banana emoji if someone says banana."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if "Kay" in message.content.upper():
            await message.add_reaction("\N{KayA}")




async def setup(bot):
    await bot.add_cog(Banana(bot))
