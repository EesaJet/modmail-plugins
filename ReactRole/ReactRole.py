from discord.ext import commands

class ReactionRole(commands.Cog):
    """Assigns a role to a user if they react with a specific emoji to a specified message."""

    def __init__(self, bot):
        self.bot = bot
        self.message_id = 1234567890 # Enter the ID of the message to add reaction to
        self.reaction_emoji = "🍌" # Enter the emoji to react with
        self.role_id = 9876543210 # Enter the ID of the role to assign

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.message_id == self.message_id and str(payload.emoji) == self.reaction_emoji:
            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            role = guild.get_role(self.role_id)
            await member.add_roles(role)

async def setup(bot):
    await bot.add_cog(ReactionRole(bot))
