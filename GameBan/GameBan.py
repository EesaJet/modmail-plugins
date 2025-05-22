import os
from dotenv import load_dotenv
load_dotenv()      # ← here

import logging, pytz, discord, aiohttp
from datetime import timedelta
from discord.ext import commands
from discord.ui import View, Button

class RobloxUserRestriction(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # your universe (game) ID
        self.universe_id = int(os.getenv("ROBLOX_UNIVERSE_ID"))
        self.second_universe_id = int(os.getenv("ROBLOX_SECOND_UNIVERSE_ID"))
        # the API key you generated in Creator Hub
        self.api_key = os.getenv("ROBLOX_API_KEY")
        if not self.api_key or not self.universe_id or not self.second_universe_id:
            raise RuntimeError("Set ROBLOX_API_KEY and ROBLOX_UNIVERSE_ID env vars")

        print(os.getenv("ROBLOX_API_KEY"))
        print(os.getenv("ROBLOX_UNIVERSE_ID"))
        print(os.getenv("ROBLOX_SECOND_UNIVERSE_ID"))
              
        self.base_url = f"https://apis.roblox.com/cloud/v2/universes/{self.universe_id}/user-restrictions"
        self.second_url = f"https://apis.roblox.com/cloud/v2/universes/{self.second_universe_id}/user-restrictions"
        self.headers = {
            "x-api-key":    self.api_key,
            "Content-Type": "application/json"
        }

    @commands.command(name="gameban")
    @commands.has_permissions(kick_members=True)
    async def roblox_ban(self, ctx, user_id: int, duration: str, *, reason: str):
        """
        Ban a Roblox user from joining your game.
        Usage: !gameban <user_id> <7d|24h|perm> <reason>
        """
        # parse duration
        permanent = duration.lower() == "perm"

        restriction = {
                "active":            True,
                "privateReason":     reason,
                "displayReason":     reason,
                "excludeAltAccounts": False
            }
        
        if not permanent:
            unit   = duration[-1].lower()
            amount = int(duration[:-1])
            if unit == "d":
                duration_seconds = amount * 86400
            elif unit == "h":
                duration_seconds = amount * 3600
            else:
                return await ctx.send("❌ Invalid duration. Use Nd, Nh, or perm.")

        if not permanent:
            restriction["duration"] = f"{duration_seconds}s"
        
        payload = {
            "gameJoinRestriction": restriction
        }

        patchurl = f"{self.base_url}/{user_id}"
        secondpatchurl = f"{self.second_url}/{user_id}"

        print(f"🔗 POST {self.base_url}")
        print(f"   Headers: {self.headers}")
        print(f"   Payload: {payload}")
                
        async with aiohttp.ClientSession() as session:
             async with session.patch(secondpatchurl, json=payload, headers=self.headers) as res:
                text = await res.text()
                if res.status in (200,201):
                    data = await res.json()
                    # data.path is "universes/{id}/user-restrictions/{restrictionId}"
                    rid = data["path"].rsplit("/", 1)[-1]
                else:
                    await ctx.send(f"❌ Could not retrieve bans ({res.status}): {text}")
                    
            async with session.patch(patchurl, json=payload, headers=self.headers) as res:
                text = await res.text()
                if res.status in (200,201):
                    data = await res.json()
                    # data.path is "universes/{id}/user-restrictions/{restrictionId}"
                    rid = data["path"].rsplit("/", 1)[-1]
                    
                    ban_embed = discord.Embed(
                        title=f"<:ban_hammer:918264271090106379> User Game Banned — ID: {user_id}",
                        color=discord.Color.red()
                    )
                    ban_embed.description = (
                        f"**Reason:** {reason}\n"
                        f"**Duration:** {'Permanent' if permanent else duration}\n"
                        f"**Restriction ID**: {rid}"
                    )
                    ban_embed.set_footer(
                        text=f"Banned by {ctx.author}",
                        icon_url=ctx.author.avatar.url  # or .avatar_url if on older discord.py
                    )                   
                    view = View()
                    view.add_item(
                        Button(
                            label="View Roblox Profile",
                            url=f"https://www.roblox.com/users/{user_id}/profile"
                        )
                    )
                    await ctx.send(embed=ban_embed, view=view)
                    log_ch = self.bot.get_channel(455207881747464192)
                    if log_ch:
                        await log_ch.send(embed=ban_embed, view=view)
                else:
                    ban_embed = discord.Embed(
                        title="❌ Ban failed",
                        color=discord.Color.red()
                    )
                    ban_embed.description = (f"({res.status}): {text}")
                    await ctx.send(embed=ban_embed)

    @commands.command(name="gameunban")
    @commands.has_permissions(kick_members=True)
    async def roblox_unban(self, ctx, user_id: int):
        """
        Lift any active ban on this user.
        Usage: ?gameunban <user_id>
        """
        # 1) fetch all restrictions for that user
        list_url = f"{self.base_url}/{user_id}"
        print(f"🔗 GET  {list_url}")
        async with aiohttp.ClientSession() as session:
            async with session.get(list_url, headers=self.headers) as list_res:
                body = await list_res.text()
                print(body)  # raw JSON string
                if list_res.status != 200:
                    return await ctx.send(f"❌ Could not list restrictions ({list_res.status}): {body}")
    
                data = await list_res.json()
                print(data)  # parsed JSON
    
            # 2) normalize into a Python list
            if isinstance(data, dict) and "data" in data:
                entries = data["data"]
            elif isinstance(data, dict) and "gameJoinRestriction" in data:
                entries = [data]
            else:
                entries = []
    
            # 3) filter for active bans
            active = [
                r for r in entries
                if r.get("gameJoinRestriction", {}).get("active", False)
            ]
            if not active:
                    ban_embed = discord.Embed(
                        color=discord.Color.blue()
                    )
                    ban_embed.description = ("ℹ️ No active ban found for that user.")
            
            # 4) take the first active restriction and patch it inactive
            restriction = active[0]
            rid = restriction["path"].rsplit("/", 1)[-1]
            
            patchurl = f"{self.base_url}/{rid}?updateMask=gameJoinRestriction"

            # pull from the nested gameJoinRestriction
            gjr = restriction["gameJoinRestriction"]
            reason_text  = gjr.get("displayReason") or gjr.get("privateReason", "No reason provided")
            
            # turn "3600s" → "1h", "86400s" → "1d", or Permanent
            raw = gjr.get("duration")
            if raw:
                secs = int(raw.rstrip("s"))
                days, rem = divmod(secs, 86400)
                hours, rem = divmod(rem, 3600)
                mins = rem // 60
                parts = []
                if days:  parts.append(f"{days}d")
                if hours: parts.append(f"{hours}h")
                if mins:  parts.append(f"{mins}m")
                duration_text = " ".join(parts) if parts else "0s"
            else:
                duration_text = "Permanent"

            # 3) build the patch payload
            payload = {"gameJoinRestriction": {"active": False}}
            print(f"🔗 PATCH {patchurl}")
            print(f"   Headers: {self.headers}")
            print(f"   Payload: {payload}")
    
            # 4) send the PATCH to deactivate the ban
            async with session.patch(patchurl, json=payload, headers=self.headers) as res:
                text = await res.text()
                if res.status == 200:
                    ban_embed = discord.Embed(
                        title=f"⚠️ Game Ban Lifted — ID: {user_id}",
                        color=discord.Color.from_rgb(252, 202, 98)
                    )
                    ban_embed.description = (
                        f"**Banned for:** {reason_text}\n"
                        f"**Original ban duration:** {duration_text}\n"
                        f"**Restriction ID**: {rid}"
                    )
                    ban_embed.set_footer(
                        text=f"Unbanned by {ctx.author}",
                        icon_url=ctx.author.avatar.url  # or .avatar_url if on older discord.py
                    )                   
                    view = View()
                    view.add_item(
                        Button(
                            label="View Roblox Profile",
                            url=f"https://www.roblox.com/users/{user_id}/profile"
                        )
                    )
                    await ctx.send(embed=ban_embed, view=view)
                    log_ch = self.bot.get_channel(455207881747464192)
                    if log_ch:
                        await log_ch.send(embed=ban_embed, view=view)
                else:
                    ban_embed = discord.Embed(
                        title="❌ Unban failed",
                        color=discord.Color.red()
                    )
                    ban_embed.description = (f"({res.status}): {text}")
                    
    @commands.command(name="gamebanlist")
    @commands.has_permissions(kick_members=True)
    async def roblox_list(self, ctx):
        """
        List all active Roblox game‐join bans.
        Usage: ?gambanlist
        """
        list_url = self.base_url  # GET /user‐restrictions returns all entries
        async with aiohttp.ClientSession() as session:
            async with session.get(list_url, headers=self.headers) as res:
                text = await res.text()
                if res.status != 200:
                    return await ctx.send(f"❌ Could not retrieve bans ({res.status}): {text}")
                data = await res.json()

        entries = data.get("data", [])
        # only keep active bans
        active = [
            e for e in entries
            if e.get("gameJoinRestriction", {}).get("active", False)
        ]

        if not active:
            empty = discord.Embed(
                description="ℹ️ No active bans found.",
                color=discord.Color.blue()
            )
            return await ctx.send(embed=empty)

        # build the embed
        embed = discord.Embed(
            title="📝 Active Game Bans",
            color=discord.Color.blue()
        )

        for e in active:
            # extract the Roblox user ID
            user_str = e["user"].split("/")[-1]
            gjr = e["gameJoinRestriction"]

            # reason & duration
            reason = gjr.get("displayReason") or gjr.get("privateReason", "No reason provided")
            raw    = gjr.get("duration")
            duration = "Permanent" if not raw else raw

            embed.add_field(
                name=f"User {user_str}",
                value=f"**Reason:** {reason}\n**Duration:** {duration}",
                inline=False
            )

        # send to the invoking channel
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(RobloxUserRestriction(bot))
