from collections import defaultdict
import datetime
import logging
import discord


client = discord.Client()

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
                notification_channels[channel.id] = guild.system_channel


# Called when someone makes some update regarding VC
@client.event
async def on_voice_state_update(member, before, after):
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

            await notification_channels[channel.id].send(message)
            logger.info(f"Sent \"{message}\"")
            
    # When joined somewhere
    if after.channel is not None:
        channel = after.channel
        logger.info(f"{member.name} joined {channel.name}")

        # In case new voice chat started
        if len(channel.members) == 1 and notification_channels[channel.id] is not None:
            message = f"{notification_messages[channel.id]}\n**{member.name}** has started voice chat on **{channel.name}**!"

            await notification_channels[channel.id].send(message)
            logger.info(f"Sent \"{message}\"")

            vc_starttimes[channel.id] = datetime.datetime.now()


# TODO: Change notification channels with slash commands
# TODO: Change notification messages with slash commands

client.run()
