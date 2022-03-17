from collections import defaultdict
import datetime
import logging
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


@client.slash_command(name="vcnsetchannel", description="Set in which channel you want VCNotifier to send messages")
async def vcnsetchannel(
    ctx: discord.ApplicationContext,
    text_channel: discord.Option(str, "Channel in which you want VCNotifier to send messages", required=True),
    voice_channel: discord.Option(str, "Want to set it for specific voice channel?") = None
):
    for tch in ctx.interaction.guild.channels:
        if not (tch.type == discord.ChannelType.text and tch.name == text_channel):
            continue

        for vch in ctx.interaction.guild.channels:
            if not (vch.type == discord.ChannelType.voice and (voice_channel is None or vch.name == voice_channel)):
                continue

            notification_channels[vch.id] = tch.id
            await ctx.respond(f"Notification channel for {voice_channel if voice_channel is not None else 'all channel'} set to be {text_channel}!")
            return

        await ctx.respond(f"Voice channel {voice_channel} not found.")
        return

    await ctx.respond(f"Text channel {text_channel} not found.")


# TODO: Change notification messages with slash commands

client.run()
