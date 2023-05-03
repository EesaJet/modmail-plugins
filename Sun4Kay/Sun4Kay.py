from datetime import datetime
from discord import Embed
from discord.ext import commands
from discord_slash import SlashContext, cog_ext
from discord_slash.utils import manage_commands
import discord

class Kay(commands.Cog):
    """Reacts with a banana emoji if someone says banana."""

    def __init__(self, bot):
        self.bot = bot
        self.log_channel_id = 1050914082083053650  # Replace with the ID of the log channel
        self.monitored_channel_ids = [466682606373830657, 455404878202798100, 773002648743706634]  # Replace with the IDs of the channels to monitor
        self.role_ids = [1002600411099828326, 455190182623313940] # Replace with your desired role IDs

    @commands.Cog.listener()
    async def on_message(self, message):
      
        exempt_words = ["SUNDAY", "SUNBURY"]
      
        if message.author.id == 259143946150739969:
            await message.add_reaction("🌸")
        if message.author.id == 303491008119832577:
            await message.add_reaction("✈️")
        if "KAY" in message.content.upper() and not message.author.bot:
            await message.add_reaction("🌸")
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
        if payload.channel_id in self.monitored_channel_ids:
            # Get the relevant information
            user_id = payload.user_id
            message_id = payload.message_id
            emoji = payload.emoji

            # Get the user, member and message objects
            guild = self.bot.get_guild(payload.guild_id)
            user = await self.bot.fetch_user(user_id)
            member = guild.get_member(user_id)
            channel = await self.bot.fetch_channel(payload.channel_id)
            message = await channel.fetch_message(message_id)

            # Create the embed object
            embed = Embed(title="Reaction added", color=0xE91E63)
            embed.add_field(name="User", value=user.mention, inline=False)
            embed.add_field(name="Channel", value=message.channel.mention, inline=True)
            embed.add_field(name="Message", value=message.content, inline=False)
            embed.add_field(name="Emoji", value=str(emoji), inline=False)
            
            # Send the embed to the log channel
            log_channel = await self.bot.fetch_channel(self.log_channel_id)
            await log_channel.send(embed=embed)
            
    @commands.slash_command(name="cake", description="Sends a cake to a user.")
    async def send_cake(self, ctx: SlashContext, user: discord.Member):
        message = f"**{user.mention}, you have been CAKED!** 🎂"
        await ctx.channel.send(message)
            
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        for role_id in self.role_ids:
            role = guild.get_role(role_id)
            if role is not None:
                await member.add_roles(role)

async def setup(bot):
    await bot.add_cog(Kay(bot))
    
#KAYA:813843744385269762
