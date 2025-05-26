import os
import aiohttp
from aiohttp import web
import discord
from discord.ext import commands

LOG_CHANNEL_ID = 1157420902951166046  # your channel

class JoinLogger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # set up aiohttp
        self.app    = web.Application()
        self.app.router.add_post("/join", self._on_player_join)
        self.runner = web.AppRunner(self.app)
        # fire it off in the bot’s loop
        bot.loop.create_task(self._start_webserver())

    async def _start_webserver(self):
        await self.runner.setup()
        site = web.TCPSite(self.runner, "0.0.0.0", int(os.getenv("JOIN_LOG_PORT", 8080)))
        await site.start()
        print(f"[JoinLogger] HTTP server running on port {site._port}")

    async def _on_player_join(self, request: web.Request):
        data = await request.json()
        # extract your fields
        user_id   = data.get("userId")
        username  = data.get("username")
        place_id  = data.get("placeId")
        ts        = data.get("time")

        chan = self.bot.get_channel(LOG_CHANNEL_ID)
        if chan:
            embed = discord.Embed(
                title="🚪 Player Joined",
                color=discord.Color.green()
            )
            embed.add_field("Username", username, inline=True)
            embed.add_field("UserId",  user_id,  inline=True)
            embed.add_field("PlaceId", place_id, inline=True)
            embed.set_footer(text=f"Timestamp: {ts}")
            await chan.send(embed=embed)

        return web.Response(text="ok")

async def setup(bot):
    await bot.add_cog(JoinLogger(bot))

