import copy
import asyncio
import discord
from discord.ext import tasks
from loguru import logger
from utils import (BOT_TOKEN,
                   MESSAGES_ENDPOINT,
                   NEWS_CHANNEL_ID,
                   PROPHECIES_ID, SCRIPTURES_ID, get_bin,
                   get_prophecies,
                   headers,
                   get_replies,
                   add_scriptures,
                   get_scripture,
                   get_replies_amount,
                   process_message,
                   send_request,
                   SCRIPTURES_CHANNEL_ID,
                   sort_messages,
                   update_bin)


intents = discord.Intents.default()
intents.message_content = True
intents.guild_messages = True
intents.dm_messages = True

client = discord.Client(intents=intents)


async def main():
    await client.start(BOT_TOKEN)


@tasks.loop(minutes=30)
async def update_scriptures():
    logger.info("Updating scriptures!")

    channel = client.get_channel(
        int(SCRIPTURES_CHANNEL_ID))

    if not channel or not SCRIPTURES_CHANNEL_ID:
        logger.error("No scriptures channel found")
        return
    messages = [message async for message in channel.history(limit=500)]

    scriptures = await get_bin(SCRIPTURES_ID)
    scriptures = scriptures['record']
    if not scriptures:
        logger.error("No scriptures found")
        return

    b_addded = await add_scriptures(messages, scriptures)

    if not b_addded:
        logger.info('No new scriptures found')
        return

    await update_bin(scriptures, SCRIPTURES_ID)


@tasks.loop(minutes=2)
async def update_prophecies():
    logger.info("Updating prophecies!")

    msgs = await send_request(MESSAGES_ENDPOINT, headers)

    if not msgs or len(msgs) == 0:
        logger.error("No messages found")
        return
    prophecies = await get_prophecies()
    prophecies = prophecies.get('record')
    old_prophecies = copy.deepcopy(prophecies)
    news = []
    if not prophecies:
        logger.error("No prophecies found")
        return

    routines = [process_message(msg, prophecies=prophecies,
                                news=news) for msg in msgs]

    await asyncio.gather(*routines)
    logger.debug('done processing')
    if prophecies == old_prophecies:
        logger.info("No new prophecies found")
        return

    if not client:
        logger.error("Client is not defined")
        return

    channel = client.get_channel(int(NEWS_CHANNEL_ID))
    if not channel:
        logger.error("Channel is not defined")
        return

    updated = await update_bin(prophecies, PROPHECIES_ID)

    if not news or len(news) == 0:
        logger.error('No news.')
        return

    if not updated:
        logger.error('Bin not updated.')
        return

    news = sort_messages(messages=news, reverse=False)

    for msg in news:
        # logger.debug(f"message: {msg}, channnel: {channel}")
        await channel.send(msg['content'])


@ client.event
async def on_ready():
    logger.info(f'Logged in as {client.user}')
    update_prophecies.start()
    update_scriptures.start()


@ client.event
async def on_message(msg):

    if msg.author.bot:
        return

    target_channel = msg.author
    if not isinstance(msg.channel, discord.DMChannel) and client.user in msg.mentions:
        target_channel = msg.channel
    elif not isinstance(msg.channel, discord.DMChannel):
        return
    logger.debug(f"Received message from {msg.author}: {msg.content}")
    if msg.content.startswith('!sign'):
        amount = get_replies_amount(msg.content)
        prophecies = await get_prophecies()

        signs = prophecies.get('record').get('signs')

        if not signs or len(signs) == 0:
            await target_channel.send('I am sorry my child, we are praying for the lord to give us a sign...')
            return

        sorted_messages = sort_messages(messages=signs)
        replies = get_replies('signs', amount, sorted_messages)

        for reply in replies:
            await target_channel.send(reply)

    if msg.content.startswith('!word'):
        amount = get_replies_amount(msg.content)
        prophecies = await get_prophecies()
        words = prophecies.get('record').get('words')

        if not words or len(words) == 0:
            await target_channel.send('I am sorry my child, we are praying for the lord to speak...')
            return

        sorted_messages = sort_messages(messages=words)
        replies = get_replies('words', amount, sorted_messages)

        for reply in replies:
            await target_channel.send(reply)

    if msg.content.startswith('!scripture'):
        scripture = await get_scripture()

        if not scripture:
            await target_channel.send('I am sorry my child, I do not have access to any scriptures right now...')
            return
        await target_channel.send(scripture)


asyncio.run(main())
