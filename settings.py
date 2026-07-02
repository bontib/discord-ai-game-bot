import os
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
BOT_NAME = os.getenv("BOT_NAME", "Bernard")