import os
import sqlite3
from datetime import timedelta

from telegram import ForceReply, Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from agents import Agent, Runner, SQLiteSession
from config import with_env

FIRST = timedelta(seconds=10)
INTERVAL = timedelta(minutes=5)
KEEP_LAST_N = 10
DB_PATH = "bot.sql"


async def prune_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Keep only the last `keep_n` rows in agent_messages for *each* session_id.
    Uses a single DELETE with a window function.
    """

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_messages_session_time
            ON agent_messages(session_id, created_at, id)
        """)
        conn.execute(
            """
            WITH ranked AS (
              SELECT id,
                     ROW_NUMBER() OVER (
                       PARTITION BY session_id
                       ORDER BY created_at DESC, id DESC
                     ) AS rn
              FROM agent_messages
            )
            DELETE FROM agent_messages
            WHERE id IN (SELECT id FROM ranked WHERE rn > ?);
            """,
            (KEEP_LAST_N,),
        )
        conn.execute("PRAGMA optimize")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""

    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )


async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Answer the user message."""

    chat_id = update.effective_chat.id
    session_id = f"chat_{chat_id}"
    session = SQLiteSession(session_id, "bot.sql")

    await update.message.reply_chat_action(ChatAction.TYPING)

    if "agent" not in context.chat_data:
        context.chat_data["agent"] = Agent(
            name="Assistant",
            instructions="You are a helpful assistant.",
        )
    agent = context.chat_data["agent"]

    result = await Runner.run(agent, update.message.text, session=session)
    await update.message.reply_text(result.final_output)


@with_env
def main() -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    application = Application.builder().token(token).build()

    start_handler = CommandHandler("start", start)
    answer_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, answer)

    application.add_handler(start_handler)
    application.add_handler(answer_handler)

    application.job_queue.run_repeating(
        prune_job,
        interval=INTERVAL,
        first=FIRST,
        name="prune_messages",
    )

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
