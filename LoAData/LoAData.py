from __future__ import annotations

import json
import re
from pathlib import Path
from datetime import datetime, time
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks

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
        # LOA role and UK timezone
        self.role_id = 570024555595169813
        self.tz = ZoneInfo("Europe/London")

        # kick off the nightly LOA check
        self._daily_loa_check.start()

    def cog_unload(self) -> None:
        self._daily_loa_check.cancel()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        # only in the target channel and emoji
        if payload.channel_id != self._channel_id or str(payload.emoji) != self._emoji:
            return

        channel = self.bot.get_channel(payload.channel_id)
        if not isinstance(channel, discord.TextChannel):
            return
        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            logger.warning(f"Message {payload.message_id} not found for logging")
            return

        doc = {
            "message_id": message.id,
            "user_id": message.author.id,
            "content": message.content,
            "timestamp": message.created_at.isoformat(),
        }

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

    @tasks.loop(time=time(hour=0, minute=0, tzinfo=ZoneInfo("Europe/London")))
    async def _daily_loa_check(self):
        """
        Every midnight UK local time, scan all LOA entries:
          • If start date == today → give LOA role
          • If return date == today → remove LOA role & delete entry
        """
        today = datetime.now(self.tz).date()

        channel = self.bot.get_channel(self._channel_id)
        if not isinstance(channel, discord.TextChannel):
            return
        guild = channel.guild
        role = guild.get_role(self.role_id)
        if role is None:
            logger.error(f"LOA role {self.role_id} not found in guild {guild.id}")
            return

        # regexes to extract dates in dd/mm/yy
        re_start = re.compile(r"Start Date:\s*(\d{1,2}/\d{1,2}/\d{2})")
        re_return = re.compile(r"Return Date:\s*(\d{1,2}/\d{1,2}/\d{2})")

        async for doc in self.collection.find({}):
            content = doc.get("content", "")
            user_id = doc.get("user_id")
            if not content or not user_id:
                continue

            m1 = re_start.search(content)
            m2 = re_return.search(content)
            if not (m1 and m2):
                continue

            start_date = datetime.strptime(m1.group(1), "%d/%m/%y").date()
            return_date = datetime.strptime(m2.group(1), "%d/%m/%y").date()

            try:
                member = guild.get_member(user_id) or await guild.fetch_member(user_id)
            except discord.NotFound:
                continue

            # on start date: add LOA role
            if start_date == today and role not in member.roles:
                await member.add_roles(role, reason="LOA start date reached")
            # on return date: remove role & delete the entry
            elif return_date == today:
                if role in member.roles:
                    await member.remove_roles(role, reason="LOA return date reached")
                await self.collection.delete_one({"_id": doc["_id"]})

    @_daily_loa_check.before_loop
    async def _before_daily_loa(self):
        # wait until the bot is ready
        await self.bot.wait_until_ready()


async def setup(bot: ModmailBot) -> None:
    await bot.add_cog(LoAData(bot))
