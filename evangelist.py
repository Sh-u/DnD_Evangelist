
import datetime
import discord
from discord.ext import tasks
import asyncio
from loguru import logger
import urllib.parse
import os
from utils import clear, get_words_or_signs, write_message_to_file, get_scripture, add_scripture, delete_scripture, get_replies_amount, send_request


intents = discord.Intents.default()
intents.message_content = True
intents.guild_messages = True
intents.dm_messages = True

client = discord.Client(intents=intents)

TARGET_CHANNEL_ID = os.environ.get('TARGET_CHANNEL_ID')
OWNER_ID = int(os.environ.get('OWNER_ID'))
SERVER_ID = str(os.environ.get('SERVER_ID'))
BOT_TOKEN = os.environ.get('BOT_TOKEN')
TOKEN = os.environ.get('TOKEN')
TARGET_USER_ID = str(os.environ.get('TARGET_USER_ID'))

MESSAGES_ENDPOINT = f"https://discord.com/api/v8/channels/{TARGET_CHANNEL_ID}/messages?limit=100"
headers = {
    'authorization': TOKEN,
    'Content-Type': 'application/json'
}


async def main():
    await client.start(BOT_TOKEN)


@tasks.loop(minutes=1)
async def update_prophecies():
    logger.info("Updating prophecies!")
    r_count = 0
    m_count = 0
    msgs = await send_request(MESSAGES_ENDPOINT, headers)

    if not msgs or len(msgs) == 0:
        logger.error("No messages found")

    for msg in msgs:

        date = msg.get('timestamp')
        date = datetime.datetime.fromisoformat(date)
        date = date.strftime('%Y-%m-%d %H:%M:%S')
        author = msg.get('author').get('username')
        content = msg.get('content') if msg.get('content') else ' '
        msg_id = msg.get('id')

        if not date:
            logger.error('Missing date')
            continue
        if not content:
            logger.error('Missing content')
            continue
        if not author:
            logger.error('Missing author')
            continue

        jump_url = f"https://discord.com/channels/{SERVER_ID}/{TARGET_CHANNEL_ID}/{msg_id}"

        if msg['author']['id'] == TARGET_USER_ID:
            m_count += 1
            logger.debug(f'Messages amount: {m_count}')

            words = {
                'date': date,
                'author': author,
                'content': content,
                'jump_url': jump_url,
            }

            await write_message_to_file(message=words, attr='words', filename='prophecies.json')
        if msg.get('reactions'):
         
            reactions = msg['reactions']

            for reaction in reactions:
                emoji = reaction['emoji']
                r = emoji.get('name')

                if emoji.get('id'):
                    r = f":{emoji['name']}:"
                    emoji = f"{emoji['name']}:{emoji['id']}"
                else:
                    emoji = emoji.get('name')
                    r = str(emoji)
                    emoji = urllib.parse.quote(emoji)
                # logger.info(r)
                endpoint = f"https://discord.com/api/v10/channels/{TARGET_CHANNEL_ID}/messages/{msg_id}/reactions/{emoji}"

                users = await send_request(endpoint, headers)
                for user in users:

                    if user['id'] != TARGET_USER_ID:
                        continue
                    r_count += 1
                    logger.debug(f'Reactions count: {r_count}')

                    signs = {
                        'date': date,
                        'author': author,
                        'content': content,
                        'jump_url': jump_url,
                        'reaction': r
                    }
                    await write_message_to_file(message=signs, attr='signs', filename='prophecies.json')


@ client.event
async def on_ready():
    logger.info(f'Logged in as {client.user}')
    update_prophecies.start()


@ client.event
async def on_message(msg):

    if msg.author.bot:
        return

    logger.info(f"Received message from {msg.author}: {msg.content}")

    target_channel = msg.author
    if not isinstance(msg.channel, discord.DMChannel) and client.user in msg.mentions:
        target_channel = msg.channel
    elif not isinstance(msg.channel, discord.DMChannel):
        logger.warning('Tried to use command without tagging the bot.')
        return

    if msg.content.startswith('!clear') and msg.author.id == OWNER_ID:
        await clear()
        return

    if msg.content.startswith('!add_scripture') and msg.author.id == OWNER_ID:
        _, value = msg.content.split(' ', 1)
        await add_scripture(value)
        return

    if msg.content.startswith('!delete_scripture') and msg.author.id == OWNER_ID:
        _, value = msg.content.split(' ', 1)
        await delete_scripture(value)
        return

    if msg.content.startswith('!sign'):
        amount = get_replies_amount(msg.content)
        signs = await get_words_or_signs('signs', amount)

        if not signs or len(signs) == 0:
            await target_channel.send('I am sorry my child, we are praying for the lord to give us a sign...')
            return
        for sign in signs:
            await target_channel.send(sign)

    if msg.content.startswith('!word'):
        amount = get_replies_amount(msg.content)
        words = await get_words_or_signs('words', amount)
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
