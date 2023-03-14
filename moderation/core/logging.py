from __future__ import annotations

import io

from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING

import discord
import datetime
import pytz
import asyncio

from discord.ext.modmail_utils import Limit, plural
from discord.utils import MISSING

from core.models import getLogger
from core.utils import truncate


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

    def is_enabled(self, guild: discord.Guild) -> bool:
        """
        Returns `True` if logging is enabled for the specified guild.
        """
        config = self.cog.guild_config(str(guild.id))
        return config.get("logging", False)

    def is_whitelisted(self, guild: discord.Guild, channel: discord.TextChannel) -> bool:
        """
        Returns `True` if channel or its category is whitelisted.
        """
        config = self.cog.guild_config(str(guild.id))
        whitelist_ids = config.get("channel_whitelist", [])
        if str(channel.id) in whitelist_ids:
            return True
        category = channel.category
        if category and str(category.id) in whitelist_ids:
            return True
        return False

    async def send_log(
        self,
        guild: discord.Guild,
        *,
        action: str,
        target: Optional[
            Union[
                discord.Member,
                discord.User,
                List[discord.Member],
            ]
        ] = None,
        description: Optional[str] = None,
        moderator: Optional[discord.Member] = None,
        reason: Optional[str] = None,
        send_params: Optional[Dict[str, Any]] = None,
        **kwargs: Dict[str, Any],
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
        send_params: Optional[Dict[str, Any]]
            Additional parameter to use when sending the log message.
        """
        config = self.cog.guild_config(str(guild.id))
        channel = config.log_channel
        if channel is None:
            return

        webhook = config.webhook or await self._get_or_create_webhook(channel)
        if send_params is None:
            send_params = {}
        if webhook:
            if not config.webhook:
                config.webhook = webhook
            send_params["username"] = self.bot.user.name
            send_params["avatar_url"] = str(self.bot.user.display_avatar)
            send_params["wait"] = True
            send_method = webhook.send
        else:
            send_method = channel.send

        # In some events (e.g. message updates) the embed is already provided.
        embed = kwargs.pop("embed", None)
        if embed is None:
            color = action_colors.get(action, action_colors["normal"])
            embed = discord.Embed(
                description=description,
                color=color,
                timestamp=discord.utils.utcnow(),
            )

        # Parsing args and kwargs, and sending embed.
        embed.title = action.title()

        if target is not None:
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
                raise TypeError(
                    f"Invalid type of target. Expected Member, User, GuildChannel, List, or None. Got {type(target).__name__} instead."
                )

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
        if not self.is_enabled(after.guild):
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
            description=description,
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

    async def on_member_remove(self, member: discord.Member) -> None:
        """
        Currently this listener is to search for kicked members.
        For some reason Discord and discord.py do not dispatch or have a specific event when a guild member
        was kicked, so we have to do it manually here.
        """
        if not self.is_enabled(member.guild):
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

    async def on_member_ban(self, guild: discord.Guild, user: Union[discord.User, discord.Member]) -> None:
        if not self.is_enabled(guild):
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
        if not self.is_enabled(guild):
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
        if not self.is_enabled(channel.guild):
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
        if not self.is_enabled(channel.guild):
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

    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent) -> None:
        if not payload.guild_id:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if not guild or not self.is_enabled(guild):
            return

        channel = guild.get_channel(payload.channel_id)
        if channel is None or self.is_whitelisted(guild, channel):
            return

        message = payload.cached_message
        if message and message.author.bot:
            return

        action = "message deleted"
        embed = discord.Embed(
            color=action_colors.get(action, action_colors["normal"]),
            timestamp=discord.utils.utcnow(),
        )
        if message:
            content = f"`{message.content}`"
            info = (
                f"Sent by: {message.author.mention}\n"
                f"Message sent on: {discord.utils.format_dt(message.created_at)}\n"
            )
            embed.add_field(name="Message info", value=info)
            footer_text = f"Message ID: {message.id}\nChannel ID: {message.channel.id}"
        else:
            try:
                channel = await client.fetch_channel(payload.channel_id)
                message = await channel.fetch_message(payload.message_id)
                content = f"`{message.content}`"
                info = (
                    f"Sent by: {message.author.mention}\n"
                    f"Message sent on: {discord.utils.format_dt(message.created_at)}\n"
                )
                embed.add_field(name="Message info", value=info)
                footer_text = f"Message ID: {message.id}\nChannel ID: {channel.id}"
            except discord.NotFound:
                content = None
                footer_text = f"Message ID: {payload.message_id}\nChannel ID: {payload.channel_id}"

          
        if message.channel.id == 455207881747464192 or message.channel.id == 937999681915604992:
            embed.description = ":exclamation: A Director or member of SMT has deleted a message from this channel. Please review the main server audit logs to find the user who deleted the message."
        else:
            embed.description = f"**Message deleted in {channel.mention}:**\n"


      
        if content:
            embed.description += truncate(content, Limit.embed_description - len(embed.description))
        else:
            footer_text = f"The message is too old, it's content cannot be retrieved.\n{footer_text}"
        embed.set_footer(text=footer_text)

        await self.send_log(
            guild,
            action=action,
            embed=embed,
        )

    async def on_raw_bulk_message_delete(self, payload: discord.RawBulkMessageDeleteEvent) -> None:
        if not payload.guild_id:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if not guild or not self.is_enabled(guild):
            return

        channel = guild.get_channel(payload.channel_id)
        if channel is None or self.is_whitelisted(guild, channel):
            return

        messages = sorted(payload.cached_messages, key=lambda msg: msg.created_at)
        message_ids = payload.message_ids
        upload_text = "Deleted messages:\n\n"

        if not messages:
            upload_text += "There are no known messages.\n"
            upload_text += "Message IDs: " + ", ".join(map(str, message_ids)) + "."
        else:
            known_message_ids = set()
            for message in messages:
                known_message_ids.add(message.id)
                try:
                    time = message.created_at.strftime("%b %-d, %Y at %-I:%M %p")
                except ValueError:
                    time = message.created_at.strftime("%b %d, %Y at %I:%M %p")
                upload_text += (
                    f"{time} • {message.author} ({message.author.id})\n"
                    f"Message ID: {message.id}\n{message.content}\n\n"
                )
            unknown_message_ids = message_ids ^ known_message_ids
            if unknown_message_ids:
                upload_text += "Unknown message IDs: " + ", ".join(map(str, unknown_message_ids)) + "."

        action = "bulk message deleted"
        embed = discord.Embed(
            color=action_colors.get(action, action_colors["normal"]),
            timestamp=discord.utils.utcnow(),
        )
        embed.description = f"**{plural(len(message_ids)):message} deleted from {channel.mention}.**"
        embed.set_footer(text=f"Channel ID: {payload.channel_id}")
        fp = io.BytesIO(bytes(upload_text, "utf-8"))
        send_params = {"file": discord.File(fp, "Messages.txt")}

        await self.send_log(
            guild,
            action=action,
            embed=embed,
            send_params=send_params,
        )

    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent) -> None:
        if not payload.guild_id:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if not guild or not self.is_enabled(guild):
            return

        channel = guild.get_channel(payload.channel_id)
        if channel is None or self.is_whitelisted(guild, channel):
            return

        message_id = payload.message_id

        new_content = payload.data.get("content", "")
        old_message = payload.cached_message

        if not new_content or (old_message and new_content == old_message.content):
            # Currently does not support Embed edits
            return

        action = "message edited"
        embed = discord.Embed(
            color=action_colors.get(action, action_colors["normal"]),
            timestamp=discord.utils.utcnow(),
        )
        embed.description = f"**Message edited in {channel.mention}:**\n"
        footer_text = f"Message ID: {payload.message_id}\nChannel ID: {payload.channel_id}"

        info = None
        if old_message:
            # always ignore bot's message
            if old_message.author.bot:
                return

            embed.add_field(
                name="Before", value=truncate(old_message.content, Limit.embed_field_value) or "No Content"
            )
            info = (
                f"Sent by: {old_message.author.mention}\n"
                f"Message sent on: {discord.utils.format_dt(old_message.created_at)}\n"
            )
        else:
            try:
                message = await channel.fetch_message(message_id)
                if message.author.bot:
                    return
                info = (
                    f"Sent by: {message.author.mention}\n"
                    f"Message sent on: {discord.utils.format_dt(message.created_at)}\n"
                )
            except discord.NotFound:
                pass
            footer_text = f"The former message content cannot be found.\n{footer_text}"

        message = await channel.fetch_message(message_id)
        target = message.author
        embed.add_field(name="After", value=truncate(new_content, Limit.embed_field_value) or "No Content")
        if info is not None:
            embed.add_field(name="Message info", value=info)
        embed.set_footer(text=footer_text)
        embed.set_thumbnail(url=target.display_avatar.url)

        await self.send_log(
            guild,
            action=action,
            embed=embed,
        )
    #logs for member joining server
    async def on_member_join(self, member: discord.Member) -> None:

        config = self.cog.guild_config(str(member.guild.id))
        if not config.get("logging"):
            return

        utcnow = datetime.datetime.now(pytz.utc)
        age = utcnow - member.created_at
        age_str = f"{age.days} days, {age.seconds // 3600} hours, {(age.seconds // 60) % 60} minutes, and {age.seconds % 60} seconds"

        invites = await member.guild.invites()
        invite = None
        for i in invites:
            if i.uses != i.max_uses and i.code == i.code:
                invite = i

        if invite is not None and invite.inviter is not None:
            inviter_name = invite.inviter.name
            inviter_id = invite.inviter.id
        else:
            inviter_name = "unknown"
            inviter_id = "unknown"

        inviteorigin = invite.code
        if invite.code == "uMzaaSnGqu":
          inviteorigin =f"They joined using the invite code from the **Quality line ROBLOX group page**, which is `{invite.code}`"
        else:
          inviteorigin =f"They joined using the invite code `{invite.code}` which was generated by `{inviter_name}`."

        description = f"`{member}` has joined the server.\n{inviteorigin}.\n\nTheir account is `{age_str}` old."
    
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
