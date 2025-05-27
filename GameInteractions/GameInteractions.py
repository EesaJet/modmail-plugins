from discord.ext import commands, tasks
from datetime import datetime, timedelta
import pytz, math, json, discord, re, asyncio
from discord.ui import View, Button

class GameInteractions(commands.Cog):
   def __init__(self, bot):
       self.bot = bot

   @commands.Cog.listener()
   async def on_interaction(self, interaction: discord.Interaction):
      #if interaction.type is not discord.InteractionType.component:
         #return

      cid = interaction.data.get("custom_id", "")
      print(cid)
      if not cid.startswith("expgb_") or not cid.endswith("_gameban"):
         return

      user_id_str = cid[len("expgb_"):-len("_gameban")]
      print(user_id_str)
      if not user_id_str.isdigit():
         return
      user_id = int(user_id_str)
      print(user_id)

      # 1) Ack immediately so the button doesn't spin forever
      await interaction.response.defer(ephemeral=True)

      # 2) Build a fake message context to invoke your prefix command
      #    We hijack the original message object for simplicity:
      fake = interaction.message
      fake.author = interaction.user
      # assuming your bot’s prefix is "?"
      fake.content = f"?gameban {user_id} perm Banned via button"

      # 3) Get a Context from that fake message...
      ctx = await self.bot.get_context(fake)
      print(ctx)

      # 4) Finally invoke the command machinery
      await self.bot.invoke(ctx)

      # 5) (Optional) send a private followup so the clicker knows it ran
      await interaction.followup.send(f"🔨 Issued `?gameban {user_id}`", ephemeral=True)
                
async def setup(bot):
    await bot.add_cog(GameInteractions(bot))
