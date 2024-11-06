import discord
from discord.ext import commands
import yt_dlp
import asyncio

import os
from dotenv import load_dotenv


import subprocess
import json
load_dotenv()
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.presences = True
intents.guilds = True


FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                          'options': '-vn'}
YDL_OPTIONS = {'format':'bestaudio','noplaylist':True}



class MusicBot(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.queue = []

    @commands.command()
    async def play(self, ctx, *, search):
        voice_channel = ctx.author.voice.channel if ctx.author.voice else None
        if not voice_channel:
            return await ctx.send("You are not in a voice channel!")
        if not ctx.voice_client:
            await voice_channel.connect()
        async with ctx.typing():
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(f"ytsearch:{search}", download=False)
                if 'entries' in info:
                    info= info['entries'][0]
                url = info['url']
                title = info['title']
                self.queue.append((url,title))
                await ctx.send(f"Added to queue: **{title}**")
        if not ctx.voice_client.is_playing():
            await self.play_next(ctx)

    async def get_audio_duration(url):
        try:

            command = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'json',
                url
            ]
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            info = json.loads(result.stdout)
            duration = float(info['format']['duration'])
            return duration
        except Exception as e:
            print(e)

    async def play_next(self, ctx):
        if self.queue:
            url, title = self.queue.pop(0)
            source = await discord.FFmpegOpusAudio.from_probe(url,**FFMPEG_OPTIONS)


            ctx.voice_client.play(source, after=lambda _:self.client.loop.create_task(self.play_next(ctx)))
            await ctx.send(f'Now playing: **{title}**')
        elif not ctx.voice_client.is_playing():
            await ctx.send("queue is empty")


    @commands.command()
    async def url(self,ctx,*,url):

        voice_channel = ctx.author.voice.channel if ctx.author.voice else None
        if not voice_channel:
            return await ctx.send("You are not in a voice channel!")
        if not ctx.voice_client:
            await voice_channel.connect()
        async with ctx.typing():
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(url,download=False)

                if 'entries' in info:
                    info= info['entries'][0]
                url = info['url']
                title = info['title']
                self.queue.append((url,title))
                await ctx.send(f"Added to queue: **{title}**")
        if not ctx.voice_client.is_playing():
            await self.play_next(ctx)



    @commands.command()
    async def skip(self,ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("Skipped")

    @commands.command()
    async def stop(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.voice_client.disconnect()
            await ctx.send("Stopped")
        else:
            if ctx.voice_client:
                 await ctx.voice_client.disconnect()
                 await ctx.send("Stopped")



client = commands.Bot(command_prefix='!', intents=intents)


async def main():
    print("Running")
    print(client)
    try:
        await client.add_cog(MusicBot(client))
        await client.start(os.getenv("TOKEN"))
    except Exception as e:
        print(f"An error occurred: {e}")

asyncio.run(main())


