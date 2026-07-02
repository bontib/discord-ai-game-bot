import os
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
BOT_NAME = os.getenv("BOT_NAME", "Bernard")

# Speech-to-text (faster-whisper)
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "large-v3-turbo")  # weak CPU: "small"
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "auto")  # "cpu" | "cuda" | "auto"
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
WHISPER_CPU_THREADS = int(os.getenv("WHISPER_CPU_THREADS", "4"))
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE") or None  # None = auto-detect
MODELS_DIR = join(dirname(__file__), "models")

# Wake-name detection
WAKE_FUZZ_THRESHOLD = int(os.getenv("WAKE_FUZZ_THRESHOLD", "80"))
SILENCE_TIMEOUT_MS = int(os.getenv("SILENCE_TIMEOUT_MS", "700"))
ATTENTION_WINDOW_S = float(os.getenv("ATTENTION_WINDOW_S", "8"))
MAX_UTTERANCE_S = float(os.getenv("MAX_UTTERANCE_S", "30"))
MIN_UTTERANCE_MS = int(os.getenv("MIN_UTTERANCE_MS", "300"))