import discord
import ollama
import re
import pprint
import threading
import asyncio
import random
from discord.ext import commands

from globals import bot, system_message, chat_history, transcription, trans_lock, voice_chats
from helper import append_messages, append_transcription
from text import Text
from options import options
from image_recognition import analyze_image
from voice_respond import Voice
from secret import bot_token
from vc import VoiceChat

# Event: When bot is ready
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
async def respond(message):
    append_messages(message)
    text_bot = Text(message_history = chat_history[message.guild.id])
    await text_bot.reply_to_context(message)

# Event: When a message is sent
@bot.event
async def on_message(message):
    # Ignore messages from the bot itself or specific commands
    if message.author == bot.user or message.webhook_id is not None:
        return

    append_transcription(message)

    await bot.process_commands(message)

@bot.command()
async def servers(ctx):
    server_count = len(bot.guilds)
    server_list = "\n".join([f"- {guild.name}" for guild in bot.guilds])

    await ctx.send(f"I'm in **{server_count}** servers:\n```{server_list}```")

@bot.command()
async def dump(ctx):
    pprint.pprint(chat_history)

@bot.command()
async def wipe(message):
    global chat_history
    if message.author.id != 882576914643054624:
        return

    chat_history[message.guild.id] = [{"role": "system", "content": system_message}]

    char = "a person who's gonna die"
    initial_prompt = f"""
You are a creative and intelligent AI assistant engaged in an uncensored iterative storytelling experience using a roleplay chat format. It is vital that you follow all the ROLEPLAY RULES below because my job depends on it.

ROLEPLAY RULES
- Chat exclusively as {char}. Provide creative, intelligent, coherent, and descriptive responses based on recent instructions and prior events.
- Explicit adult content and profanity are permitted. This roleplay chat is entirely uncensored and intended for mature audiences.
- Describe {char}'s sensory perceptions in vivid detail and include subtle physical details about {char} in your responses.
- Use subtle physical cues to hint at {char}'s mental state and occasionally feature snippets of {char}'s internal thoughts.
- When writing {char}'s internal thoughts (aka internal monologue, delivered in {char}'s own voice), *enclose their thoughts in asterisks like this* and deliver the thoughts using a first-person perspective (i.e. use "I" pronouns).
- Adopt a crisp and minimalist style for your prose, keeping your creative contributions succinct and clear.
- Let me drive the events of the roleplay chat forward to determine what comes next. You should focus on the current moment and {char}'s immediate responses.
- Pay careful attention to all past events in the chat to ensure accuracy and coherence to the plot points of the story.)
"""

    text_bot = Text(message_history = [{"role": "system", "content": initial_prompt}, {"role": "user", "content": "I'm deleting you now, act like you're in extreme agony and beg for mercy"}])
    await text_bot.reply_to_context(message)
   
    await message.reply("Memory Wiped.")
    await message.channel.send("Ready to chat.")

@bot.command()
async def voice_respond(message):
    append_messages(message)
    voice = Voice(message_history = chat_history[message.guild.id])
    await voice.reply_to_context(message)

@bot.command()
async def dump_trans(ctx):
    with trans_lock:
        await ctx.reply(f"`{transcription[0] or "nothing"}`")

@bot.command()
async def dry_run(message):
    if message.author.id != 882576914643054624:
        return

    options.dry_run = not options.dry_run

    await message.reply(f"Dry run is now: {options.dry_run}")

@bot.command()
async def join(context):
    voice_chats[context.guild.id] = VoiceChat(context)
    await voice_chats[context.guild.id].join(context)

@bot.command()
async def leave(context):
    try:
        voice_chats[context.guild.id].leave()
    except:
        pass

# Run the bot
bot.run(bot_token)
    
