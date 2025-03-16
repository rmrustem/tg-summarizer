import datetime

from google import genai
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from summarizer import db
from summarizer.config import settings
from summarizer.models import Base, Message

client = genai.Client(api_key=settings.gemini_key)


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


async def get_messages(chat_id: int, hours: int = 24) -> list[Message]:
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
    prompt = f"""Напиши краткое резюме (без вводной части) этих сообщений из Telegram чата (номер чата "{chat_id}") в виде связанного текста вида "Обсудили это, узнали новость такую-то, Вася сделал то-то". Отдельные ключевые слова должны быть оформлены как ссылки (в формате html) на сообщения. Текст сообщений: \n\n"""  # pylint:disable=line-too-long
    response = client.models.generate_content(model=model, contents=prompt + text)
    return str(response.text)


async def post_summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    messages = await get_messages(chat_id)
    summary = await summarize(messages, chat_id)
    intro = "⚡️<b>Дайджест за последние 24 часа</b> 🗞\n"
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=intro + summary, parse_mode="HTML"
    )


def start() -> None:
    Base.metadata.create_all(bind=db.engine)
    app = ApplicationBuilder().token(settings.tg_bot_key).build()
    save_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), save_text)
    app.add_handler(save_handler)
    app.add_handler(CommandHandler("summary", post_summary))
    app.run_polling()
