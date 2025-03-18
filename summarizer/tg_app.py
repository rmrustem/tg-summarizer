import datetime

from google import genai
from telegram import Bot, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackContext,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from summarizer import db
from summarizer.config import settings
from summarizer.models import Base, Message


client = genai.Client(api_key=settings.gemini_key)


def clamp(num: int, smallest: int = 1, greatest: int = 48) -> int:
    return max(smallest, min(num, greatest))


def hours_rus(num: int) -> str:
    last_two = num % 100
    tens = last_two // 10
    if tens == 1:
        return f"{num} часов"
    ones = last_two % 10
    if ones == 1:
        return f"{num} час"
    if 2 <= ones <= 4:
        return f"{num} часа"
    return f"{num} часов"


async def save_text(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id not in settings.chats_whitelist:
        return
    if update.message.from_user.is_bot:
        return

    msg = Message(
        chat_id=chat_id,
        message_id=update.message.message_id,
        user=update.message.from_user.first_name,
        text=update.message.text,
        created=update.message.date,
    )
    with db.Session() as session:
        session.add(msg)
        session.commit()


async def get_messages(chat_id: int, hours: int) -> list[Message]:
    since = datetime.datetime.utcnow() - datetime.timedelta(hours=hours)
    with db.Session() as session:
        return (
            session.query(Message)
            .filter(Message.chat_id == chat_id)
            .filter(Message.created > since)
            .all()
        )


async def summarize(messages: list[Message], chat_id: int) -> str:
    if not messages:
        return ""

    model = "gemini-2.0-flash"

    text = "\n".join(
        [f"{msg.message_id} {msg.user}: {msg.text}" for msg in messages if msg.text]
    )
    prompt = f"""Напиши краткое резюме (без вводной части) этих сообщений из Telegram чата (номер чата "{chat_id}") в виде связанного текста вида "Обсудили это, узнали новость такую-то, Вася рассказал то-то". Ключевые слова сообщений должны быть оформлены как ссылки (в формате html) на сообщения. Сообщения на одну тему должны быть сгруппированы, независимо от порядка их обсуждения. В самом начале вставь 2 emoji в тему сообщений. Текст сообщений: \n\n"""  # pylint:disable=line-too-long
    response = client.models.generate_content(model=model, contents=prompt + text)
    return str(response.text)


async def daily_summary(_: CallbackContext) -> None:
    for chat_id in settings.chats_whitelist:
        await collect_post_summary(chat_id, settings.summary_period)


async def post_summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    hours = int(context.args[0]) if context.args else settings.summary_period
    await collect_post_summary(chat_id, hours)


async def collect_post_summary(chat_id: int, hours: int) -> None:
    hours = clamp(hours)
    messages = await get_messages(chat_id, hours)
    intro = f"⚡️<b>#Дайджест за последние {hours_rus(hours)}</b> 🗞\n"
    summary = await summarize(messages, chat_id)
    bot = Bot(token=settings.tg_bot_key)
    await bot.send_message(chat_id=chat_id, text=intro + summary, parse_mode="HTML")


def start() -> None:
    Base.metadata.create_all(bind=db.engine)
    app = ApplicationBuilder().token(settings.tg_bot_key).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), save_text))
    app.add_handler(CommandHandler("summary", post_summary))
    app.job_queue.run_daily(daily_summary, datetime.time(hour=settings.daily_hour))
    app.run_polling()
