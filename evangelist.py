
import discord
from discord.ext import tasks
import asyncio
from loguru import logger
from utils import BOT_TOKEN, MESSAGES_ENDPOINT, get_prophecies, headers, get_replies, add_scriptures, get_scripture,  get_replies_amount, process_message, send_request, SCRIPTURES_CHANNEL_ID


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
    channel = client.get_channel(SCRIPTURES_CHANNEL_ID)
    messages = [message async for message in channel.history(limit=500)]
    await add_scriptures(messages)


@tasks.loop(minutes=1)
async def update_prophecies():
    logger.info("Updating prophecies!")

    msgs = await send_request(MESSAGES_ENDPOINT, headers)

    if not msgs or len(msgs) == 0:
        logger.error("No messages found")
        return
    prophecies = await get_prophecies()
    for msg in msgs:
        process_message(msg, prophecies)

    await asyncio.gather(*tasks)


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
    logger.info(f"Received message from {msg.author}: {msg.content}")
    if msg.content.startswith('!sign'):
        amount = get_replies_amount(msg.content)
        logger.debug(amount)
        signs = await get_replies('signs', amount)
        logger.debug(signs)

        if not signs or len(signs) == 0:
            await target_channel.send('I am sorry my child, we are praying for the lord to give us a sign...')
            return
        for sign in signs:
            await target_channel.send(sign)

    if msg.content.startswith('!word'):
        amount = get_replies_amount(msg.content)
        words = await get_replies('words', amount)
        if not words or len(words) == 0:
            await target_channel.send('I am sorry my child, we are praying for the lord to speak...')
            return

        for word in words:
            await target_channel.send(word)

    if msg.content.startswith('!scripture'):
        scripture = await get_scripture()

        if not scripture:
            await target_channel.send('I am sorry my child, I do not have access to any scriptures right now...')
            return
        await target_channel.send(scripture)


asyncio.run(main())
