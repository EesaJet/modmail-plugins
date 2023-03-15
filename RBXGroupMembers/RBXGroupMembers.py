import datetime
import pytz
import asyncio
import discord
from discord.ext import commands, tasks

class RobloxGroupCount(commands.Cog):
    """A Discord bot plugin that sends the count of members in a Roblox group."""

    def __init__(self, bot, group_id, channel_id):
        self.bot = bot
        self.group_id = 4418793
        self.channel_id = 937837334534172732
        self.check_group_count.start()

    def cog_unload(self):
        self.check_group_count.cancel()

    @tasks.loop()
    async def check_group_count(self):
        await self.bot.wait_until_ready()

        # Convert check_time to the London timezone
        london_tz = pytz.timezone('Europe/London')
        now = datetime.datetime.now(tz=london_tz)
        check_time = datetime.time(hour=20, minute=04)
        next_check = datetime.datetime.combine(now, check_time, london_tz)

        # If the next check time has already passed today, add one day to the next check time
        if next_check <= now:
            next_check += datetime.timedelta(days=1)

        # Sleep until the next check time
        await asyncio.sleep((next_check - now).total_seconds())

        # Send the group count
        await self.send_group_count()

    async def send_group_count(self):
        # Get the group member count
        group_url = f'https://groups.roblox.com/v1/groups/{self.group_id}'
        async with self.bot.session.get(group_url) as response:
            data = await response.json()
        member_count = data['memberCount']

        # Get the channel where the group count should be posted
        channel = self.bot.get_channel(self.channel_id)

        # Check if the group count has increased since the last check
        last_count = await self.bot.redis.get(f'group_count:{self.group_id}', encoding='utf-8')
        if last_count is not None and int(last_count) >= member_count:
            return

        # Post the group count in the channel
        message = f'The group member count is now {member_count}.'
        await channel.send(message)

        # Update the last count in Redis
        await self.bot.redis.set(f'group_count:{self.group_id}', member_count)

def setup(bot):
    # Set the group ID and channel ID
    group_id = 4418793  # Replace with your group ID
    channel_id = 937837334534172732  # Replace with your channel ID

    # Create the plugin instance
    plugin = RobloxGroupCount(bot, group_id, channel_id)

    # Add the plugin to the bot
    bot.add_cog(plugin)
