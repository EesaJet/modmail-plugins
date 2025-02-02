    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent) -> None:
        if not payload.guild_id:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if not guild or not self.is_enabled(guild):
            return
    
        channel = guild.get_channel(payload.channel_id)
        if channel is None or self.is_whitelisted(guild, channel):
            return
    
        ignored_channel_ids = [937999681915604992]  # Adjusted to not ignore 455207881747464192
        message = payload.cached_message
        
        if message and message.author.bot and message.channel.id not in ignored_channel_ids:
            return
    
        action = "message deleted"
        embed = discord.Embed(
            color=action_colors.get(action, action_colors["normal"]),
            timestamp=discord.utils.utcnow(),
        )
        
        if message:
            if message.content:
                content = message.content
            else:
                content = "No message text - see attachments"
            
            info = (
                f"Sent by: {message.author.mention}\n"
                f"Message sent on: {discord.utils.format_dt(message.created_at)}\n"
            )
            embed.add_field(name="Message info", value=info)
            footer_text = f"Message ID: {message.id}\nChannel ID: {message.channel.id}"
            
            attachments = [a.url for a in message.attachments]
            if attachments:
                embed.add_field(name="Attachments", value="\n".join(attachments), inline=False)
        else:
            content = None
            footer_text = f"Message ID: {payload.message_id}\nChannel ID: {payload.channel_id}"
    
        embed.description = f"**Message deleted in {channel.mention}:**\n"
        if content:
            embed.description += truncate(content, Limit.embed_description - len(embed.description))
        else:
            embed.description = f":hand_splayed: Message deleted in {channel.mention}, but the contents could not be retrieved."
            embed.set_footer(text=footer_text)
        
        if channel.id == 455207881747464192:  # Check if the deleted message is from the specified channel
            repost_embed = discord.Embed(
                title="Reposted Deleted Message",
                description=content or "No content available",
                color=discord.Color.orange(),
                timestamp=discord.utils.utcnow()
            )
            repost_embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
            if attachments:
                repost_embed.add_field(name="Attachments", value="\n".join(attachments), inline=False)
            await channel.send(embed=repost_embed)
    
        await self.send_log(
            guild,
            action=action,
            embed=embed,
        )
