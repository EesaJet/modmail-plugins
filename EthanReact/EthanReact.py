from discord.ext import commands

class Ethan(commands.Cog):
    """Reacts with a banana emoji if someone says banana."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if "ETHAN" in message.content.upper():
            await message.add_reaction("KNIGHT:1080268333976391780")

async def setup(bot):
    await bot.add_cog(Ethan(bot))
