import discord
import asyncio

client = discord.Client()

@asyncio.coroutine
def my_background_task():
    yield from client.wait_until_ready()
    counter = 0
    channel = discord.Object(id='283729943521656835')
    while not client.is_closed:
        counter += 1
        yield from client.send_message(channel, counter)
        yield from asyncio.sleep(60) # task runs every 60 seconds

@client.event
@asyncio.coroutine
def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

client.loop.create_task(my_background_task())
client.run('MjgzNzI3ODU1MDQzNzM5NjY5.C45RuA.DvqiMBa8CDkvm_BVt4srXgpKnJk')
