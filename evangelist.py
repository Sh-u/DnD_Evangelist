
import discord
from discord.ext import tasks
import asyncio
from loguru import logger
from dotenv import dotenv_values
from utils import clear, get_words_or_signs, write_message_to_file, get_scripture, add_scripture, delete_scripture, parse_to_number, get_replies_amount, get_messages, send_request

config = dotenv_values(".env")

intents = discord.Intents.default()
intents.message_content = True
intents.guild_messages = True
intents.dm_messages = True

client = discord.Client(intents=intents)

proxies = []
OWNER_ID = int(config['OWNER_ID'])


async def main():
    await client.start(config['BOT_TOKEN'])


@tasks.loop(minutes=1)
async def update_prophecies():
    logger.info("Updating prophecies!")
    # channel = discord.utils.get(client.get_all_channels(
    # ), guild__name='test', name='xdd')
    # if not channel:
    #     logger.error("Channel not found")
    #     return

    # logger.info(f"Channel: {channel}")

    # msgs = [message async for message in channel.history(limit=500)]
    msgs = await get_messages()

    for msg in msgs:
        logger.debug(msg.content)
        if msg['author']['id'] == int(config['TARGET_USER_ID']):

            words = {
                'date': msg['created_at'],
                'author': msg['author']['name'],
                'content': msg['content'],
                'jump_url': msg['jump_url'],
            }

            await write_message_to_file(message=words, attr='words', filename='prophecies.json').id == int(config['TARGET_USER_ID']):

            words = {
                'date': msg.created_at.strftime('%Y-%m-%d %H:%M:%S %z'),
                'author': msg.author.name,
                'content': msg.content,
                'jump_url': msg.jump_url,
            }

            await write_message_to_file(message=words, attr='words', filename='prophecies.json')
        if msg['reactions']:
            reactions = msg['reactions']
            for reaction in reactions:
                endpoint = f"https://discord.com/api/v10/channels/{config['TARGET_CHANNEL_ID']}/messages/{msg['id']}/reactions/{reaction['emoji']}"
                users = [user async for user in reaction.users()]
                for user in users:
                    if user.id != int(config['TARGET_USER_ID']):
                        continue

                    signs = {
                        'date': msg.created_at.strftime('%Y-%m-%d %H:%M:%S %z'),
                        'author': msg.author.name,
                        'content': msg.content,
                        'jump_url': msg.jump_url,
                        'reaction': str(reaction.emoji)
                    }
                    await write_message_to_file(message=signs, attr='signs', filename='prophecies.json')
                    logger.debug(user)


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
        logger.error('Tried to use command without tagging the bot.')
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
        logger.info(value)
        await delete_scripture(value)
        return

    if msg.content.startswith('!sign'):
        amount = get_replies_amount(msg.content)
        signs = await get_words_or_signs('signs', amount)
        for sign in signs:
            await target_channel.send(sign)

    if msg.content.startswith('!word'):
        amount = get_replies_amount(msg.content)
        words = await get_words_or_signs('words', amount)
        for word in words:
            await target_channel.send(word)

    if msg.content.startswith('!scripture'):
        scripture = await get_scripture()

        if not scripture:
            await target_channel.send('I am sorry my child, I do not have access to any scriptures right now...')
            return
        await target_channel.send(scripture)


asyncio.run(main())
