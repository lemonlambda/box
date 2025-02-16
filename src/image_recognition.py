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

from globals import bot, transcription, trans_lock, options
from helper import thread_it, fawait

IMAGE_FOLDER = ".\\images\\"
os.makedirs(IMAGE_FOLDER, exist_ok=True)

async def download_image(url, filename):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    # Read image data into memory
                    image_data = await resp.read()

                    # Convert image data to a PIL Image
                    image = Image.open(io.BytesIO(image_data))

                    # Ensure the image is converted to RGB (required for saving as JPEG)
                    image = image.convert("RGB")

                    # Set the output path for the JPEG file
                    file_path = os.path.join(IMAGE_FOLDER, f"{filename}.jpg")

                    # Save the image as JPEG
                    image.save(file_path, "JPEG")
                    return file_path
    except Exception as e:
        print(f"Error downloading or processing image: {e}")
    return None


def start_analyzing_image(message, result_queue):
    image_paths = []
    
    for attachment in message.attachments:
        # Only process image file types
        if any(attachment.filename.lower().endswith(ext) for ext in ["png", "jpg", "jpeg", "webp", "gif"]):
            file_path = fawait(download_image(attachment.url, attachment.filename))
            if file_path:
                image_paths.append(file_path)

    if image_paths == []:
        return

    try:
        # Send the image(s) to Ollama
        response = ollama.chat(
            model = "llava:7b",
            messages = [
                {"role": "user", "content": "describe the image", "images": image_paths}
            ]
        )

        reply = response.get("message", {}).get("content", "Sorry, I couldn't analyze the image.")
        fawait(result_queue.put(reply))

    except Exception as e:
        print(f"Error analyzing image: {e}")
        fawait(result_queue.put("Error analyzing image."))

async def analyze_image(message):
    if not message.attachments:
        return  # No image attached
    try:
        emoji_inbox = '📥'
        try:
            await message.add_reaction(emoji_inbox)     
        except:
            pass
        if not options["dry_run"]:
            reply = await thread_it(start_analyzing_image, message) 
        try:
            await message.remove_reaction(emoji_inbox, bot.user)
        except:
            pass

        emoji = discord.PartialEmoji(name='boxed', id=1338711580124250163)
        try:
            await message.add_reaction(emoji)
        except:
            pass

        with trans_lock:
            transcription[0] = transcription[0] + f"User {message.author} sent an image containing: {reply or "Couldn't Anaylze"}\n"

    except Exception as e:
        print(f"Error: {e}")
        await message.channel.send("An error occurred while processing your request.")
