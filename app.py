from collections import defaultdict
import datetime
import logging
import re
import discord


client = discord.Bot()

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# TODO: Replace with DB (for persistence)
# key = voice channel id
notification_channels = defaultdict(lambda: None)
notification_messages = defaultdict(lambda: "@everyone")
vc_starttimes = {}


@client.event
async def on_ready():
    for guild in client.guilds:
        logger.info(f"[ Server: {guild.name} ]")

        channels_found = [
            channel
            for channel in guild.channels
            if channel.type == discord.ChannelType.voice
        ]
        
        logger.info(f" {len(channels_found)} voice channel(s) found.")

        for channel in channels_found:
            logger.info(f" - {channel.name} [ID: {channel.id}]")

            # Notification channel defaults to system channel
            if notification_channels[channel.id] is None:
                notification_channels[channel.id] = guild.system_channel.id


# Called when someone makes some update regarding VC
@client.event
async def on_voice_state_update(
    member: discord.Member,
    before: discord.VoiceState,
    after: discord.VoiceState
):
    # Confirm that the member made inter-voicechannel moves
    if before.channel == after.channel:
        return

    # When left from somewhere
    if before.channel is not None:
        channel = before.channel
        logger.info(f"{member.name} left {channel.name}")

        # In case no one left
        if len(channel.members) == 0 and notification_channels[channel.id] is not None:
            if channel.id in vc_starttimes:
                vc_length = datetime.datetime.now() - vc_starttimes.pop(channel.id)
                message = f"Voice chat on **{channel.name}** has ended. (lasted for {vc_length})"
            else:
                message = f"Voice chat on **{channel.name}** has ended."

            await client.get_channel(notification_channels[channel.id]).send(message)
            logger.info(f"Sent \"{message}\"")
            
    # When joined somewhere
    if after.channel is not None:
        channel = after.channel
        logger.info(f"{member.name} joined {channel.name}")

        # In case new voice chat started
        if len(channel.members) == 1 and notification_channels[channel.id] is not None:
            message = f"{notification_messages[channel.id]}\n**{member.name}** has started voice chat on **{channel.name}**!"

            await client.get_channel(notification_channels[channel.id]).send(message)
            logger.info(f"Sent \"{message}\"")

            vc_starttimes[channel.id] = datetime.datetime.now()


@client.slash_command(name="vcnsetchannel", description="Set which channel VCNotifier will send messages to")
async def vcnsetchannel(
    ctx: discord.ApplicationContext,
    text_channel: discord.Option(str, "Channel in which you want VCNotifier to send messages", required=True),
    voice_channel: discord.Option(str, "Want to set it for specific voice channel?") = None
):
    # Find text channel with specified name
    textch_id = next((
        textch.id
        for textch in ctx.interaction.guild.channels
        if textch.type == discord.ChannelType.text and textch.name == text_channel
    ), None) # default value

    if textch_id is None:
        await ctx.respond(f"Text channel **{text_channel}** not found.")
        return

    # Find voice channel with specified name
    voicech_id = next((
        voicech.id
        for voicech in ctx.interaction.guild.channels
        if voicech.type == discord.ChannelType.voice and (voice_channel is None or voicech.name == voice_channel)
    ), None)

    if voicech_id is None:
        await ctx.respond(f"Voice channel **{voice_channel}** not found.")
        return

    notification_channels[voicech_id] = textch_id
    await ctx.respond(f"Notification channel for **{voice_channel if voice_channel is not None else 'all channel'}** set to be **{text_channel}**!")


@client.slash_command(name="vcnsetmessage", description="Set what VCNotifier will say")
async def vcnsetmessage(
    ctx: discord.ApplicationContext,
    message: discord.Option(str, "Message you like (can include @mention)", required=True),
    voice_channel: discord.Option(str, "Want to set it for specific voice channel?") = None
):
    # Find voice channel with specified name
    voicech_id = next((
        voicech.id
        for voicech in ctx.interaction.guild.channels
        if voicech.type == discord.ChannelType.voice and (voice_channel is None or voicech.name == voice_channel)
    ), None)

    if voicech_id is None:
        await ctx.respond(f"Voice channel **{voice_channel}** not found.")
        return

    notification_messages[voicech_id] = message
    await ctx.respond(f"Notification message for **{voice_channel if voice_channel is not None else 'all channel'}** set to be \"{message}\"!")


client.run()
