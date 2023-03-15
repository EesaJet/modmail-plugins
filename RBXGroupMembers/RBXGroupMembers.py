from discord.ext import commands
import requests

class RobloxGroup(commands.Cog):
    """Sends a message to a specified channel with the total number of members in a Roblox group when a new person joins."""

    def __init__(self, bot, group_id, channel_id):
        self.bot = bot
        self.group_id = 2572027
        self.channel_id = 1079457518788554772

    @commands.Cog.listener()
    async def on_member_join(self, member):
        url = f'https://groups.roblox.com/v1/groups/{self.group_id}'
        response = requests.get(url)
        data = response.json()
        member_count = data['memberCount']

        channel = self.bot.get_channel(self.channel_id)
        await channel.send(f'{member.mention} just joined the group! Total members now: {member_count}')

async def setup(bot):
    # Set your Roblox group ID and channel ID here
    group_id = 2572027
    channel_id = 1079457518788554772

    await bot.add_cog(RobloxGroup(bot, group_id, channel_id))
