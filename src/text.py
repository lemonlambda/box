import discord
import ollama
import re
import pprint
import threading
import asyncio
import random

from globals import command_names, bot, system_message, transcription, trans_lock, options
from helper import fawait, thread_it, long_message#, LongMessage

chat_history = [{"role": "system", "content": system_message}]

# class Text:
#     def __init__(self, chat_model = "deepseek-r1:8b", message_history = [], message_history_rollover = 20, current_options = options):
#         self.chat_model = chat_model
#         self.options = current_options
#         self.message_history = message_history
#         self.message_history_rollover = message_history_rollover

#     # Generic method to chat with any method and get their result
#     def model_chat(self, result_queue):
#         try:
#             # Generates the response
#             response = ollama.chat(model=self.chat_model, messages=self.message_history)

#             # Gets the response
#             reply = response["message"]["content"]
#             reply = re.sub(r"<think>.*?</think>", "", reply, flags=re.IGNORECASE | re.DOTALL) # removes garbage think stuff

#             fawait(result_queue.put(reply)) # return the result
#         except Exception as e:
#             fawait(result_queue.put(str(e)))

#     # A function to reply to a given Discord.py Context
#     async def reply_to_context(self, context, dry_run_message = "This is a dry run message"):
#         if not self.options.dry_run:
#             async with context.channel.typing():
#                 reply = await thread_it(model_chat(self))

#                 with LongMessage(context) as context:
#                     await context.reply(reply)
#         else:
#             with LongMessage(context) as context:
#                 await context.reply(dry_run_message)

def deepseek_call(result_queue, message_history = None):
    try:
        # Call Ollama's chat function

        # Extract and clean up the response
        if "message" in response:
            reply = response["message"]["content"]
            reply = re.sub(r"<think>.*?</think>", "", reply, flags=re.IGNORECASE | re.DOTALL)
            chat_history.append({"role": "assistant", "content": reply})
        else:
            reply = "Sorry, I couldn't generate a response."
            chat_history.pop()  # If something goes wrong, remove the last entry

        fawait(result_queue.put(reply))
    except Exception as e:
        fawait(result_queue.put(str(e)))

async def respond_to(message):
    with trans_lock:
        chat_history.append({"role": "user", "content": transcription[0]})
        transcription[0] = ""
    if len(chat_history) >= 20:
        chat_history.pop(1)
    try:
        if not options["dry_run"]:
            async with message.channel.typing():
                reply = await thread_it(deepseek_call) 

            # Send the response to the channel
            await long_message(message.reply, reply)

    except Exception as e:
        print(f"Error: {e}")
        await message.channel.send("An error occurred while processing your request.")

async def create_response(message, force = False):
    if message.content not in command_names:
        with trans_lock:
            transcription[0] = transcription[0] + f"User {message.author.global_name} says: {message.content}\n"

    if random.randint(0, 100) == 1 or force:
        await respond_to(message)
