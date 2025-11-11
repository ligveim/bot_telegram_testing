import asyncio
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
import config
from memory_manager import MemoryManager
from claude_handler import ClaudeHandler
from scheduler import PostScheduler

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class TelegramBot:
    """Main Telegram bot class"""

    def __init__(self):
        self.memory = MemoryManager()
        self.claude = ClaudeHandler(self.memory)
        self.scheduler = PostScheduler(self.memory)
        self.app = None
        self.bot_username = None

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        await update.message.reply_text(
            "Привет! Я бот на базе Claude Sonnet 4.5.\n\n"
            "Я автоматически постю новости раз в день и отвечаю когда меня упоминают.\n\n"
            "Команды:\n"
            "/start - это сообщение\n"
            "/status - статус бота\n"
            "/next_post - когда следующий пост"
        )

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        last_post_info = self.memory.get_last_post_info()
        participants_count = len(self.memory.get_participants())
        logs_count = len(self.memory.get_recent_logs())

        status_msg = (
            f"🤖 Статус бота:\n\n"
            f"Модель: {config.CLAUDE_MODEL}\n"
            f"Участников в памяти: {participants_count}\n"
            f"Сообщений в логах: {logs_count}\n"
            f"Последний пост: {last_post_info.get('last_post_date', 'никогда')}\n"
        )

        if self.scheduler.should_post_today():
            time_until = self.scheduler.get_time_until_post()
            if time_until.total_seconds() > 0:
                hours = int(time_until.total_seconds() // 3600)
                minutes = int((time_until.total_seconds() % 3600) // 60)
                status_msg += f"Следующий пост через: {hours}ч {minutes}м\n"
            else:
                status_msg += "Следующий пост: скоро!\n"
        else:
            status_msg += "Пост на сегодня уже опубликован\n"

        await update.message.reply_text(status_msg)

    async def next_post_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /next_post command"""
        if not self.scheduler.should_post_today():
            await update.message.reply_text("Пост на сегодня уже был!")
            return

        scheduled_time = self.scheduler.get_scheduled_time()
        time_until = self.scheduler.get_time_until_post()

        if time_until.total_seconds() > 0:
            hours = int(time_until.total_seconds() // 3600)
            minutes = int((time_until.total_seconds() % 3600) // 60)
            await update.message.reply_text(
                f"📅 Следующий пост запланирован на {scheduled_time.strftime('%H:%M')} MSK\n"
                f"Осталось: {hours}ч {minutes}м"
            )
        else:
            await update.message.reply_text("Пост должен быть со минуты на минуту!")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages"""
        message = update.message

        if not message or not message.text:
            return

        # Get user info
        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.first_name or "Unknown"

        # Log the message
        self.memory.add_log(user_id, username, message.text, is_bot=False)
        self.memory.update_participant(user_id, username)

        # Check if bot is mentioned
        bot_mentioned = False

        # Check for @bot_username mention
        if self.bot_username and f"@{self.bot_username}" in message.text.lower():
            bot_mentioned = True

        # Check for reply to bot
        if message.reply_to_message and message.reply_to_message.from_user.is_bot:
            bot_mentioned = True

        # Check for keywords that might be directed at bot
        bot_keywords = ["бот", "клод", "claude"]
        if any(keyword in message.text.lower() for keyword in bot_keywords):
            bot_mentioned = True

        # If bot is mentioned, generate a response
        if bot_mentioned:
            logger.info(f"Bot mentioned by {username}: {message.text}")

            # Show typing indicator
            await context.bot.send_chat_action(
                chat_id=message.chat_id,
                action="typing"
            )

            # Generate response using Claude
            response = await self.claude.generate_response(
                user_message=message.text,
                include_context=True
            )

            # Send response
            sent_message = await message.reply_text(response)

            # Log bot's response
            self.memory.add_log(
                user_id=context.bot.id,
                username=self.bot_username or "bot",
                message=response,
                is_bot=True
            )

    async def post_daily_news(self, context: ContextTypes.DEFAULT_TYPE):
        """Post daily news to the target chat"""
        if not config.TARGET_CHAT_ID:
            logger.warning("TARGET_CHAT_ID not configured, skipping daily post")
            return

        logger.info("Generating daily news post...")

        try:
            # Generate news using Claude
            news_post = await self.claude.generate_daily_news()

            # Send to target chat
            await context.bot.send_message(
                chat_id=config.TARGET_CHAT_ID,
                text=news_post,
                disable_web_page_preview=False
            )

            # Log the post
            self.memory.add_log(
                user_id=context.bot.id,
                username=self.bot_username or "bot",
                message=news_post,
                is_bot=True
            )

            # Mark post as completed
            self.scheduler.mark_post_completed()

            logger.info("Daily news posted successfully!")

        except Exception as e:
            logger.error(f"Error posting daily news: {e}")

    async def check_and_post_news(self, context: ContextTypes.DEFAULT_TYPE):
        """Job that checks if it's time to post news"""
        if self.scheduler.is_time_to_post():
            await self.post_daily_news(context)

    async def post_error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Log errors"""
        logger.error(f"Exception while handling an update: {context.error}")

    async def initialize_bot(self):
        """Initialize the bot and get bot info"""
        bot = self.app.bot
        bot_info = await bot.get_me()
        self.bot_username = bot_info.username
        logger.info(f"Bot initialized: @{self.bot_username}")

    def run(self):
        """Run the bot"""
        print("🤖 Инициализация бота...")

        # Create application
        self.app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

        # Register handlers
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        self.app.add_handler(CommandHandler("next_post", self.next_post_command))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        # Register error handler
        self.app.add_error_handler(self.post_error_handler)

        # Schedule daily news check (every 5 minutes)
        self.app.job_queue.run_repeating(
            self.check_and_post_news,
            interval=300,  # 5 minutes
            first=10  # First check after 10 seconds
        )

        print("✅ Бот запущен!")
        print(f"📊 Модель: {config.CLAUDE_MODEL}")

        # Check if we should post today
        if self.scheduler.should_post_today():
            scheduled_time = self.scheduler.get_scheduled_time()
            print(f"📅 Пост запланирован на {scheduled_time.strftime('%H:%M')} MSK")
        else:
            print("✅ Пост на сегодня уже был")

        if not config.TARGET_CHAT_ID:
            print("⚠️  TARGET_CHAT_ID не настроен в .env!")

        print("\n🚀 Бот работает. Нажми Ctrl+C для остановки.\n")

        # Run the bot with initialization
        self.app.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )


if __name__ == "__main__":
    bot = TelegramBot()
    bot.run()
