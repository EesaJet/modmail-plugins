from discord.ext import commands

class Eesa(commands.Cog):
    """Reacts with a banana emoji if someone says banana."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if "EESA" in message.content.upper():
            await message.add_reaction("\N{AIRPLANE}")
        elif "SHIT" in message.content.upper():
            await message.add_reaction("SHIT:1080259762266050670")
        elif "THAMES" in message.content.upper():
            await message.add_reaction("\N{SAILBOAT}")
        elif "PHOTO" in message.content.upper():
            await message.add_reaction("\N{CAMERA}")
        elif "JAY" in message.content.upper():
            await message.add_reaction("OLDMAN:1080268375911059517")
        elif "ETHAN" in message.content.upper():
            await message.add_reaction("KNIGHT:1080268333976391780")
        elif "DAFFY" in message.content.upper():
            await message.add_reaction("\N{CROWN}")

    @commands.command()
    async def say(self, ctx, *, message):
        await ctx.send(message)
        await ctx.message.delete()


async def setup(bot):
    await bot.add_cog(Eesa(bot))
