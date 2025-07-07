from __future__ import annotations

import json
import re
from pathlib import Path
from datetime import datetime, time
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks

from core.models import getLogger

# --- helper for flexible date parsing ---
_MONTHS = {
    "january": 1,  "jan": 1,
    "february": 2, "feb": 2,
    "march": 3,    "mar": 3,
    "april": 4,    "apr": 4,
    "may": 5,
    "june": 6,     "jun": 6,
    "july": 7,     "jul": 7,
    "august": 8,   "aug": 8,
    "september": 9,"sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11,"nov": 11,
    "december": 12,"dec": 12,
}

def parse_flexible_date(raw: str, default_year: int) -> datetime.date | None:
    """
    Parse a date from raw text. Supports:
      - DD/MM/YY or D/M/YY
      - Dth Month [YYYY]
      - D Month [YYYY]
    Returns a date object or None if parsing fails.
    """
    cleaned = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", raw, flags=re.IGNORECASE)
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{2,4})", cleaned)
    if m:
        day, mon, yr = map(int, m.groups())
        if yr < 100:
            yr += 2000
        try:
            return datetime(year=yr, month=mon, day=day).date()
        except ValueError:
            return None
    m = re.search(r"(\d{1,2})\s+([A-Za-z]+)(?:\s+(\d{2,4}))?", cleaned)
    if m:
        day = int(m.group(1))
        mon_name = m.group(2).lower()
        yr_raw = m.group(3)
        mon = _MONTHS.get(mon_name[:3])
        if not mon:
            return None
        yr = int(yr_raw) if yr_raw else default_year
        if yr < 100:
            yr += 2000
        try:
            return datetime(year=yr, month=mon, day=day).date()
        except ValueError:
            return None
    return None

# --- plugin metadata (required by loader) ---
info_json = Path(__file__).parent.resolve() / "info.json"
with open(info_json, encoding="utf-8") as f:
    __plugin_info__ = json.loads(f.read())

__version__ = __plugin_info__["version"]
__description__ = "\n".join(__plugin_info__["description"]).format(__version__)

logger = getLogger(__name__)

class LoAData(commands.Cog):
    __doc__ = __description__

    def __init__(self, bot: ModmailBot):
        self.bot = bot
        self.db = bot.api.get_plugin_partition(self)
        self.collection = self.db["reacted_messages"]
        self._channel_id = 455404878202798100  # also error reporting channel
        self._emoji = "✅"
        self.role_id = 570024555595169813
        self.tz = ZoneInfo("Europe/London")
        self._daily_loa_check.start()

    def cog_unload(self) -> None:
        self._daily_loa_check.cancel()

    async def report_error(self, message: str) -> None:
        """Send error message to the designated channel and log it."""
        logger.error(message)
        ch = self.bot.get_channel(self._channel_id)
        if isinstance(ch, discord.TextChannel):
            try:
                await ch.send(f"⚠️ Error in LoAData: {message}")
            except Exception as exc:
                logger.error(f"Failed to report error to channel: {exc}")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.channel_id != self._channel_id or str(payload.emoji) != self._emoji:
            return
        channel = self.bot.get_channel(payload.channel_id)
        if not isinstance(channel, discord.TextChannel):
            return
        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            await self.report_error(f"Message {payload.message_id} not found for logging")
            return

        doc = {
            "message_id": message.id,
            "user_id": message.author.id,
            "content": message.content,
            "timestamp": message.created_at.isoformat(),
        }
        try:
            await self.collection.insert_one(doc)
        except Exception as exc:
            await self.report_error(f"Failed to log reaction: {exc}")

    @commands.command(name="reactionlog_count")
    @commands.has_permissions(administrator=True)
    async def _count(self, ctx: commands.Context):
        try:
            cnt = await self.collection.count_documents({})
            await ctx.send(f"✅ There are currently **{cnt}** logged reactions.")
        except Exception as exc:
            await self.report_error(f"Failed to count documents: {exc}")

    @tasks.loop(time=time(hour=14, minute=44, tzinfo=ZoneInfo("Europe/London")))
    async def _daily_loa_check(self):
        today = datetime.now(self.tz).date()
        default_year = today.year
        channel = self.bot.get_channel(self._channel_id)
        if not isinstance(channel, discord.TextChannel):
            return
        guild = channel.guild
        role = guild.get_role(self.role_id)
        if role is None:
            await self.report_error(f"LOA role {self.role_id} not found in guild {guild.id}")
            return

        async for doc in self.collection.find({}):
            content = doc.get("content", "")
            user_id = doc.get("user_id")
            if not (content and user_id):
                continue

            start_m = re.search(r"(?:Start Date|Date Start):\s*([^\n\r]+)", content, re.IGNORECASE)
            end_m = re.search(r"(?:Return Date|Date End|End Date):\s*([^\n\r]+)", content, re.IGNORECASE)
            if not (start_m and end_m):
                continue

            start_date = parse_flexible_date(start_m.group(1), default_year)
            return_date = parse_flexible_date(end_m.group(1), default_year)
            if not (start_date and return_date):
                continue

            try:
                member = guild.get_member(user_id) or await guild.fetch_member(user_id)
            except discord.NotFound:
                continue

            # start date actions
            if start_date == today:
                if role not in member.roles:
                    try:
                        await member.add_roles(role, reason="LOA start date reached")
                    except Exception as exc:
                        await self.report_error(f"Failed to add role to {member.id}: {exc}")
                old_nick = member.nick
                try:
                    await self.collection.update_one({"_id": doc["_id"]}, {"$set": {"old_nick": old_nick}})
                except Exception as exc:
                    await self.report_error(f"Failed to store old nickname for {member.id}: {exc}")
                current = member.nick or member.name
                match = re.match(r"^(🔰)\s*\w+\s*\|\|\s*(.+)$", current)
                new_nick = f"{match.group(1)} LoA || {match.group(2)}" if match else f"🔰 LoA || {current}"
                try:
                    await member.edit(nick=new_nick, reason="LOA start nickname change")
                except Exception as exc:
                    await self.report_error(f"Failed to update nickname for {member.id}: {exc}")

            # return date actions
            elif return_date == today:
                if role in member.roles:
                    try:
                        await member.remove_roles(role, reason="LOA return date reached")
                    except Exception as exc:
                        await self.report_error(f"Failed to remove role from {member.id}: {exc}")
                old_nick = doc.get("old_nick")
                try:
                    await member.edit(nick=old_nick, reason="Revert LoA nickname")
                except Exception as exc:
                    await self.report_error(f"Failed to revert nickname for {member.id}: {exc}")
                try:
                    await self.collection.delete_one({"_id": doc["_id"]})
                except Exception as exc:
                    await self.report_error(f"Failed to delete LOA entry for {member.id}: {exc}")

    @_daily_loa_check.before_loop
    async def _before_daily_loa(self):
        await self.bot.wait_until_ready()

async def setup(bot: ModmailBot) -> None:
    await bot.add_cog(LoAData(bot))
