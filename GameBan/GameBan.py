import os
from dotenv import load_dotenv
load_dotenv()      # ← here

import logging, pytz, discord, aiohttp
from datetime import timedelta
from discord.ext import commands

class RobloxUserRestriction(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # your universe (game) ID
        self.universe_id = int(os.getenv("ROBLOX_UNIVERSE_ID"))
        # the API key you generated in Creator Hub
        self.api_key = os.getenv("ROBLOX_API_KEY")
        if not self.api_key or not self.universe_id:
            raise RuntimeError("Set ROBLOX_API_KEY and ROBLOX_UNIVERSE_ID env vars")

        print(os.getenv("ROBLOX_API_KEY"))
        print(os.getenv("ROBLOX_UNIVERSE_ID"))

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

        print(f"🔗 POST {self.base_url}")
        print(f"   Headers: {self.headers}")
        print(f"   Payload: {payload}")
                
        async with aiohttp.ClientSession() as session:
            async with session.patch(patchurl, json=payload, headers=self.headers) as res:
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
        Usage: ?runban <user_id>
        """
        # 1) fetch all restrictions for that user
        list_url = f"{self.base_url}/users/{user_id}"
        print(f"🔗 GET  {list_url}")
        async with aiohttp.ClientSession() as session:
            async with session.get(list_url, headers=self.headers) as list_res:
                body = await list_res.text()
                if list_res.status != 200:
                    return await ctx.send(f"❌ Could not list restrictions ({list_res.status}): {body}")
                data = await list_res.json()

        # 2) find the first active restriction
        restriction = next(
            (r for r in data.get("data", []) if r["gameJoinRestriction"]["active"]),
            None
        )
        if not restriction:
            return await ctx.send("ℹ️ No active ban found for that user.")

        # extract the restriction ID
        rid = restriction["path"].rsplit("/", 1)[-1]
        patchurl = f"{self.base_url}/{rid}?updateMask=gameJoinRestriction"

        # 3) build the patch payload
        payload = {"gameJoinRestriction": {"active": False}}
        print(f"🔗 PATCH {patchurl}")
        print(f"   Headers: {self.headers}")
        print(f"   Payload: {payload}")

        # 4) send the PATCH to deactivate the ban
        async with aiohttp.ClientSession() as session:
            async with session.patch(patchurl, json=payload, headers=self.headers) as res:
                text = await res.text()
                if res.status == 200:
                    await ctx.send(f"✅ Un-banned <@{user_id}> (restriction `{rid}` lifted).")
                else:
                    await ctx.send(f"❌ Unban failed ({res.status}): {text}")

async def setup(bot):
    await bot.add_cog(RobloxUserRestriction(bot))
