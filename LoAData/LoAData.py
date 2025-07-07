from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime

import discord
from discord.ext import commands

from core.models import getLogger

# --- plugin metadata (required by your loader) ---
info_json = Path(__file__).parent.resolve() / "info.json"
with open(info_json, encoding="utf-8") as f:
    __plugin_info__ = json.loads(f.read())

__version__ = __plugin_info__["version"]
__description__ = "\n".join(__plugin_info__["description"]).format(__version__)

logger = getLogger(__name__)

# --- the Cog ---
class LoAData(commands.Cog):
    __doc__ = __description__

    def __init__(self, bot: ModmailBot):
        self.bot = bot
        # get your mongo collection (AsyncIOMotorCollection)
        self.db = bot.api.get_plugin_partition(self)
        self.collection = self.db["reacted_messages"]
        # the channel & emoji to watch
        self._channel_id = 455404878202798100
        self._emoji = "✅"

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        # only in the target channel
        if payload.channel_id != self._channel_id:
            return

        # only the ✅ emoji
        if str(payload.emoji) != self._emoji:
            return

        # fetch the channel & message
        channel = self.bot.get_channel(payload.channel_id)
        if not isinstance(channel, discord.TextChannel):
            return
        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            logger.warning(f"Message {payload.message_id} not found for logging")
            return

        # build our document
        doc = {
            "message_id": message.id,
            "user_id": message.author.id,
            "content": message.content,
            "timestamp": message.created_at.isoformat()
        }

        # insert into Mongo (optionally catch dupes here)
        try:
            await self.collection.insert_one(doc)
            logger.info(f"Logged reaction on message {message.id} by {message.author.id}")
        except Exception as exc:
            logger.error(f"Failed to log reaction: {exc}")

    @commands.command(name="reactionlog_count")
    @commands.has_permissions(administrator=True)
    async def _count(self, ctx: commands.Context):
        """
        (Admin) Show how many entries are in the reaction log.
        """
        cnt = await self.collection.count_documents({})
        await ctx.send(f"✅ There are currently **{cnt}** logged reactions.")

async def setup(bot: ModmailBot) -> None:
    await bot.add_cog(LoAData(bot))
