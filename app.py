import logging
import discord


client = discord.Client()

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@client.event
async def on_ready():
    channels_found = []
    for channel in client.get_all_channels():
        if channel.type != discord.ChannelType.voice:
            continue
        channels_found.append(channel)
    
    if not channels_found:
        return
    
    logger.info(f"{len(channels_found)} voice channel(s) found.")
    for channel in channels_found:
        logger.info(f"{channel.name} [ID: {channel.id}]")


client.run()
