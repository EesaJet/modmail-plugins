import modmail

@modmail.plugin
async def audit_logs(client, message):
    if message.channel.name != "audit-logs":
        return

    audit_logs = await message.guild.audit_logs(limit=100).flatten()

    for log in audit_logs:
        await message.channel.send(f'{log.user} {log.action} {log.target}')
