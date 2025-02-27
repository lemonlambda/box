import discord
import ollama
import re
import pprint
import threading
import asyncio
import random
import aiohttp
import base64
import io
import os
from PIL import Image
from discord.ext import commands

from globals import bot, system_message, chat_history, transcription, trans_lock, chat_history

def fawait(arg):
    global bot
    # Ensure that args contains a coroutine
    return asyncio.run_coroutine_threadsafe(arg, bot.loop).result()

async def long_message(func, message: str, chunk_size: int = 2000):
    """Splits a long message into chunks and sends them, avoiding word cuts if possible."""
    while len(message) > chunk_size:
        split_index = message.rfind(" ", 0, chunk_size)  # Find the last space before limit
        if split_index == -1:
            split_index = chunk_size  # If no space is found, split at exact limit
        await func(message[:split_index])
        message = message[split_index:].lstrip()  # Remove leading spaces in the next chunk
    await func(message)  # Send the remaining part

async def thread_it(func, *args, **kwargs):
    # Create a queue to retrieve the result from the thread
    result_queue = asyncio.Queue()

    args = args + (result_queue,)

    # Start a new thread to call Ollama
    threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True).start()

    return await result_queue.get()

def nthread_it(func, *args, **kwargs):
    loop = asyncio.get_running_loop()
    asyncio.run_coroutine_threadsafe(func(*args, **kwargs), loop)
    
def append_transcription(message):
    if message.content == "" or message.content == None:
        return
    if message.content[0] == "!":
        return
    
    with trans_lock:
        transcription[0] += f"{message.content}\n"

def append_messages(message):
    guild_id = message.guild.id
    
    if chat_history.get(guild_id) == None:
        chat_history[guild_id] = [{"role": "system", "content": system_message}]
    chat_history[guild_id].append({"role": "user", "content": transcription[0]})
    with trans_lock:
        transcription[0] = ""

# A helper class for working with messages of indeterminate length
class LongMessage(object):
    def __init__(self, context):
        self.context = context

    async def __respond(self, func, content = None, **kwargs):
        if content == None:
            return
        
        chunk_size = 2000
        """Splits a long message into chunks and sends them, avoiding word cuts if possible."""
        while len(content) > chunk_size:
            split_index = content.rfind(" ", 0, chunk_size)  # Find the last space before limit
            if split_index == -1:
                split_index = chunk_size  # If no space is found, split at exact limit
            await func(content[:split_index], kwargs)
            content = content[split_index:].lstrip()  # Remove leading spaces in the next chunk
        await func(content, **kwargs)  # Send the remaining part

    async def reply(self, content, **kwargs):
        await self.__respond(self.context.reply, content = content, **kwargs)

    async def send(self, content, **kwargs):
        await self.__respond(self.context.send, content = content, **kwargs)
        

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass
