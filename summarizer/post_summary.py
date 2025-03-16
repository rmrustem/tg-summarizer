import asyncio
import sys

import telegram
from google import genai

from summarizer.config import settings
from summarizer.tg_app import get_messages, summarize

client = genai.Client(api_key=settings.gemini_key)


async def main() -> None:
    chat_id = int(sys.argv[1])
    bot = telegram.Bot(token=settings.tg_bot_key)
    messages = await get_messages(chat_id)
    summary = await summarize(messages, chat_id)
    intro = "⚡️<b>Дайджест за последние 24 часа</b> 🗞\n"
    await bot.send_message(chat_id=chat_id, text=intro + summary, parse_mode="HTML")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Specify chat_id to post summary!")

    asyncio.run(main())
