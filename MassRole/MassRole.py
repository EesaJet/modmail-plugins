from discord.ext import commands

class Ethan(commands.Cog):
    """Gives everyone a specified role on command."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def giverole(self, ctx, role_name: str):
        """Gives everyone a specified role."""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role is None:
            await ctx.send(f"Role {role_name} does not exist.")
        else:
            for member in ctx.guild.members:
                await member.add_roles(role)
            await ctx.send(f"Role {role_name} has been given to everyone.")

async def setup(bot):
    bot.add_cog(Ethan(bot))
