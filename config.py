import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
TARGET_CHAT_ID = os.getenv('TARGET_CHAT_ID', '')

# Timezone and posting schedule
TIMEZONE = os.getenv('TIMEZONE', 'Europe/Moscow')
POST_TIME_START = os.getenv('POST_TIME_START', '16:00')
POST_TIME_END = os.getenv('POST_TIME_END', '23:50')

# Claude Model
CLAUDE_MODEL = 'claude-sonnet-4-5-20250929'

# File paths
MEMORY_DIR = 'memory'
LOGS_FILE = os.path.join(MEMORY_DIR, 'logs.json')
PARTICIPANTS_FILE = os.path.join(MEMORY_DIR, 'participants.json')
SYSTEM_PROMPT_FILE = os.path.join(MEMORY_DIR, 'system_prompt.txt')
LAST_POST_FILE = os.path.join(MEMORY_DIR, 'last_post.json')

# Bot settings
MAX_LOG_MESSAGES = 100  # Maximum number of messages to keep in logs
MAX_CONTEXT_MESSAGES = 20  # Maximum messages to send to Claude for context
