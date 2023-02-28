from discord.ext import commands

class Shit(commands.Cog):
    """Reacts with a banana emoji if someone says banana."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if "SHIT" in message.content.upper():
            await message.add_reaction("\N{POOP}", "\N{SHIT}", "\N{HANKEY}", "\N{POO}")

async def setup(bot):
    await bot.add_cog(Shit(bot))
