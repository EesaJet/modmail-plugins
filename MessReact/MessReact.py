from discord.ext import commands

class MessReact(commands.Cog):
    """Reacts with a banana emoji if someone says banana."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if "MICKEY" in message.content.upper():
            await message.add_reaction("🏅")
      
async def setup(bot):
    await bot.add_cog(MessReact(bot))
