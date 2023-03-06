from __future__ import annotations

from typing import List, Optional, Union, TYPE_CHECKING

import discord
import datetime
import pytz

from discord.utils import MISSING

from core.models import getLogger


if TYPE_CHECKING:
    from bot import ModmailBot
    from ..moderation import Moderation


logger = getLogger(__name__)

action_colors = {
    "normal": discord.Color.blue(),

    #greens
    "user joined voice channel": discord.Color.green(),
    "invite created": discord.Color.green(),
    "member joined": discord.Color.green(),

    #reds
    "ban": discord.Color.red(),
    "member left": discord.Color.red(),
    "user left voice channel": discord.Color.red(),
    "message deleted": discord.Color.red(),
    "multiban": discord.Color.red(),
    "invite deleted": discord.Color.red(),

    #others
    "message edited": discord.Color.yellow(),
    "mute": discord.Color.dark_grey(),
}


class ModerationLogging:
    """
    ModerationLogging instance to handle and manage the logging feature.
    """

    def __init__(self, cog: Moderation):
        self.cog: Moderation = cog
        self.bot: ModmailBot = cog.bot

    async def send_log(
        self,
        guild: discord.Guild,
        *,
        action: str,
        target: Union[discord.Member, discord.User, List[discord.Member]],
        description: str,
        moderator: Optional[discord.Member] = None,
        reason: Optional[str] = None,
        **kwargs,
    ) -> None:
        """
        Sends logs to the log channel.

        Parameters
        ----------
        guild: discord.Guild
            Guild object. This is to fetch the guild config.
        action: str
            The moderation action.
        target: discord.Member or discord.User or List
            Target that was executed from this moderation action.
            Could be a list of "Member" or "User" especially if the action is "multiban".
        description: str
            A message to be put in the Embed description.
        moderator: Optional[discord.Member]
            Moderator that executed this moderation action.
        reason: Optional[str]
            Reason for this moderation action.
        """
        config = self.cog.guild_config(str(guild.id))

        if not config.get("logging"):
            return
        channel = config.log_channel
        if channel is None:
            return

        send_params = {}
        webhook = config.webhook or await self._get_or_create_webhook(channel)
        if webhook:
            if not config.webhook:
                config.webhook = webhook
            send_params["username"] = self.bot.user.name
            send_params["avatar_url"] = str(self.bot.user.display_avatar)
            send_params["wait"] = True
            send_method = webhook.send
        else:
            send_method = channel.send

        # Parsing args and kwargs, and sending embed.
        color = action_colors.get(action, action_colors["normal"])
        embed = discord.Embed(
            title=action.title(),
            description=description,
            color=color,
            timestamp=discord.utils.utcnow(),
        )

        if isinstance(target, (discord.Member, discord.User)):
            embed.set_thumbnail(url=target.display_avatar.url)
            embed.add_field(name="User", value=target.mention)
            embed.set_footer(text=f"User ID: {target.id}")
        elif isinstance(target, list):
            embed.add_field(
                name="User" if len(target) == 1 else "Users",
                value="\n".join(str(m) for m in target),
            )
        elif isinstance(target, discord.abc.GuildChannel):
            embed.add_field(name="Channel", value=f"# {target.name}")
            embed.set_footer(text=f"Channel ID: {target.id}")
        else:
            raise TypeError("Invalid type of parameter `target`. Expected type: `Member`, `User`, or `List`.")

        if reason is not None:
            embed.add_field(name="Reason", value=reason)

        # extra info
        for key, value in kwargs.items():
            name = key.replace("_", " ").capitalize()
            embed.add_field(name=name, value=value)

        if moderator is not None:
            embed.add_field(name="Moderator", value=moderator.mention, inline=False)

        send_params["embed"] = embed
        return await send_method(**send_params)

    async def _get_or_create_webhook(self, channel: discord.TextChannel) -> Optional[discord.Webhook]:
        """
        An internal method to retrieve an existing webhook from the channel if any, otherwise a new one
        will be created.

        Parameters
        -----------
        channel : discord.TextChannel
            The channel to get or create the webhook from.
        """
        config = self.cog.guild_config(str(channel.guild.id))
        wh_url = config.get("webhook")
        if wh_url:
            wh = discord.Webhook.from_url(
                wh_url,
                session=self.bot.session,
                bot_token=self.bot.token,
            )
            wh = await wh.fetch()
            return wh

        # check bot permissions first
        bot_me = channel.guild.me
        if not bot_me or not channel.permissions_for(bot_me).manage_webhooks:
            return None

        wh = None
        webhooks = await channel.webhooks()
        if webhooks:
            # find any webhook that has token which means that belongs to the client
            wh = discord.utils.find(lambda x: x.token is not None, webhooks)

        if not wh:
            avatar = await self.bot.user.display_avatar.read()
            try:
                wh = await channel.create_webhook(
                    name=self.bot.user.name,
                    avatar=avatar,
                    reason="Webhook for Moderation logs.",
                )
            except Exception as e:
                logger.error(f"{type(e).__name__}: {str(e)}")
                wh = None

        if wh:
            config.set("webhook", wh.url)
            await config.update()

        return wh

    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        """
        General member update events will be caught from here.
        As of now, we only look for these events:
        - Guild avatar update
        - Nickname changes
        - Timed out changes
        - Role updates
        """
        config = self.cog.guild_config(str(after.guild.id))
        if not config.get("logging"):
            return

        if before.guild_avatar != after.guild_avatar:
            return await self._on_member_guild_avatar_update(before, after)

        audit_logs = after.guild.audit_logs(limit=10)
        found = False
        async for entry in audit_logs:
            if int(entry.target.id) == after.id:
                action = entry.action
                if action == discord.AuditLogAction.member_update:
                    if hasattr(entry.after, "nick"):
                        found = True
                        await self._on_member_nick_update(before, after, entry.user, reason=entry.reason)
                    elif hasattr(entry.after, "timed_out_until"):
                        found = True
                        await self._on_member_timed_out_update(before, after, entry.user, reason=entry.reason)
                elif action == discord.AuditLogAction.member_role_update:
                    found = True
                    await self._on_member_role_update(before, after, entry.user, reason=entry.reason)
                if found:
                    return

    async def _on_member_guild_avatar_update(self, before: discord.Member, after: discord.Member) -> None:
        action = "updated" if after.guild_avatar is not None else "removed"
        description = f"`{after}` {action} their guild avatar."
        await self.send_log(
            after.guild,
            action="avatar update",
            target=after,
        )

    async def _on_member_nick_update(
        self,
        before: discord.Member,
        after: discord.Member,
        moderator: discord.Member,
        *,
        reason: Optional[str] = None,
    ) -> None:
        action = "set" if before.nick is None else "removed" if after.nick is None else "updated"
        description = f"`{after}`'s nickname was {action}"
        description += "." if after.nick is None else f" to `{after.nick}`."
        await self.send_log(
            after.guild,
            action="nickname",
            target=after,
            moderator=moderator if moderator != after else None,
            reason=reason if reason else "None",
            description=description,
            before=f"`{str(before.nick)}`",
            after=f"`{str(after.nick)}`",
        )

    async def _on_member_role_update(
        self,
        before: discord.Member,
        after: discord.Member,
        moderator: discord.Member,
        *,
        reason: Optional[str] = None,
    ) -> None:
        description = f"`{after}`'s roles were updated."
        added = [role for role in after.roles if role not in before.roles]
        removed = [role for role in before.roles if role not in after.roles]
        kwargs = {}
        if added:
            kwargs["added"] = "\n".join(r.mention for r in added)
        if removed:
            kwargs["removed"] = "\n".join(r.mention for r in removed)

        await self.send_log(
            after.guild,
            action="role update",
            target=after,
            moderator=moderator if moderator != after else None,
            reason=reason if reason else "None",
            description=description,
            **kwargs,
        )

    async def _on_member_timed_out_update(
        self,
        before: discord.Member,
        after: discord.Member,
        moderator: discord.Member,
        *,
        reason: Optional[str] = None,
    ) -> None:
        if moderator == self.bot.user:
            # handled in mute/unmute command
            return

        kwargs = {}
        description = f"`{after}`"
        if after.timed_out_until is None:
            action = "unmute"
            description += " has been unmuted."
        elif before.timed_out_until is None:
            action = "mute"
            description += " has been muted."
            kwargs["expires"] = discord.utils.format_dt(after.timed_out_until, "R")
        else:
            action = "mute update"
            description += "'s mute time out has been updated."
            kwargs["before"] = discord.utils.format_dt(before.timed_out_until, "F")
            kwargs["after"] = discord.utils.format_dt(after.timed_out_until, "F")

        await self.send_log(
            after.guild,
            action=action,
            target=after,
            description=description,
            moderator=moderator,
            reason=reason,
            **kwargs,
        )

    #logs for edited messages
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        config = self.cog.guild_config(str(after.guild.id))
        if not config.get("logging"):
            return
        
        audit_logs = after.guild.audit_logs(limit=10)
        found = False
        async for entry in audit_logs:
            if str(entry.target.id) == after.id:
                action = entry.action
                if action == discord.AuditLogAction.message_edit:
                    found = True
                    await self._on_message_edit(before, after, entry.user, reason=entry.reason)
                if found:
                    return
                

        if before.content == after.content:
              return  # ignore if the message content hasn't changed
        guild = before.guild
        author = before.author
        channel = before.channel
        description = f"Message edited by {author.mention} in {channel.mention}"
        mBefore: before.content
        mAfter: after.content
  
        await self.send_log(
            guild,
            action="message edited",
            target=author,
            description=description,
            before=f"`{str(before.content)}`",
            after=f"`{str(after.content)}`",
        )

    #logs for deleted messages
    async def on_message_delete(self, message: discord.Message) -> None:
      
        config = self.cog.guild_config(str(message.guild.id))
        if not config.get("logging"):
            return

        audit_logs = message.guild.audit_logs(limit=10)
        async for entry in audit_logs:
            if entry.target.id == message.author.id and entry.action in (discord.AuditLogAction.message_delete, discord.AuditLogAction.message_bulk_delete):
                mod = entry.user
                if mod == self.bot.user:
                    return
        author = message.author
        channel = message.channel
        description = f"The following message was deleted from {channel.mention}:\n`{message.content}`"

        await self.send_log(
            message.guild,
            action="message deleted",
            target=author,
            description=description,
        )

  
    async def on_member_remove(self, member: discord.Member) -> None:
        """
        Currently this listener is to search for kicked members.
        For some reason Discord and discord.py do not dispatch or have a specific event when a guild member
        was kicked, so we have to do it manually here.
        """
        config = self.cog.guild_config(str(member.guild.id))
        if not config.get("logging"):
            return

        audit_logs = member.guild.audit_logs(limit=10, action=discord.AuditLogAction.kick)
        async for entry in audit_logs:
            if int(entry.target.id) == member.id:
                break
        else:
            return

        mod = entry.user
        if mod == self.bot.user:
            return

        if entry.created_at.timestamp() < member.joined_at.timestamp():
            return

        await self.send_log(
            member.guild,
            action="kick",
            target=member,
            moderator=mod,
            reason=entry.reason,
            description=f"`{member}` has been kicked.",
        )

    #logs for member joining server
    async def on_member_join(self, member: discord.Member) -> None:

        config = self.cog.guild_config(str(member.guild.id))
        if not config.get("logging"):
            return

        utcnow = datetime.datetime.now(pytz.utc)
        age = utcnow - member.created_at
        age_str = f"{age.days} days, {age.seconds // 3600} hours, {(age.seconds // 60) % 60} minutes, and {age.seconds % 60} seconds"

        inviter = None
        invites_before = await member.guild.invites()
        await asyncio.sleep(1)  # wait 1 second to ensure invite info has updated
        invites_after = await member.guild.invites()
        for invite in invites_after:
            if invite not in invites_before:
                inviter = invite.inviter
    
        description = f"`{member}` has joined the server. Their account is {age_str} old."
    
        if inviter:
            description += f" They were invited by `{inviter}` using the invite `{invite.code}`."
    
        await self.send_log(
            member.guild,
            action="member joined",
            target=member,
            description=description,
        )

    #logs for creating invite
    async def on_invite_create(self, invite: discord.Invite) -> None:

        config = self.cog.guild_config(str(invite.guild.id))
        if not config.get("logging"):
            return
          
        member = invite.inviter
        if invite.max_uses == 0:
          invitemaxuses = "**has no limit of uses**"
        else:
          invitemaxuses =f"can be used {invite.max_uses} times"
        if invite.max_age == 0:
          invitemaxage = "**never expires**"
        else:
          invitemaxage =f"expires in {invite.max_age // 60} minutes from when this message was sent"
          

        await self.send_log(
            invite.guild,
            action="invite created",
            target=member,
            description=f"`{invite.inviter}` created server invite {invite.url} which {invitemaxuses} and {invitemaxage}",
        )

        #logs for deleting invite
    async def on_invite_delete(self, invite: discord.Invite) -> None:

        config = self.cog.guild_config(str(invite.guild.id))
        if not config.get("logging"):
            return


        async for log in invite.guild.audit_logs(limit=10, action=discord.AuditLogAction.invite_delete):
            if log.target == invite:
                member = log.user
                # Send a log message showing who deleted the invite
                await self.send_log(
                    invite.guild,
                    action="invite deleted",
                    target=member,
                    description=f"`{log.user}` deleted the server invite {invite.url}.",
                )
      
    #logs for member joinin/leaving VC
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:

        config = self.cog.guild_config(str(member.guild.id))
        if not config.get("logging"):
            return

        if before.channel is not None and after.channel is None:
            await self.send_log(
                member.guild,
                action="user left voice channel",
                target=member,
                description=f"`{member}` has left `{before.channel.name}`",
            )
        if before.channel is None and after.channel is not None:
            await self.send_log(
                  member.guild,
                  action="user joined voice channel",
                  target=member,
                  description=f"`{member}` has joined `{after.channel.name}`",
            )


    #logs for member leaving server  
    async def on_member_remove(self, member: discord.Member) -> None:

        config = self.cog.guild_config(str(member.guild.id))
        if not config.get("logging"):
            return

        await self.send_log(
            member.guild,
            action="member left",
            target=member,
            description=f"`{member}` has left the server.",
        )    
        
    async def on_member_ban(self, guild: discord.Guild, user: Union[discord.User, discord.Member]) -> None:
        config = self.cog.guild_config(str(guild.id))
        if not config.get("logging"):
            return

        audit_logs = guild.audit_logs(limit=10, action=discord.AuditLogAction.ban)
        async for entry in audit_logs:
            if int(entry.target.id) == user.id:
                break
        else:
            logger.error("Cannot find the audit log entry for user ban of %d, guild %s.", user, guild)
            return

        mod = entry.user
        if mod == self.bot.user:
            return

        if isinstance(user, discord.Member):
            if not user.joined_at or entry.created_at.timestamp() < user.joined_at.timestamp():
                return

        await self.send_log(
            guild,
            action="ban",
            target=user,
            moderator=mod,
            reason=entry.reason,
            description=f"`{user}` has been banned.",
        )

    async def on_member_unban(self, guild: discord.Guild, user: discord.User) -> None:
        config = self.cog.guild_config(str(guild.id))
        if not config.get("logging"):
            return

        audit_logs = guild.audit_logs(limit=10, action=discord.AuditLogAction.unban)
        async for entry in audit_logs:
            if int(entry.target.id) == user.id:
                break
        else:
            logger.error("Cannot find the audit log entry for user unban of %d, guild %s.", user, guild)
            return

        mod = entry.user
        if mod == self.bot.user:
            return

        await self.send_log(
            guild,
            action="unban",
            target=user,
            moderator=mod,
            reason=entry.reason,
            description=f"`{user}` is now unbanned.",
        )

    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel) -> None:
        config = self.cog.guild_config(str(channel.guild.id))
        if not config.get("logging"):
            return

        audit_logs = channel.guild.audit_logs(limit=10, action=discord.AuditLogAction.channel_create)
        async for entry in audit_logs:
            if int(entry.target.id) == channel.id:
                break
        else:
            logger.error(
                "Cannot find the audit log entry for channel creation of %d, guild %s.", channel, guild
            )
            return

        mod = entry.user

        kwargs = {}
        if channel.category:
            kwargs["category"] = channel.category.name

        await self.send_log(
            channel.guild,
            action="channel created",
            target=channel,
            moderator=mod,
            description=f"Channel {channel.mention} was created.",
            reason=entry.reason,
            **kwargs,
        )

    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel) -> None:
        config = self.cog.guild_config(str(channel.guild.id))
        if not config.get("logging"):
            return

        audit_logs = channel.guild.audit_logs(limit=10, action=discord.AuditLogAction.channel_delete)
        async for entry in audit_logs:
            if int(entry.target.id) == channel.id:
                break
        else:
            logger.error(
                "Cannot find the audit log entry for channel deletion of %d, guild %s.", channel, guild
            )
            return

        mod = entry.user

        kwargs = {}
        if channel.category:
            kwargs["category"] = channel.category.name

        await self.send_log(
            channel.guild,
            action="channel deleted",
            target=channel,
            moderator=mod,
            description=f"Channel `# {channel.name}` was deleted.",
            reason=entry.reason,
            **kwargs,
        )
