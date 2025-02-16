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

from globals import bot

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
        await func(content, kwargs)  # Send the remaining part

    async def reply(self, content = None, **kwargs):
        await self.__respond(self.context.reply, content, kwargs)

    async def send(self, content = None, **kwargs):
        await self.__respond(self.context.send, content, kwargs)
        

    def __enter__(self):
        return self

    def __exit__(self):
        pass
