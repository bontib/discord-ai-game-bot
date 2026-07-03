import asyncio

import discord
from discord.ext import commands

from src.ai.pipeline import VoicePipeline
from src.bot.sink import StreamingSink


def create_bot() -> commands.Bot:
    intents = discord.Intents.default()
    intents.message_content = True
    intents.voice_states = True

    bot = commands.Bot(intents=intents)
    pipelines: dict[int, VoicePipeline] = {}

    @bot.event
    async def on_ready():
        print(f"Logged in as {bot.user} (ID: {bot.user.id})")

    @bot.event
    async def on_message(message: discord.Message):
        if message.author.bot:
            return

        if bot.user in message.mentions:
            await handle_tagged_message(message)

        await bot.process_commands(message)

    @bot.slash_command(name="listen", description="Join your voice channel and start listening for voice commands")
    async def listen(ctx: discord.ApplicationContext):
        if ctx.author.voice is None:
            await ctx.respond("You need to be in a voice channel first.")
            return

        if ctx.guild.id in pipelines:
            await ctx.respond("Already listening in this server.")
            return

        await ctx.defer()

        vc = await ctx.author.voice.channel.connect()
        pipeline = VoicePipeline(guild=ctx.guild, text_channel=ctx.channel)
        pipeline.start()
        pipelines[ctx.guild.id] = pipeline

        sink = StreamingSink(asyncio.get_running_loop(), pipeline.queue)
        sink.vc = vc
        vc.start_recording(sink, on_recording_error)
        await ctx.respond("Listening for voice commands.")

    @bot.slash_command(name="stop", description="Stop listening and leave the voice channel")
    async def stop(ctx: discord.ApplicationContext):
        vc = ctx.voice_client
        if vc is None:
            await ctx.respond("I'm not in a voice channel.")
            return

        if vc.is_recording():
            vc.stop_recording()

        pipeline = pipelines.pop(ctx.guild.id, None)
        if pipeline is not None:
            await pipeline.stop()

        await vc.disconnect()
        await ctx.respond("Stopped listening.")

    return bot


async def handle_tagged_message(message: discord.Message) -> None:
    # TODO: hand off to AI/NLU pipeline
    pass


def on_recording_error(exc: Exception | None) -> None:
    # Called by the voice reader thread; must not touch asyncio state.
    if exc is not None:
        print(f"Voice recording stopped with error: {exc}")
