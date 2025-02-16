import discord
import ollama
import re
import pprint
import threading
import asyncio
import random

from options import options
from helper import fawait, thread_it, LongMessage

class Text:
    def __init__(self, chat_model = "deepseek-r1:8b", message_history = [], message_history_rollover = 20, current_options = options):
        self.chat_model = chat_model
        self.options = current_options
        self.message_history = message_history
        self.message_history_rollover = message_history_rollover

    # Generic method to chat with any method and get their result
    def model_chat(self, result_queue):
        try:
            # Generates the response
            response = ollama.chat(model=self.chat_model, messages=self.message_history)

            # Gets the response
            reply = response["message"]["content"]
            reply = re.sub(r"<think>.*?</think>", "", reply, flags=re.IGNORECASE | re.DOTALL) # removes garbage think stuff

            fawait(result_queue.put(reply)) # return the result
        except Exception as e:
            fawait(result_queue.put(str(e)))

    async def get_response(self):
        reply = await thread_it(Text.model_chat, self)
        return reply

    # A function to reply to a given Discord.py Context
    async def reply_to_context(self, context, dry_run_message = "This is a dry run message"):
        if not self.options.dry_run:
            async with context.channel.typing():
                reply = await self.get_response()

                with LongMessage(context) as context:
                    await context.reply(reply)
        else:
            with LongMessage(context) as context:
                await context.reply(dry_run_message)
