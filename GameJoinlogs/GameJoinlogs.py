from discord.ext import commands, tasks
from datetime import datetime, timedelta
import pytz, math, json, discord, re
from discord.ui import View, Button


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
            for embed in message.embeds:
                title = embed.title or ""
                desc  = embed.description or ""
                combined = f"{title}\n{desc}".lower()
                    
                # 2) “Shift on <location>” announcer
                if "joined" in combined:
                    for key, (place_name, game_link) in location_map.items():
                        if key in combined:

                            new_embed = discord.Embed(
                                title = embed.title,
                                description = embed.description,
                            )
            
                            game_link = location_map[key][1]
            
                            user_id = None
                            for line in desc.splitlines():
                                if line.lower().startswith("user id"):
                                    # split on ":" then filter digits
                                    parts = line.split(": ", 1)
                                    user_id = "".join(filter(str.isdigit, parts[1]))
                                    break
                                print(user_id)
                            
                            view = View()
                            view.add_item(Button(label="View Game",    url=game_link))
                            if user_id:
                                profile_url = f"https://www.roblox.com/users/{user_id}/profile"
                                view.add_item(Button(label="View Profile", url=profile_url))
                            
                            await message.channel.send(embed=new_embed, view=view)
                            #await message.delete()        # ← delete the original embed message
                            return
                            
                return
                
async def setup(bot):
    await bot.add_cog(GameJoinlogs(bot))
