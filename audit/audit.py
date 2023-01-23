from modmail import Plugin

class AuditLogs(Plugin):
    async def on_message(self, message):
        if message.channel.name != "audit-logs":
            return

        audit_logs = await message.guild.audit_logs(limit=100).flatten()

        for log in audit_logs:
            await message.channel.send(f'{log.user} {log.action} {log.target}')
