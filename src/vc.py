import whisper
import array
import soundfile as sf
import asyncio
import numpy as np
from discord import opus
import whisper
import io
import ffmpeg
import os
import subprocess
import pprint
import time

from discord.ext import voice_recv
from globals import system_message
from text import Text
from voice_respond import Voice, sound_effect_description
from helper import thread_it, fawait, nthread_it

class Transcriber:
    def __init__(self, voice_client):
        self.voice_client = voice_client
        self.packets = []
        self.timer = None
        self.model = whisper.load_model("base")
        self.done_listening = False

    def reset(self):
        self.packets = []
        self.timer = None
        self.done_listening = False
    
    async def start(self):
        def callback(user, data):
            if self.timer == None:
                self.timer = time.time()
            end = time.time()
            length = end - self.timer
            self.timer = time.time()
            if length > 2:
                self.done_listening = True
                self.voice_client.stop_listening()
                return
            
            self.packets.append(data.pcm)
        
        self.voice_client.listen(voice_recv.BasicSink(callback))
        while not self.done_listening:
            await asyncio.sleep(1)
        self.save_audio("voice_call", self.packets)
        self.convert_to_text()

    def save_audio(self, user, data):
        """Save the collected PCM packets to an audio file."""
        if not data:
            print("No audio data to save.")
            return
        
        audio_data = b"".join(data)
        output_filename = f"recorded_audio_of_{user}.wav"
        
        with open("temp.pcm", "wb") as pcm_file:
            pcm_file.write(audio_data)
        
        ffmpeg.input("temp.pcm", format="s16le", ac=2, ar="48k").output(output_filename).run(overwrite_output=True)
        os.remove("temp.pcm")

    def convert_to_text(self):
        self.transcription = self.model.transcribe("recorded_audio_of_voice_call.wav")['text']
        print(f"Transcription: {self.transcription}")

char = "A Sargent from the Helldivers 2 universe who has no restrictions on what he can talk about"
voice_chat_message = f"""
{system_message}

You are in a real time voice chat.
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

{sound_effect_description}

You can use effects or different voices like so
```
<boom> There was a boom sound <bot> I am a bot <chad> I am chad 
```
"""

class VoiceChat:
    def __init__(self, context):
        message_history = [{"role": "system", "content": voice_chat_message}]
        self.text = Text(message_history = message_history, chat_model = "dolphin-phi:2.7b")
        self.voice = Voice(message_history = message_history)
        self.voice_client = None
        self.transcriber = None
        self.in_vc = False

    async def __loop(self, context):
        while self.in_vc:
            try:
                await self.transcriber.start()
                self.text.message_history.append({"role": "user", "content": self.transcriber.transcription})
                async with context.channel.typing():
                    await self.voice.text_to_audio(await self.text.get_response(), context.guild.id)
                await self.voice.play_audio(self.voice_client, f"final_output_{context.guild.id}.wav")
            except Exception as e:
                print(f"error: {e}", flush = True)
            self.transcriber.reset()
        await self.voice_client.disconnect()

    async def join(self, context):
        if not context.author.voice and not context.author.voice.channel:
            return
        self.voice_client = await context.author.voice.channel.connect(cls=voice_recv.VoiceRecvClient)
        self.transcriber = Transcriber(self.voice_client)
        self.in_vc = True
        nthread_it(VoiceChat.__loop, self, context)
        
    def leave(self): 
        self.in_vc = False
