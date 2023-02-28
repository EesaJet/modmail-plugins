from discord.ext import commands

class Jay(commands.Cog):
    """Reacts with a banana emoji if someone says banana."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if "SIMPLE" in message.content.upper():
            await message.add_reaction("OLDMAN:1080264190062768289")

async def setup(bot):
    await bot.add_cog(Jay(bot))
