import discord
import time
import json
import gpt
import env
from db import db

db.execute("CREATE TABLE IF NOT EXISTS threads (channel_id TEXT PRIMARY KEY, thread_id TEXT)")
db.execute("CREATE TABLE IF NOT EXISTS disabled (channel_id TEXT PRIMARY KEY, value INTEGER)")

def get_thread(channel_id):
    # use a hashpmap to get a thread id for each user id.
    # if there is no thread id for the user id, create a new thread and return the thread id

    # if channel_id in map:
    #     return map[channel_id]

    # thread = gpt.beta.threads.create()
    # map[channel_id] = thread.id
    # return thread.id

    result = db.execute("SELECT thread_id FROM threads WHERE channel_id = ?", (channel_id,)).fetchone()

    if result:
        return result[0]

    thread = gpt.gpt.beta.threads.create()
    db.execute("INSERT INTO threads (channel_id, thread_id) VALUES (?, ?)", (channel_id, thread.id))

    db.commit()

    return thread.id


def get_disabled(channel_id):
    # if channel_id in disabled:
    #     return disabled[channel_id]
    # return False

    result = db.execute("SELECT value FROM disabled WHERE channel_id = ?", (channel_id,)).fetchone()

    if result:
        return result[0] == 1

    return False

def set_disabled(channel_id, value):
    # disabled[channel_id] = value

    db.execute("INSERT OR REPLACE INTO disabled (channel_id, value) VALUES (?, ?)", (channel_id, 1 if value else 0))
    db.commit()

    return value

def adm_check(message):
    for role in message.author.roles:
        if role.id == env.ADM_ROLE_ID:
            return True

    return False

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        #reply 
        if message.author == self.user:
            return

        print(f'Message from {message.author}: {message.content}')

        if message.channel.category_id != env.CATEGORY_ID:
            return

        if message.content == 'ping':
            await message.reply('pong')
            return

        if message.content == '$disable' and adm_check(message):
            set_disabled(message.channel.id, True)
            await message.reply('Atendimento por IA desativado no canal.')
            return

        if message.content == '$enable' and adm_check(message):
            set_disabled(message.channel.id, False)
            await message.reply('Atendimento por IA ativado no canal.')
            return

        if get_disabled(message.channel.id):
            return

        thread_id = get_thread(message.channel.id)

        msg = gpt.gpt_ask(message.content, thread_id)

        if "Atendimento transferido para um atendente." in msg:
            set_disabled(message.channel.id, True)

        await message.reply(msg)


intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run(env.DISCORD_TOKEN)