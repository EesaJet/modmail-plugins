import discord
from discord.ext import commands
import datetime

class Ethan(commands.Cog):
    """Reacts with a banana emoji if someone says banana."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id == 455404878202798100 and "Start date:" in message.content and "Return date:" in message.content:
            # Send a message to prompt you to react
            print("Bot detected a valid message in the specified channel.")
            prompt_message = await message.channel.send("React with ✅ to confirm.")
            await prompt_message.add_reaction("✅")

            # Wait for your reaction
            def check(reaction, user):
                return user == message.author and str(reaction.emoji) == "✅"
            
            try:
                print("Bot is waiting for your reaction...")
                reaction, user = await self.bot.wait_for("reaction_add", timeout=10.0, check=check)
            except asyncio.TimeoutError:
                print("You didn't react in time. Aborting.")
                return
            
            print("You reacted with ✅. Continuing with role assignment...")
            start_date = None
            return_date = None
            lines = message.content.split('\n')
            for line in lines:
                if line.startswith("Start date:"):
                    start_date = datetime.datetime.strptime(line.split(":")[1].strip(), '%d/%m/%y')
                elif line.startswith("Return date:"):
                    return_date = datetime.datetime.strptime(line.split(":")[1].strip(), '%d/%m/%y')
            
            current_date = datetime.datetime.now()
            if start_date <= current_date <= return_date:
                print("Current date is within the specified range. Assigning role...")
                user = message.author
                guild = message.guild
                role = discord.utils.get(guild.roles, id=570024555595169813)  # Your role ID
                await user.add_roles(role)
                
                await self.schedule_role_removal(user, role, return_date)
            else:
                print("Current date is not within the specified range. Role assignment skipped.")

        if "ETHAN" in message.content.upper():
            await message.add_reaction("🍌")
            print("Bot reacted with 🍌 to message containing 'ETHAN'.")

    async def schedule_role_removal(self, user, role, return_date):
        while True:
            current_date = datetime.datetime.now()
            if current_date >= return_date:
                await user.remove_roles(role)
                print(f"Role {role.name} removed from {user.name} as return date has passed.")
                break
            else:
                await asyncio.sleep(60)

async def setup(bot):
    bot.add_cog(Ethan(bot))

