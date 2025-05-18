import os, logging
from dotenv import load_dotenv
load_dotenv()      # ← here
import pytz
import discord
import aiohttp
from datetime import timedelta
from discord.ext import commands

class RobloxUserRestriction(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_key     = os.getenv("ROBLOX_API_KEY")
        self.universe_id = os.getenv("ROBLOX_UNIVERSE_ID")
        
        logging.info(f"🔑 ROBLOX_API_KEY = {self.api_key!r}")
        logging.info(f"🌐 ROBLOX_UNIVERSE_ID = {self.universe_id!r}")

        if not self.api_key or not self.universe_id:
            raise RuntimeError("Missing ROBLOX_API_KEY or ROBLOX_UNIVERSE_ID!")
        
        # convert universe_id to int now that we know it exists
        self.universe_id = int(self.universe_id)

        self.base_url = f"https://apis.roblox.com/cloud/v2/universes/{self.universe_id}/user-restrictions"
        self.headers = {
            "x-api-key":    self.api_key,
            "Content-Type": "application/json"
        }

    @commands.command(name="rban")
    @commands.has_permissions(kick_members=True)
    async def roblox_ban(self, ctx, user_id: int, duration: str, *, reason: str):
        """
        Ban a Roblox user from joining your game.
        Usage: !rban <user_id> <7d|24h|perm> <reason>
        """
        # parse duration
        if duration.lower() == "perm":
            duration_seconds = 0  # 0 means permanent in this API
        else:
            unit = duration[-1].lower()
            amount = int(duration[:-1])
            if unit == "d":
                duration_seconds = amount * 86400
            elif unit == "h":
                duration_seconds = amount * 3600
            else:
                return await ctx.send("❌ Invalid duration. Use Nd, Nh, or perm.")

        payload = {
            "user": f"users/{user_id}",
            "gameJoinRestriction": {
                "active":            True,
                "duration":          f"{duration_seconds}s",
                "privateReason":     reason,
                "displayReason":     reason,
                "excludeAltAccounts": True
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.base_url, json=payload, headers=self.headers) as res:
                text = await res.text()
                if res.status in (200,201):
                    data = await res.json()
                    # data.path is "universes/{id}/user-restrictions/{restrictionId}"
                    rid = data["path"].rsplit("/", 1)[-1]
                    await ctx.send(f"✅ Banned <@{user_id}> for {duration}: restriction id `{rid}`.")
                else:
                    await ctx.send(f"❌ Ban failed ({res.status}): {text}")

    @commands.command(name="runban")
    @commands.has_permissions(kick_members=True)
    async def roblox_unban(self, ctx, user_id: int):
        """
        Lift any active ban on this user.
        Usage: !runban <user_id>
        """
        # first, list existing restrictions for that user
        list_url = f"{self.base_url}?user=users/{user_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(list_url, headers=self.headers) as list_res:
                if list_res.status != 200:
                    text = await list_res.text()
                    return await ctx.send(f"❌ Could not list restrictions ({list_res.status}): {text}")
                data = await list_res.json()

            # find the first active gameJoinRestriction
            restriction = next((
                r for r in data.get("data", [])
                if r["gameJoinRestriction"]["active"]
            ), None)

            if not restriction:
                return await ctx.send("ℹ️ No active ban found for that user.")

            rid = restriction["path"].rsplit("/", 1)[-1]
            patch_url = f"{self.base_url}/{rid}?updateMask=gameJoinRestriction"
            payload = {"gameJoinRestriction": {"active": False}}

            async with session.patch(patch_url, json=payload, headers=self.headers) as patch_res:
                text = await patch_res.text()
                if patch_res.status == 200:
                    await ctx.send(f"✅ Un-banned <@{user_id}> (restriction `{rid}` lifted).")
                else:
                    await ctx.send(f"❌ Unban failed ({patch_res.status}): {text}")

async def setup(bot):
    await bot.add_cog(RobloxUserRestriction(bot))
