from pypdf import PdfReader
import edge_tts
import asyncio
import re
import discord
from pydub import AudioSegment

from text import deepseek_call, chat_history
from globals import options, trans_lock, transcription
from helper import thread_it

voices = {
    "us_female": "en-US-JennyNeural",
    "au_female": "en-AU-NatashaNeural",
    "us_male": "en-US-GuyNeural",
    "us_male_sigma": "en-US-AndrewMultilingualNeural",
    "au_male": "en-AU-WilliamNeural"
}

# Default voice index
default_voice = voices["us_male_sigma"]

# Define sound effect mappings
sound_effects = {
    "<boom>": {"name": "boom", "type": "mp3"},
    "<clap>": {"name": "clap", "type": "wav"},
    "<laugh>": {"name": "laugh", "type": "wav"},
    "<bowser>": {"name": "bowser", "type": "ogg"},
    "<delivery>": {"name": "delivery", "type": "ogg"},
    "<kefkalaugh>": {"name": "kefkalaugh", "type": "ogg"},
    "<minecart>": {"name": "minecart", "type": "ogg"},
    "<wedontknow>": {"name": "wedontknow", "type": "ogg"},
    "<yesyes>": {"name": "yesyes", "type": "ogg"},
}

sound_effect_description = """
You have access to the following sound effects:
- <boom>
- <clap>
- <laugh>
- <bowser>
- <delivery>
- <kefkalaugh>
- <minecart>
- <wedontknow>
- <yesyes>

You can use them by writing them exactly as put previously.

The description of them in order is:
- Vine boom sound effect, loud and funny
- Audience clapping
- Laughing
- Evil sound for evil moments
- We've got a delivery exclaimed excitedly
- Evil laugh
- Minecart sound very annoying
- We don't know said out
- Yes yes said out
"""

async def text_to_audio(message):
    """Processes a message containing text and sound effect tags into a properly ordered audio file."""
    parts = re.split(r"(<.*?>)", message)  # Split text while keeping tags
    final_audio = AudioSegment.silent(duration=0)  # Start with silence

    for part in parts:
        if part in sound_effects:
            # Add sound effect at the correct position
            file_path = f"./sounds/{sound_effects[part]['name']}.{sound_effects[part]['type']}"
            effect_audio = AudioSegment.from_file(file_path, format=sound_effects[part]['type'])
            final_audio += effect_audio + AudioSegment.silent(duration=300)  # Small gap after SFX
        elif part.strip():  
            # Generate TTS for spoken text
            tts_file_mp3 = "tts_output.mp3"
            tts_file_wav = "tts_output.wav"

            communicate = edge_tts.Communicate(part, default_voice, rate="+0%")
            await communicate.save(tts_file_mp3)  # Edge TTS outputs MP3

            # Convert MP3 to WAV
            tts_audio = AudioSegment.from_file(tts_file_mp3, format="mp3")
            tts_audio.export(tts_file_wav, format="wav")

            # Append spoken text to final audio
            final_audio += AudioSegment.from_file(tts_file_wav, format="wav")

    # Save the final combined audio
    final_output = "final_output.wav"
    final_audio.export(final_output, format="wav")

async def respond_in_voice(message):
    with trans_lock:
        chat_history.append({"role": "user", "content": transcription[0]})
        transcription[0] = ""
    if len(chat_history) >= 20:
        chat_history.pop(1)
    try:
        voice_client = None
        if not options["dry_run"]:
            async with message.channel.typing():
                array = chat_history + [{"role": "user", "content": sound_effect_description}]
                reply = await thread_it(deepseek_call, message_history = array)
            if message.author.voice and message.author.voice.channel:
                voice_client = await message.author.voice.channel.connect()
                await text_to_audio(reply)
            else:
                await message.reply("You're not a in a voice channel sending normally..")
                await message.reply(reply)
                return

        else:
            if message.author.voice and message.author.voice.channel:
                voice_client = await message.author.voice.channel.connect()
                await text_to_audio("<boom> Hello, my friend, <clap>, <laugh>")
            else:
                await message.reply("You're not a in a voice channel sending normally..")
                await message.reply("<boom> Hello, my friend <laugh>")
                return

        while not voice_client.is_connected():
            await asyncio.sleep(1)
        
        voice_client.play(discord.FFmpegPCMAudio("final_output.wav"))
        await asyncio.sleep(1)

        while voice_client.is_playing():
            await asyncio.sleep(1)
        await voice_client.disconnect()

    except Exception as e:
        print(f"Error: {e}")
        await message.channel.send("An error occurred while processing your request.")
    
