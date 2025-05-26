from discord.ext import commands, tasks
from datetime import datetime, timedelta
import pytz, math, json, discord, re
from discord.ui import View, Button


class GameInteractions(commands.Cog):
    """Reacts with specific emojis and manages deadlines."""

    def __init__(self, bot):
        self.bot = bot
        self.channel_id = 466682606373830657

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        # 1) only care about component interactions (buttons / selects)
        if interaction.type is not discord.InteractionType.component:
            return

        custom_id = interaction.data.get("custom_id", "")
        # 2) must match exp_<digits>_gameban
        if not custom_id.startswith("exp_") or not custom_id.endswith("_gameban"):
            return

        # 3) extract the Roblox user ID in between
        user_id_str = custom_id[len("exp_"):-len("_gameban")]
        if not user_id_str.isdigit():
            return  # sanity

        user_id = int(user_id_str)

        # 4) acknowledge the click immediately
        await interaction.response.followup.send(f"Succesffuly banned", ephermal=True)

        # 5) call your ban‐cog’s command directly
        ban_cog = self.bot.get_cog("RobloxUserRestriction")
        if not ban_cog:
            return await interaction.followup.send(
                "❌ Ban subsystem is not loaded.", ephemeral=True
            )

        # Here we invoke your existing ban logic.
        # We're assuming you want a permanent ban, but you can adjust:
        try:
            # Note: we're passing the Interaction as 'ctx', since it has send methods
            await ban_cog.roblox_ban(
                interaction,               # this will act like a Context
                user_id,
                "perm",                    # duration
                reason="Banned via button" # or whatever default
            )
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to ban: {e}", ephemeral=True)
                
async def setup(bot):
    await bot.add_cog(GameInteractions(bot))
