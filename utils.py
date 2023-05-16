
import os
import sys
from datetime import datetime
import urllib
import aiohttp
import aiofiles
from loguru import logger
import random


DEBUG = True if len(sys.argv) >= 2 and sys.argv[1] == 'DEBUG' else False
logger.debug(DEBUG)
BOT_TOKEN = os.environ.get('EVANGELIST_BOT_TOKEN')
TOKEN = os.environ.get('EVANGELIST_TOKEN')

PROPHECIES_ID = os.environ.get('EVANGELIST_PROPHECIES_BIN_ID')
SCRIPTURES_ID = os.environ.get('EVANGELIST_SCRIPTURES_BIN_ID')
BIN_MASTER_KEY = os.environ.get('EVANGELIST_BIN_MASTER')
SCRIPTURES_CHANNEL_ID = os.environ.get('EVANGELIST_SCRIPTURES_CHANNEL_ID')
TEST_CHANNEL_ID = os.environ.get('EVANGELIST_TEST_CHANNEL_ID')
TEST_NEWS_CHANNEL_ID = os.environ.get('EVANGELIST_TEST_NEWS_CHANNEL_ID')
TEST_SERVER_ID = os.environ.get('EVANGELIST_TEST_SERVER_ID')


OWNER_ID = os.environ.get('EVANGELIST_OWNER_ID')


SERVER_ID = os.environ.get(
    'EVANGELIST_SERVER_ID') if not DEBUG else TEST_SERVER_ID
GRAYSUN_USER_ID = os.environ.get(
    'EVANGELIST_GRAYSUN_USER_ID') if not DEBUG else OWNER_ID
SDF_USER_ID = os.environ.get(
    'EVANGELIST_SDF_USER_ID') if not DEBUG else OWNER_ID
TERENCE_USER_ID = os.environ.get(
    'EVANGELIST_TERENCE_USER_ID') if not DEBUG else OWNER_ID
NEWS_CHANNEL_ID = os.environ.get(
    'EVANGELIST_NEWS_CHANNEL_ID') if not DEBUG else TEST_NEWS_CHANNEL_ID
TARGET_CHANNEL_ID = os.environ.get(
    'EVANEGLIST_TARGET_CHANNEL_ID') if not DEBUG else TEST_CHANNEL_ID

MESSAGES_ENDPOINT = f"https://discord.com/api/v8/channels/{TARGET_CHANNEL_ID}/messages?limit=100"

headers = {
    'authorization': TOKEN,
    'Content-Type': 'application/json'
}


async def process_message(msg, prophecies, news=None):

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
        logger.success(f'found message: {content}')
        words = {
            'id': msg_id,
            'date': date,
            'author': author,
            'author_id': author_id,
            'content': content,
            'jump_url': jump_url,
        }
        news_message = await add_prophecies(prophecies, word_or_sign=words, attr='words')
        if news_message:
            news.append(news_message)

    if msg.get('reactions'):
        logger.success(f'found reactions: {content}')
        reactions = msg['reactions']
        target_reactions = []
        author = ''
        reactor_id = ""
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

            endpoint = f"https://discord.com/api/v10/channels/{TARGET_CHANNEL_ID}/messages/{msg_id}/reactions/{emoji}"
            users = await send_request(endpoint, headers)

            for user in users:

                if user['id'] == GRAYSUN_USER_ID:
                    author = user['username']
                    reactor_id = user['id']
                    break
                elif user['id'] == SDF_USER_ID or user['id'] == TERENCE_USER_ID:
                    author = user['username']
                    reactor_id = user['id']
                    break

            if not author:
                continue
            target_reactions.append(r)

        signs = {
            'id': msg_id,
            'date': date,
            'author_id': reactor_id,
            'author': author,
            'content': content,
            'jump_url': jump_url,
            'reaction': ' '.join(target_reactions)
        }
        news_message = await add_prophecies(prophecies, word_or_sign=signs, attr='signs')
        if news_message:
            news.append(news_message)


async def add_prophecies(prophecies, word_or_sign, attr):
    # logger.debug(f"Adding message: {word_or_sign.get('content')}")
    if attr not in prophecies:
        logger.error("Invalid obj property name")
        return
    prophecy_id = word_or_sign.get('id')
    prophecy_reaction = word_or_sign.get('reaction')
    index_to_replace = -1
    for i, d in enumerate(prophecies[attr]):
        if d['id'] == prophecy_id:
            index_to_replace = i
            break

    if index_to_replace != -1:
        if prophecy_reaction and len(prophecy_reaction) > len(prophecies[attr][index_to_replace]['reaction']):
            prophecies[attr][index_to_replace] = word_or_sign
        else:
            return
    else:
        prophecies[attr].append(word_or_sign)

    sorted_messages = [word_or_sign]
    reply = get_replies(attr, 1, sorted_messages=sorted_messages)[0]
    reply = {
        'date': word_or_sign['date'],
        'content': reply
    }
    return reply


def sort_messages(messages: list, reverse=True):

    return sorted(
        messages, key=lambda x: x['date'], reverse=reverse)


def get_replies(attr, amount=1, sorted_messages=None):
    # logger.debug(f'getting replies for sorted_message: {sorted_messages[0]}')
    if not sorted_messages:
        logger.error("Sorted messages are not defined")
        return
    # logger.warning(f"amount: {amount}, msgs: {len(sorted_messages)}")
    if amount > 1 and amount >= len(sorted_messages):
        amount = len(sorted_messages)
    elif amount <= 0:
        amount = 1

    replies = []
    blessing = 'word' if attr == 'words' else 'sign'

    for i in range(amount):
        if i < len(sorted_messages):
            reply = generate_reply(sorted_messages[i], blessing)
            if i != amount-1:
                reply += "\n--------------------------------------------"
            replies.append(reply)

    return replies


def ordinal(n):
    if not isinstance(n, int):
        return ''
    elif 11 <= n <= 13:
        return f'{n}th'
    elif n % 10 == 1:
        return f'{n}st'
    elif n % 10 == 2:
        return f'{n}nd'
    elif n % 10 == 3:
        return f'{n}rd'
    else:
        return f'{n}th'


def generate_reply(message, blessing):

    # logger.warning(
    #     f"Generating a reply for a message: {message} with blessing: {blessing}")
    praying_hands = '\U0001F64F'
    praying_hands = ''
    jump_url = message['jump_url']
    date = message['date']
    date_obj = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')

    date = date_obj.strftime('%B ') + ordinal(date_obj.day) + \
        date_obj.strftime(', %H:%M:%S UTC')

    reacted_message = f"a mortal's voice echoed: \n*`{message['content']}`*"
    content = message['content']
    reaction = message.get('reaction')
    reply = ""
    author_id = message.get('author_id')
    author = f"the mighty lord **{message['author']}**" \
        if author_id == GRAYSUN_USER_ID else f"the unsung hero of the heavens **{message['author']}**"

    if blessing == 'sign':
        reply = f"{jump_url} On {date} {reacted_message}\nThereupon" \
            f" {author} blessed us with a {blessing}: {reaction}\n*Praise be to him!*{praying_hands}"
    else:
        reply = f"{jump_url} On {date} {author} blessed us with a {blessing}: " \
            f"\n`{content}`\n*Praise be to him!*{praying_hands}"

    return reply


async def _request_bin(bin_id, method, data=None):
    url = f"https://api.jsonbin.io/v3/b/{bin_id}"
    header = {
        'Content-Type': 'application/json',
        'X-Master-Key': f"{BIN_MASTER_KEY}"
    }
    async with aiohttp.ClientSession() as session:
        try:

            request_method = getattr(session, method)

            async with request_method(url, json=data, headers=header) as response:
                logger.warning(f"making a request: {method}, for url: {url}")
                response.raise_for_status()
                data = await response.json()

                if not data or response.status != 200:
                    logger.error(
                        f"Could not process the bin, status code: {response.status}\n")

                return data
        except aiohttp.ClientError as error:
            logger.error(f"Error sending request: {error}")


async def send_request(url, header):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=header) as response:
                response.raise_for_status()
                data = await response.json()

                if not data or response.status != 200:
                    logger.error(
                        f"Could not get messages, status code: {response.status}\n")

                return data
        except aiohttp.ClientError as error:
            logger.error(f"Error sending request: {error}")


async def update_bin(data, bin_id):
    await _request_bin(bin_id, 'put', data)


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
    scriptures = scriptures['record']['scriptures']

    if not scriptures or len(scriptures) == 0:
        logger.error("Scriptures are empty.")
        return None
    scripture = random.choice(scriptures)
    # logger.debug(
    #     f"Getting a scripture index: {scriptures.index(scripture)}")
    return scripture


async def add_scriptures(messages, scriptures):
    b_added = False
    for message in messages:
        content = message.content

        if content in scriptures['scriptures']:
            # logger.error('that scripture already exists')
            continue
        scriptures['scriptures'].append(content)
        b_added = True

    return b_added


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
