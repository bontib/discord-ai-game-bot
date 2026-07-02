import discord
from discord.ext import commands


def create_bot() -> commands.Bot:
    intents = discord.Intents.default()
    intents.message_content = True
    intents.voice_states = True

    bot = commands.Bot(intents=intents)

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

        vc = await ctx.author.voice.channel.connect()
        vc.start_recording(discord.sinks.WaveSink(), on_recording_finished, ctx.channel)
        await ctx.respond("Listening for voice commands.")

    @bot.slash_command(name="stop", description="Stop listening and leave the voice channel")
    async def stop(ctx: discord.ApplicationContext):
        vc = ctx.voice_client
        if vc is None:
            await ctx.respond("I'm not in a voice channel.")
            return

        if vc.recording:
            vc.stop_recording()
        await vc.disconnect()
        await ctx.respond("Stopped listening.")

    return bot


async def handle_tagged_message(message: discord.Message) -> None:
    # TODO: hand off to AI/NLU pipeline
    pass


async def on_recording_finished(sink: discord.sinks.Sink, channel: discord.TextChannel) -> None:
    # TODO: hand off recorded per-user audio to Whisper/STT pipeline
    pass
