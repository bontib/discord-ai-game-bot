from settings import DISCORD_TOKEN
from src.bot.client import create_bot


def main():
    bot = create_bot()
    bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()
