from discord.ext import commands, tasks
from datetime import datetime, timedelta
import pytz
import math
import json
import discord

class Essentials(commands.Cog):
    """Reacts with specific emojis and manages deadlines."""

    def __init__(self, bot):
        self.bot = bot
        self.timer_file = "timers.json"
        self.timers = self.load_timers()
        self.deadline_message_id = None
        self.channel_id = 466682606373830657
        self.deadline = self.get_next_monday_midnight()
        self.check_deadline.start()
        self.role_ids = [1002600411099828326, 455190182623313940] # Replace with your desired role IDs
        self.shift_notifications_role_id = 1237844151525969930  # Role ID for Shift Notifications
        self.last_tag_time = datetime.now() - timedelta(minutes=90)  # Initialize last tag time

    message_counter = {}

    def load_timers(self):
        try:
            with open(self.timer_file, "r") as f:
                timers = json.load(f)
        except FileNotFoundError:
            return {}
        else:
            # Convert stored timestamps to datetime objects
            for user_id, timestamp in timers.items():
                timers[user_id] = datetime.fromisoformat(timestamp)
            return timers

    def save_timers(self):
        # Convert datetime objects to ISO formatted strings for JSON serialization
        timers = {str(user_id): timestamp.isoformat() for user_id, timestamp in self.timers.items()}
        with open(self.timer_file, "w") as f:
            json.dump(timers, f)

    def get_next_monday_midnight(self):
        now = datetime.now(pytz.timezone('Europe/London'))
        days_ahead = 0 - now.weekday() + 7  # Calculate days until next Monday
        if days_ahead <= 0:  # If today is Monday or later in the week, add 7 days
            days_ahead += 7
        next_monday = now + timedelta(days=days_ahead)
        next_monday_midnight = next_monday.replace(hour=0, minute=0, second=0, microsecond=0)
        return next_monday_midnight

    async def post_deadline_message(self, channel):
        self.deadline = self.get_next_monday_midnight()
        unix_timestamp = int(self.deadline.timestamp())
        message_content = f"The deadline to submit activity for this week is approximately <t:{unix_timestamp}:R>, on **<t:{unix_timestamp}:F>**"
        message = await channel.send(message_content)
        self.deadline_message_id = message.id


    @tasks.loop(minutes=1)
    async def check_deadline(self):
        now = datetime.now(pytz.timezone('Europe/London'))
        if now >= self.deadline:
            channel = self.bot.get_channel(self.channel_id)
            if channel and self.deadline_message_id:
                try:
                    message = await channel.fetch_message(self.deadline_message_id)
                    await message.delete()
                    await channel.send("Activity submissions for the week closed.")
                    await channel.send("https://tenor.com/view/rainbow-border-line-colorful-gif-17203048")
                except discord.NotFound:
                    pass
            self.deadline_message_id = None  # Reset the message ID

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
          
        if message.channel.id == self.channel_id:
            if self.deadline_message_id:
                try:
                    old_message = await message.channel.fetch_message(self.deadline_message_id)
                    await old_message.delete()
                except discord.NotFound:
                    pass
            await self.post_deadline_message(message.channel)

        if message.channel.id == 550791497880961047 and message.author.id == 1233898948100362321:
        # Check if it's been more than 2 minutes since last tag
            if datetime.now() - self.last_tag_time >= timedelta(minutes=90):
                role = message.guild.get_role(self.shift_notifications_role_id)
                if role:
                    await message.channel.send(role.mention)
                    self.last_tag_time = datetime.now()

    @commands.command()
    async def say(self, ctx, *, message):
        await ctx.send(message)
        await ctx.message.delete()

    @commands.command()
    async def start(self, ctx):
        """Starts a personal stopwatch for the user."""
        if str(ctx.author.id) in self.timers:
            await ctx.send("You already have a stopwatch running.")
            return

        self.timers[str(ctx.author.id)] = datetime.now()
        self.save_timers()
        await ctx.send("Stopwatch started.")

    @commands.command()
    async def stop(self, ctx):
        """Stops the user's personal stopwatch."""
        if str(ctx.author.id) not in self.timers:
            await ctx.send("You don't have a stopwatch running.")
            return

        elapsed_time = datetime.now() - self.timers[str(ctx.author.id)]
        elapsed_seconds = math.ceil(elapsed_time.total_seconds())
        hours, remainder = divmod(elapsed_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        del self.timers[str(ctx.author.id)]
        self.save_timers()
        elapsed_time_str = f"{hours} Hours {minutes} Minutes {seconds} Seconds"
        await ctx.send(f"Stopwatch stopped. Elapsed time: {elapsed_time_str}")

    @commands.command()
    async def time(self, ctx):
        """Displays the user's elapsed stopwatch time."""
        if str(ctx.author.id) not in self.timers:
            await ctx.send("You don't have a stopwatch running.")
            return

        elapsed_time = datetime.now() - self.timers[str(ctx.author.id)]
        elapsed_seconds = math.ceil(elapsed_time.total_seconds())
        hours, remainder = divmod(elapsed_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        elapsed_time_str = f"{hours} Hours {minutes} Minutes {seconds} Seconds"
        await ctx.send(f"Elapsed time: {elapsed_time_str}")

    @commands.command()
    async def dm(self, ctx, user: discord.User, *, message: str):
        """Sends a direct message to the specified user."""
        await user.send(message)
        await ctx.send(f"Sent a message to {user.name}.")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Gives a specified role to the new member."""
        role_id = 1002600411099828326  # Replace with the ID of the role you want to give to new members
        role = member.guild.get_role(role_id)
        if role is None:
            return
        else:
            await member.add_roles(role)

    @commands.command()
    async def giverole(self, ctx, role_name: str):
        """Gives everyone a specified role."""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role is None:
            await ctx.send(f"Role {role_name} does not exist.")
        else:
            for member in ctx.guild.members:
                await member.add_roles(role)
            await ctx.send(f"Role {role_name} has been given to everyone.")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        for role_id in self.role_ids:
            role = guild.get_role(role_id)
            if role is not None:
                await member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # Check if the reaction was added in the activity logs channel
        if payload.channel_id == 466682606373830657:
            # Check if the emoji is an "x" and the reactor is either yourself or Kay
            if str(payload.emoji) == "❌" and payload.user_id in [303491008119832577, 259143946150739969]:
                channel = self.bot.get_channel(payload.channel_id)
                message = await channel.fetch_message(payload.message_id)
                
                # Ensure the message author is not a bot
                if not message.author.bot:
                    # DM the user
                    dm_message = f"The following activity log which you have submitted has been declined: {message.jump_url}.\n\nPlease see <#466682606373830657> for more information and amend your log as required."
                    await message.author.send(dm_message)

async def setup(bot):
    await bot.add_cog(Essentials(bot))
