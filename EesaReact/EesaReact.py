from discord.ext import commands
from datetime import datetime, timedelta
import pytz
import math
import json
import discord

class Eesa(commands.Cog):
    """Reacts with specific emojis and manages deadlines."""

    def __init__(self, bot):
        self.bot = bot
        self.timer_file = "timers.json"
        self.timers = self.load_timers()
        self.deadline_message_id = None
        self.channel_id = 466682606373830657

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
        deadline = self.get_next_monday_midnight()
        message_content = f"The deadline is {deadline.strftime('%Y-%m-%d %H:%M:%S %Z')}."
        message = await channel.send(message_content)
        self.deadline_message_id = message.id

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if "EESA" in message.content.upper():
            await message.add_reaction("✈️")
        elif "SHIT" in message.content.upper():
            await message.add_reaction("💩")
        elif "DAFFY" in message.content.upper():
            await message.add_reaction("👑")
        elif "SHANIE" in message.content.upper():
            await message.add_reaction("🌸")
        elif "MIKE" in message.content.upper():
            await message.add_reaction("CANTERBURY:1097286182527828109")
        elif "JONATHAN" in message.content.upper():
            await message.add_reaction("JONATHAN:1080274489465651283")

        if message.channel.id == self.channel_id:
            if self.deadline_message_id:
                try:
                    old_message = await message.channel.fetch_message(self.deadline_message_id)
                    await old_message.delete()
                except discord.NotFound:
                    pass
            await self.post_deadline_message(message.channel)

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

async def setup(bot):
    await bot.add_cog(Eesa(bot))
