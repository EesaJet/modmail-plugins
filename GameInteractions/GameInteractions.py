from discord.ext import commands, tasks
from datetime import datetime, timedelta
import pytz, math, json, discord, re, asyncio
from discord.ui import View, Button
from discord import ButtonStyle

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
      await interaction.response.send_message(
         f"<:ban_hammer:918264271090106379> Successfully game banned `{user_id}`", 
         ephemeral=True
      )
      
      old_rows = interaction.message.components  # list of ActionRow
      new_view = View()
      
      for row in old_rows:
         for comp in row.children:
            # if it’s our Ban button, disable it
            if getattr(comp, "custom_id", "") == cid:
               new_view.add_item(
                  Button(
                     style=ButtonStyle.danger,
                     label=comp.label,
                     emoji=comp.emoji,
                     custom_id=comp.custom_id,
                     disabled=True
                     )
               )
            elif comp.style == ButtonStyle.link:
               new_view.add_item(
                  Button(
                     style=ButtonStyle.link,
                     label=comp.label,
                     url=comp.url,
                     disabled=False
                  )
               )
               
      await interaction.followup.edit_message(
         message_id=interaction.message.id,
         view=new_view
      )
      
async def setup(bot):
    await bot.add_cog(GameInteractions(bot))
