import datetime
import pytz
import discord
from discord.ext import commands, tasks

class RobloxGroupCount(commands.Cog):
    """A Discord bot cog to post the member count of a Roblox group."""

    def __init__(self, bot, group_id, channel_id, check_time):
        self.bot = bot
        self.group_id = 4418793
        self.channel_id = 937837334534172732
        self.check_time = check_time
        self.check_group_count.start()

    def cog_unload(self):
        self.check_group_count.cancel()

    @tasks.loop(hours=24)
    async def check_group_count(self):
        # Get the member count of the Roblox group
        url = f'https://groups.roblox.com/v1/groups/{self.group_id}'
        response = await self.bot.session.get(url)
        data = await response.json()
        member_count = data.get('memberCount', 0)

        # Check if the member count has increased since the last check
        last_member_count = await self.bot.get_cog_data(self, 'last_member_count')
        if member_count > last_member_count:
            # Update the last member count
            await self.bot.set_cog_data(self, last_member_count=member_count)

            # Post the member count in the specified channel
            channel = self.bot.get_channel(self.channel_id)
            message = f'The {data["name"]} group now has {member_count:,} members!'
            await channel.send(message)

    @check_group_count.before_loop
    async def before_check_group_count(self):
        await self.bot.wait_until_ready()

        # Convert check_time to the London, UK timezone
        london_tz = pytz.timezone('Europe/London')
        now = datetime.datetime.now(tz=london_tz)
        next_check = datetime.datetime.combine(now.date(), self.check_time, london_tz)

        # If the next check time has already passed today, add one day to the next check time
        if next_check <= now:
            next_check += datetime.timedelta(days=1)

        # Sleep until the next check time
        await discord.utils.sleep_until(next_check)

        # Send the group count before starting the loop
        await self.check_group_count()

def setup(bot):
    # Replace these with your own values
    group_id = 4418793
    channel_id = 937837334534172732
    check_time = datetime.time(hour=20, minute=10)

    bot.add_cog(RobloxGroupCount(bot, group_id, channel_id, check_time))
