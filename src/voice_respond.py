from pypdf import PdfReader
import edge_tts
import asyncio
import re
import discord
from pydub import AudioSegment

from globals import trans_lock, transcription
from options import options
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

voice_changes = {
    "<chad>": "us_male_sigma",
    "<usfemale>": "us_female",
    "<aufemale>": "au_female",
    "<usmale>": "us_male",
    "<aumale>": "au_male"
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

Along with these you have access to the following voices:
- <chad>
- <usfemale>
- <aufemale>
- <usmale>
- <aumale>

Here's a description:
- Your default voice he sounds sexy and elegant and like a drill sargent
- Average american female
- Average australian female
- Average american male
- Average australian male
"""

class Voice:
    def __init__(self, message_history = [], current_options = options):
        message_history.append({"role": "system", "content": sound_effect_description})
        self.text = Text(message_history = message_history, current_options = options)

    async def __text_to_audio(contents, guild_id):
        parts = re.split(r"(<.*?>)", message)  # Split text while keeping tags
        final_audio = AudioSegment.silent(duration=0)  # Start with silence
        
        tts_file_mp3 = f"tts_output_{guild_id}.mp3"
        tts_file_wav = f"tts_output_{guild_id}.wav"
        final_output = f"final_output_{guild_id}.wav"

        current_voice = default_voice
        
        for part in parts:
            if part in sound_effects:
                # Add sound effect at the correct position
                file_path = f"./sounds/{sound_effects[part]['name']}.{sound_effects[part]['type']}"
                effect_audio = AudioSegment.from_file(file_path, format=sound_effects[part]['type'])
                final_audio += effect_audio + AudioSegment.silent(duration=300)  # Small gap after SFX
            elif part in voice_changes:
                current_voice = voices[voice_changes[part]]
            elif part.strip():  
                # Generate TTS for spoken text
                communicate = edge_tts.Communicate(part, current_voice, rate="+0%")
                await communicate.save(tts_file_mp3)  # Edge TTS outputs MP3

                # Convert MP3 to WAV
                tts_audio = AudioSegment.from_file(tts_file_mp3, format="mp3")
                tts_audio.export(tts_file_wav, format="wav")

                # Append spoken text to final audio
                final_audio += AudioSegment.from_file(tts_file_wav, format="wav")

        # Save the final combined audio
        final_audio.export(final_output, format="wav")

    async def play_audio(voice_client, name):
        while not voice_client.is_connected():
            await asyncio.sleep(0.1)
        
        voice_client.play(discord.FFmpegPCMAudio(name))
        await asyncio.sleep(1)

        while voice_client.is_playing():
            await asyncio.sleep(0.1)
        await voice_client.disconnect()

    async def reply_to_context(self, context, dry_run_message = "This is a dry run message."):
        if not context.author.voice and not context.author.voice.channel:
            return
        async with context.channel.typing():
            reply = self.text.get_response()
            self.__text_to_audio(reply, context.guild.id)
            
            if context.author.voice and context.author.voice.channel:
                voice_client = await context.author.voice.channel.connect()
                self.play_audio(f"final_output_{context.guild.id}.wav")
            else:
                context.reply("It seems like you're not in a vc anymore, how shameful of you!")
                with Longmessage(context) as context:
                    context.reply(reply)
