

import aiohttp
from datetime import datetime
import random
import aiofiles
from loguru import logger
import os
import sys


DEBUG = True if sys.argv[1] and sys.argv[1] == 'DEBUG' else False
logger.debug(DEBUG)
BOT_TOKEN = os.environ.get('EVANGELIST_BOT_TOKEN')
TOKEN = os.environ.get('EVANGELIST_TOKEN')

PROPHECIES_ID = os.environ.get('EVANGELIST_PROPHECIES_BIN_ID')
SCRIPTURES_ID = os.environ.get('EVANGELIST_SCRIPTURES_BIN_ID')
BIN_MASTER_KEY = os.environ.get('EVANGELIST_BIN_MASTER')
SCRIPTURES_CHANNEL_ID = os.environ.get('EVANGELIST_SCRIPTURES_CHANNEL_ID')
TEST_CHANNEL_ID = os.environ.get('EVANGELIST_TEST_CHANNEL_ID')
TEST_SERVER_ID = os.environ.get('EVANGELIST_TEST_SERVER_ID')


OWNER_ID = os.environ.get('EVANGELIST_OWNER_ID')


SERVER_ID = os.environ.get(
    'EVANGELIST_SERVER_ID') if not DEBUG else TEST_SERVER_ID
GRAYSUN_USER_ID = os.environ.get(
    'EVANGELIST_GRAYSUN_USER_ID') if not DEBUG else OWNER_ID
SDF_USER_ID = os.environ.get(
    'EVANGELIST_SDF_USER_ID') if not DEBUG else OWNER_ID
NEWS_CHANNEL_ID = os.environ.get(
    'EVANGELIST_NEWS_CHANNEL_ID') if not DEBUG else TEST_CHANNEL_ID
TARGET_CHANNEL_ID = os.environ.get(
    'EVANEGLIST_TARGET_CHANNEL_ID') if not DEBUG else TEST_CHANNEL_ID

MESSAGES_ENDPOINT = f"https://discord.com/api/v8/channels/{TARGET_CHANNEL_ID}/messages?limit=100"

headers = {
    'authorization': TOKEN,
    'Content-Type': 'application/json'
}


async def _request_bin(bin_id, method, data=None):
    url = f"https://api.jsonbin.io/v3/b/{bin_id}"
    headers = {
        'Content-Type': 'application/json',
        'X-Master-Key': f"{BIN_MASTER_KEY}"
    }
    async with aiohttp.ClientSession() as session:
        try:

            request_method = getattr(session, method)

            async with request_method(url, data=data, headers=headers) as response:
                logger.warning(f"master: {BIN_MASTER_KEY}, bin id: {bin_id}")
                response.raise_for_status()
                data = await response.json()
                logger.debug(data)
                if not data or response.status != 200:
                    logger.error(
                        f"Could not process the bin, status code: {response.status}\n")

                return data
        except aiohttp.ClientError as error:
            logger.error(f"Error sending request: {error}")


async def send_request(url, headers):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()

                if not data or response.status != 200:
                    logger.error(
                        f"Could not get messages, status code: {response.status}\n")

                return data
        except aiohttp.ClientError as error:
            logger.error(f"Error sending request: {error}")


async def update_bin(data, bin_id):
    await _request_bin(bin_id, 'put', data=data)


async def get_bin(bin_id):
    return await _request_bin(bin_id, 'get')


async def get_proxies():
    async with aiofiles.open('validProxies.txt', 'r') as f:
        global proxies
        proxies = await f.read().split("\n")


async def get_prophecies():
    return await get_bin(PROPHECIES_ID)


async def get_scripture():
    scriptures = await get_bin(SCRIPTURES_ID)
    scriptures = scriptures['scriptures']

    if len(scriptures) == 0:
        logger.error("Scriptures are empty.")
        return None
    scripture = random.choice(scriptures)
    logger.debug(
        f"Getting a scripture index: {scriptures.index(scripture)}")
    return scripture


async def add_scriptures(messages):
    scriptures = await get_bin(SCRIPTURES_ID)

    for message in messages:
        if message in scriptures['scriptures']:
            continue
        scriptures['scriptures'].append(message)

    await update_bin(scriptures, SCRIPTURES_ID)


async def get_replies(type, amount=1):
    if amount > 3:
        amount = 3
    elif amount <= 0:
        amount = 1
    prophecies = await get_prophecies()

    logger.debug(prophecies)

    if not prophecies or type != 'words' and type != 'signs':
        logger.error(f"Failed retrieving prophecies or wrong type.")
        return
    sorted_messages = sorted(
        prophecies[type], key=lambda x: x['date'], reverse=True)

    replies = []
    blessing = 'word' if type == 'words' else 'sign'

    for i in range(amount):
        if i < len(sorted_messages):
            reply = generate_reply(sorted_messages[i], blessing)
            if i != amount-1:
                reply += "\n--------------------------------------------"
            replies.append(reply)

    return replies


async def add_prophecies(message, attr, client=None):
    logger.debug('add prophecies')
    prophecies = await get_bin(PROPHECIES_ID)
    if not attr in prophecies:
        logger.error(f"Invalid obj property name")
        return

    if message in prophecies[attr]:
        return

    prophecies[attr].append(message)

    await update_bin(prophecies, PROPHECIES_ID)
    if not client:
        logger.error(f"Client is not defined")
        return

    channel = client.get_channel(NEWS_CHANNEL_ID)

    if not channel:
        logger.error(f"Channel is not defined")
        return

    reply = get_replies(attr, 1)
    await channel.send(reply)


def generate_reply(message, blessing):
    praying_hands = '\U0001F64F'

    jump_url = message['jump_url']
    date = message['date'][:-5]
    date_obj = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
    date = date_obj.strftime(
        '%B %d' + ('th' if 4 <= date_obj.day <= 20 or 24 <= date_obj.day <= 30 else ['st', 'nd', 'rd'][date_obj.day % 10 - 1]))

    reacted_message = f"a mortal's voice echoed: \n *`{message['content']}`*"
    content = message['content']
    reaction = message.get('reaction')
    reply = ""
    author = f"the mighty lord **{message['author']}**" if message['author'] == 'Graysun' else f"the unsung hero of the heavens **{message['author']}**"
    if blessing == 'sign':
        reply = f"{jump_url} On {date} {reacted_message}\nTherefore {author} blessed us with a {blessing}: {reaction}\nPraise be to him {praying_hands}"
    else:
        reply = f"{jump_url} On {date}, {author} blessed us with a {blessing}: \n`{content}`\nPraise be to him {praying_hands}"
    return reply


async def process_message(msg, prophecies):

    date = msg.get('timestamp')
    date = datetime.fromisoformat(date)
    date = date.strftime('%Y-%m-%d %H:%M:%S')
    author = msg.get('author').get('username')
    content = msg.get('content') if msg.get('content') else ' '
    msg_id = msg.get('id')

    if not date:
        logger.error('Missing date')
        return
    if not content:
        logger.error('Missing content')
        return
    if not author:
        logger.error('Missing author')
        return

    jump_url = f"https://discord.com/channels/{SERVER_ID}/{TARGET_CHANNEL_ID}/{msg_id}"
    author_id = msg.get('author').get('id')

    if author_id == GRAYSUN_USER_ID or author_id == SDF_USER_ID:
        logger.success('found message')
        words = {
            'date': date,
            'author': author,
            'content': content,
            'jump_url': jump_url,
        }
        await add_prophecies(message=words, attr='words')

    if msg.get('reactions'):
        reactions = msg['reactions']
        target_reactions = []
        author = ''
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

            endpoint = f"https://discord.com/api/v10/channels/{SERVER_ID}/messages/{msg_id}/reactions/{emoji}"
            users = await send_request(endpoint, headers)

            for user in users:
                if user['id'] == GRAYSUN_USER_ID:
                    author = 'Graysun'
                    break
                elif user['id'] == SDF_USER_ID:
                    author = 'sdf'
                    break

            if not author:
                continue
            target_reactions.append(r)

        signs = {
            'date': date,
            'author': author,
            'content': content,
            'jump_url': jump_url,
            'reaction': ' '.join(target_reactions)
        }
        await add_prophecies(message=signs, attr='signs')


def parse_to_number(input):
    try:
        index = int(input)
        return index
    except ValueError:
        logger.warning(f"Input has to be a valid number: {input}")
        return


def get_replies_amount(args):
    amount = 1
    splitted = args.split(' ')

    if len(splitted) > 1:
        amount = parse_to_number(
            splitted[1])
        if amount is None:
            amount = 1

    return amount
