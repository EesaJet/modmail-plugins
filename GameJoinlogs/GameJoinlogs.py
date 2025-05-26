from discord.ext import commands, tasks
from datetime import datetime, timedelta
import pytz
import math
import json
import discord

class GameJoinlogs(commands.Cog):
    """Reacts with specific emojis and manages deadlines."""

    def __init__(self, bot):
        self.bot = bot
        self.channel_id = 466682606373830657

    @commands.Cog.listener()
    async def on_message(self, message):
    # Group shout + Shift-watcher
        location_map = {
            "cornwall":    ("Cornwall",                "https://www.roblox.com/games/4986113387/UPDATE-The-West-Cornwall-Project"),
            "palm beach":  ("Palm Beach Resort & Spa", "https://www.roblox.com/games/14918591976/Palm-Beach-Resort-Spa"),
            "northpark":   ("Northpark C Line",        "https://www.roblox.com/games/2337773502/Northpark-C-Line"),
        }
        if message.channel.id == 1157420902951166046 and message.author.id == 1157437939475828827:
            # map of location keywords → (display name, game link)
            original = message.embeds[0]
            
            for embed in message.embeds:
                title = embed.title or ""
                desc  = embed.description or ""
                combined = f"{title}\n{desc}".lower()

                
                # 2) “Shift on <location>” announcer
                if "joined" in combined:
                    for key, (place_name, game_link) in location_map.items():
                        if key in combined:
                            await message.channel.send(
                                f"📢 **Shift on {place_name}**\n\n"
                                f"{filtered_desc}\n\n"
                                f"**Game Link: 🔗** {game_link}\n"
                                "<@&1237844151525969930>"
                            )
                            await message.delete()        # ← delete the original embed message
                            return
                            
                await message.delete()        # ← delete the original embed message
                return
                
async def setup(bot):
    await bot.add_cog(GameJoinlogs(bot))
