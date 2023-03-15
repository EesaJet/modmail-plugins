from discord.ext import commands, tasks
import requests
import pytz
import datetime
import asyncio


class RobloxGroup(commands.Cog):
    """Sends a message to a specified channel with the total number of members in a Roblox group every day at a specified time."""

    def __init__(self, bot, group_id, channel_id, check_time):
        self.bot = bot
        self.group_id = 2572027
        self.channel_id = 455189806180466701
        self.check_time = datetime.time(hour=10, minute=0)
        self.member_count = None

    async def send_group_count(self):
        url = f'https://groups.roblox.com/v1/groups/{self.group_id}'
        response = requests.get(url)
        data = response.json()
        member_count = data['memberCount']

        if member_count >= self.member_count:
            self.member_count = member_count
            channel = self.bot.get_channel(self.channel_id)
            await channel.send(f"Good morning Quality line! Great news, today we have **{member_count} members** in the ROBLOX group!\nLet the sun shine up your day <a:KayA:813843744385269762>")

    @tasks.loop(hours=24)
    async def check_group_count(self):
        await self.send_group_count()

    @check_group_count.before_loop
    async def before_check_group_count(self):
        await self.bot.wait_until_ready()
    
        # Convert check_time to the US/Eastern timezone
        london_tz = pytz.timezone('Europe/London')
        now = datetime.datetime.now(tz=london_tz)
        check_time = datetime.time(hour=10, minute=0)
        next_check = datetime.datetime.combine(now, check_time, london_tz)
    
        # If the next check time has already passed today, add one day to the next check time
        if next_check <= now:
            next_check += datetime.timedelta(days=1)
    
        # Sleep until the next check time
        await asyncio.sleep((next_check - now).total_seconds())
    
        # Send the group count before starting the loop
        await self.send_group_count()
    
        def cog_unload(self):
            self.check_group_count.cancel()

async def setup(bot):
    # Set your Roblox group ID, channel ID, and check time here
    group_id = 2572027
    channel_id = 455189806180466701
    check_time = datetime.time(hour=10, minute=0)

    cog = RobloxGroup(bot, group_id, channel_id, check_time)
    bot.add_cog(cog)
    cog.check_group_count.start()

