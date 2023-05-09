

import aiohttp
import datetime
import json
import random
import aiofiles
from loguru import logger
import requests
from dotenv import dotenv_values

config = dotenv_values(".env")


async def send_request(url, headers):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()
                if not data or response.status_code != 200:
                    logger.error(
                        f"Could not get messages, status code: {response.status_code}\n")
                return data
        except aiohttp.ClientError as error:
            print(f"Error sending request: {error}")


async def get_proxies():
    async with aiofiles.open('validProxies.txt', 'r') as f:
        global proxies
        proxies = await f.read().split("\n")


async def clear():
    async with aiofiles.open('prophecies.json', 'w') as file:
        cleared = {
            "words": [],
            "signs": []
        }
        await file.write(json.dumps(cleared))


async def get_scripture():
    async with aiofiles.open('scriptures.json', 'r', encoding='utf-8') as file:
        scriptures = json.loads(await file.read())
        scriptures = scriptures['scriptures']

        if len(scriptures) == 0:
            logger.error("Scriptures are empty.")
            return None
        scripture = random.choice(scriptures)
        logger.info(
            f"Getting a scripture index: {scriptures.index(scripture)}")
        return scripture


async def add_scripture(scripture):
    async with aiofiles.open('scriptures.json', 'r', encoding='utf-8') as file:
        scriptures = json.loads(await file.read())
        scriptures['scriptures'].append(scripture)

        async with aiofiles.open('scriptures.json', 'w', encoding='utf-8') as file:
            await file.write(json.dumps(scriptures))


async def delete_scripture(input):
    index = parse_to_number(input)
    if not index:
        return
    try:
        async with aiofiles.open('scriptures.json', 'r', encoding='utf-8') as file:
            scriptures = json.loads(await file.read())
            if index < 0 or index >= len(scriptures['scriptures']):
                logger.error(f"Index out of range: {index}")
                return
            scriptures['scriptures'].pop(index)
            logger.debug(scriptures['scriptures'])
            async with aiofiles.open('scriptures.json', 'w', encoding='utf-8') as file:
                await file.write(json.dumps(scriptures))

    except FileNotFoundError:
        logger.error(f"Scriptures file not found.")
        return


async def get_words_or_signs(type, amount=1):
    if amount > 3:
        amount = 3
    elif amount <= 0:
        amount = 1
    data = await get_prophecies()
    # logger.info(f'my data: {data}')
    if not data or type != 'words' and type != 'signs':
        logger.error(f"Failed retrieving prophecies or wrong type.")
        return
    sorted_messages = sorted(
        data[type], key=lambda x: x['date'], reverse=True)
    # logger.info('signs2')
    messages = []
    blessing = 'word' if type == 'words' else 'sign'
    praying_hands = '\U0001F64F'
    for i in range(amount):
        if i < len(sorted_messages):
            jump_url = sorted_messages[i]['jump_url']
            date = sorted_messages[i]['date'][:-5]
            content = f"``{sorted_messages[i]['content']}``" if blessing == 'word' else sorted_messages[i]['reaction']
            sign = f"{jump_url}\n\n *At {date}UTC, **Lord Graysun** has blessed us with a {blessing}:* \n\n {content}\n\n *Praise be to him* {praying_hands}\n-------------------------------------------------------\n"
            messages.append(sign)
    return messages


async def write_message_to_file(message, attr, filename):
    async with aiofiles.open(filename, 'r', encoding='utf-8') as file:
        prophecies = json.loads(await file.read())
        # logger.info(f"Data: {data}")
        if not attr in prophecies:
            logger.error(f"Invalid obj property name")
            return
        if message in prophecies[attr]:
            # logger.error(f"Message already exists")
            return

        prophecies[attr].append(message)

        async with aiofiles.open(filename, 'w', encoding='utf-8') as file:
            await file.write(json.dumps(prophecies))


async def get_prophecies():
    async with aiofiles.open('prophecies.json', 'r', encoding='utf-8') as file:
        return json.loads(await file.read())


async def get_messages():
    headers = {
        'authorization': config['TOKEN'],
        'Content-Type': 'application/json'
    }
    data = await send_request(config['MESSAGES_URL'], headers)

    # for obj in data:
    #     author = obj['author']['username']
    # author_id = obj['author']['id']
    # content = obj['content']
    # date_string = obj['timestamp']
    # date = datetime.fromisoformat(date_string[:-6])
    # formatted_date = date.strftime('%Y-%m-%d %H:%M:%S')

    # for r in reactions:
    #     logger.debug(
    #         f"reactor id: {r['id']}  \n")
    # logger.debug(
    #     f"message: {obj}  \n")

    return data


def requestDataByProxy(site, proxies, type='get', options=None,):
    proxy = random.choice(proxies)

    try:
        logger.info(f"Using a proxy [{proxy}]")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept-Language': 'en-US,en;q=0.5'
        }
        res = requests.post(
            site, proxies={'http': proxy, 'https': proxy}, headers=headers) if type == 'post' else requests.get(
            site, proxies={'http': proxy, 'https': proxy}, headers=headers)

        res.raise_for_status()
        data = res.json()
        logger.debug(f"Returned: {data}\n")
        return data
    except requests.exceptions.JSONDecodeError as err:
        logger.error(f"Json Decode Error: {err}\n")
    except requests.exceptions.HTTPError as err:
        logger.error(f"Http error: {err}\n")
    except requests.exceptions.RequestException as err:
        logger.error(f"RequestException: {err}\n")


def parse_to_number(input):
    try:
        index = int(input)
        return index
    except ValueError:
        logger.error(f"Input has to be a valid number: {input}")
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
