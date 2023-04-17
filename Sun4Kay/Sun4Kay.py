from datetime import datetime
from discord import Embed
from discord.ext import commands

class Kay(commands.Cog):
    """Reacts with a banana emoji if someone says banana."""

    def __init__(self, bot):
        self.bot = bot
        self.log_channel_id = 1050914082083053650  # Replace with the ID of the log channel
        self.monitored_channel_id = 466682606373830657  # Replace with the ID of the channel to monitor

    @commands.Cog.listener()
    async def on_message(self, message):
      
        exempt_words = ["SUNDAY", "SUNBURY"]
      
        if "KAY" in message.content.upper() and not message.author.bot:
            await message.add_reaction("KAYA:813843744385269762")
        if "SUN" in message.content.upper() and not message.author.bot and all(exemption not in message.content.upper() for exemption in exempt_words):
            await message.channel.send("Here comes the sun!")
            await message.channel.send("<a:KayA:813843744385269762>")
        if "MELLOW" in message.content.upper() and not message.author.bot:
            await message.channel.send("STOP IT MELLOW!")
            await message.channel.send(":black_cat:")
        if "BREAKDATE" in message.content.upper() and not message.author.bot:
            await message.channel.send("ROTOXIC HAVE DONE A BREAKDATE! :boom:")
            await message.channel.send("https://tenor.com/view/roblox-developer-crash-gif-24842627")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.channel_id == self.monitored_channel_id:
            # Get the relevant information
            user_id = payload.user_id
            message_id = payload.message_id
            emoji = payload.emoji
            event_time = datetime.utcfromtimestamp(payload.event_time)

            # Get the user, member and message objects
            guild = self.bot.get_guild(payload.guild_id)
            user = await self.bot.fetch_user(user_id)
            member = guild.get_member(user_id)
            channel = await self.bot.fetch_channel(payload.channel_id)
            message = await channel.fetch_message(message_id)

            # Create the embed object
            embed = Embed(title="Reaction added", color=0xFFD700)
            embed.add_field(name="User", value=user.mention, inline=False)
            embed.add_field(name="Message", value=message.jump_url, inline=False)
            embed.add_field(name="Emoji", value=str(emoji), inline=False)
            embed.add_field(name="Timestamp", value=event_time.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
            embed.set_thumbnail(url=user.avatar_url)

            # Send the embed to the log channel
            log_channel = await self.bot.fetch_channel(self.log_channel_id)
            await log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Kay(bot))
