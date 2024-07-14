class Kay(commands.Cog):
    """Reacts with a banana emoji if someone says banana."""

    def __init__(self, bot):
        self.bot = bot
        self.role_ids = [1002600411099828326, 455190182623313940] # Replace with your desired role IDs
        self.shift_notifications_role_id = 1237844151525969930  # Role ID for Shift Notifications
        self.last_tag_time = datetime.now() - timedelta(minutes=90)  # Initialize last tag time
        
    @commands.Cog.listener()
    async def on_message(self, message):
        exempt_words = ["SUNDAY", "SUNBURY"]
    
        if "KAY" in message.content.upper() and not message.author.bot:
            await message.add_reaction("🌸")
        if "SUN" in message.content.upper() and not message.author.bot and all(
                exemption not in message.content.upper() for exemption in exempt_words):
            await message.channel.send("Here comes the sun!")
            await message.channel.send("<a:KayA:813843744385269762>")
        if "MELLOW" in message.content.upper() and not message.author.bot:
            await message.channel.send("STOP IT MELLOW!")
            await message.channel.send(":black_cat:")
        if "BREAKDATE" in message.content.upper() and not message.author.bot:
            await message.channel.send("ROTOXIC HAVE DONE A BREAKDATE! :boom:")
            await message.channel.send("https://tenor.com/view/roblox-developer-crash-gif-24842627")
        if "STUDIO" in message.content.upper() and not message.author.bot:
            await message.channel.send("\"Fucking Studio 😡\" ~ Kay 2024")

async def setup(bot):
    await bot.add_cog(Kay(bot))
