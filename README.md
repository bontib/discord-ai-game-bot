# Project Bernard

[![CI](https://github.com/bontib/discord-ai-game-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/bontib/discord-ai-game-bot/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A self-hosted Discord bot that listens to your voice channel, wakes up when you say its name, and answers questions about the games you play — player stats for titles like R6 or COD, wiki lookups for games like Subnautica 2 or Anno 117. Everything runs locally: speech-to-text, wake-word matching, and (soon) the language model itself.

> [!NOTE]
> Project Bernard is under active development. The voice pipeline (listening, transcription, wake-name detection) is working; the game-stats and wiki tools, and the LLM agent that ties it all together, are still being built.

## Features

- **Voice-activated** — join a voice channel with `/listen` and just say the bot's name to get its attention, no push-to-talk or slash command needed mid-conversation.
- **Local speech-to-text** — transcription runs on your own machine via [faster-whisper](https://github.com/SYSTRAN/faster-whisper), multilingual, CPU or GPU.
- **Fuzzy wake-word matching** — recognizes the bot's name even through STT noise or accented pronunciation (e.g. "Bernhard", "bernárd") using [rapidfuzz](https://github.com/rapidfuzz/RapidFuzz).
- **Text mentions** — tag the bot in a text channel to ask it something directly.
- **Game tools** *(planned)* — player stats (R6, COD) and wiki search (Subnautica 2, Anno 117) as callable tools for the agent.

## How it works

```
voice packets ──> per-speaker buffer ──> silence-gap segmentation ──> faster-whisper
                                                                            │
                                                                            v
                                                         wake-name fuzzy match (rapidfuzz)
                                                                            │
                                                              matched? ──> agent callback ──> reply in text channel
```

Discord only sends audio packets while a user is actively speaking, so a gap in packets is used as the utterance boundary — no separate voice-activity detector is needed. Once an utterance is transcribed, its text is fuzzy-matched against the configured bot name; a match opens a short attention window during which the next utterance from that speaker is treated as a prompt and handed to the agent.

## Getting started

### Prerequisites

- Python 3.12+
- A [Discord application](https://discord.com/developers/applications) with a bot user
  - **Message Content Intent** and **voice permissions** enabled for the bot

### Installation

```bash
git clone https://github.com/bontib/discord-ai-game-bot.git
cd discord-ai-game-bot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
DISCORD_TOKEN=your-bot-token
BOT_NAME=Bernard
```

<details>
<summary>Optional speech-to-text and wake-detection settings</summary>

| Variable | Default | Description |
|---|---|---|
| `WHISPER_MODEL` | `large-v3-turbo` | faster-whisper model size; use `small` on weaker CPUs |
| `WHISPER_DEVICE` | `auto` | `cpu`, `cuda`, or `auto` |
| `WHISPER_COMPUTE_TYPE` | `int8` | faster-whisper compute type |
| `WHISPER_CPU_THREADS` | `4` | Threads used when running on CPU |
| `WHISPER_LANGUAGE` | *(auto-detect)* | Force a transcription language |
| `WAKE_FUZZ_THRESHOLD` | `80` | Minimum fuzzy-match score (0–100) to trigger the wake name |
| `SILENCE_TIMEOUT_MS` | `700` | Silence gap that ends an utterance |
| `ATTENTION_WINDOW_S` | `8` | How long the bot keeps listening after being addressed |
| `MAX_UTTERANCE_S` | `30` | Hard cap on a single utterance's length |
| `MIN_UTTERANCE_MS` | `300` | Utterances shorter than this are discarded as noise |

> [!TIP]
> The whisper model is downloaded automatically on first use into `./models`, so the first `/listen` will take longer than the rest.

</details>

### Running

```bash
python main.py
```

Then, in your Discord server:

| Command | Description |
|---|---|
| `/listen` | Joins your current voice channel and starts listening for the wake name |
| `/stop` | Stops listening and leaves the voice channel |

## Project structure

```
discord-ai-game-bot/
├── main.py              # Entry point
├── settings.py          # Environment-based configuration
├── src/
│   ├── bot/             # Discord client, slash commands, voice sink
│   ├── ai/              # Voice pipeline, transcriber, wake-word matching, agent handoff
│   └── tools/
│       ├── wiki/        # Game wiki lookups (planned)
│       └── stats/       # Player stat lookups (planned)
├── tests/                # pytest suite
└── models/               # Downloaded whisper models (not tracked by git)
```

## Testing

```bash
ruff check .
pytest tests/ -v
```
