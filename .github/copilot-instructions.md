# Copilot Instructions

## Project Overview
This is a self-hosted Discord AI game bot written in Python. It uses a local Whisper model for speech-to-text and a local LLM for natural language understanding. The bot is able to answer game-related questions by querying game wikis and player stat APIs.

## Repository Structure
```
discord-ai-game-bot/
├── main.py              # Entry point
├── requirements.txt     # Python dependencies
├── src/
│   ├── bot/             # Discord bot event handlers and commands
│   ├── ai/              # Whisper and LLM model wrappers
│   ├── tools/
│   │   ├── wiki/        # Tools for searching game wikis (e.g. Subnautica, Anno)
│   │   └── stats/       # Tools for fetching player stats (e.g. R6, COD)
│   └── config/          # Configuration loading and validation
├── tests/               # Unit and integration tests (pytest)
├── docs/                # Project documentation
├── models/              # Local AI model files (not tracked by git)
└── data/                # Static data and assets
```

## Coding Conventions
- Use Python 3.12+.
- Format and lint with **ruff**.
- Write tests with **pytest** and place them in the `tests/` directory.
- Use `async`/`await` throughout (discord.py is async).
- Keep AI model loading in `src/ai/`, game-data queries in `src/tools/`.
- Store secrets (tokens, API keys) in a `.env` file — never commit them.
- Use `python-dotenv` to load environment variables.

## Key Technologies
| Purpose | Library |
|---|---|
| Discord integration | `py-cord` |
| Speech-to-text | `openai-whisper` (local) |
| LLM inference | `llama-cpp-python` (local GGUF models) |
| HTTP requests | `aiohttp` / `requests` |
| Config / secrets | `python-dotenv` |
| Testing | `pytest` |
| Linting | `ruff` |

## Bot Capabilities
- Respond to text and voice messages in Discord.
- Search game wikis (Subnautica 2, Anno 117, …).
- Look up player stats from game APIs (Rainbow Six Siege, Call of Duty, …).
- All AI inference runs **locally** — no external AI API calls.

## Guidelines for Contributions
- Keep modules small and focused on a single responsibility.
- Add type hints to all public functions.
- Document all public functions and classes with docstrings.
- Every new tool in `src/tools/` should implement a common interface so the LLM can discover and call it uniformly.
- Run `ruff check .` and `pytest tests/` before opening a pull request.
