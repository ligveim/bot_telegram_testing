import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import config


class MemoryManager:
    """Manages bot memory, logs, and participant information"""

    def __init__(self):
        self._ensure_memory_files()

    def _ensure_memory_files(self):
        """Create memory directory and files if they don't exist"""
        os.makedirs(config.MEMORY_DIR, exist_ok=True)

        if not os.path.exists(config.LOGS_FILE):
            with open(config.LOGS_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f)

        if not os.path.exists(config.PARTICIPANTS_FILE):
            with open(config.PARTICIPANTS_FILE, 'w', encoding='utf-8') as f:
                json.dump({"participants": {}}, f)

        if not os.path.exists(config.LAST_POST_FILE):
            with open(config.LAST_POST_FILE, 'w', encoding='utf-8') as f:
                json.dump({"last_post_date": None, "scheduled_time": None}, f)

        if not os.path.exists(config.SYSTEM_PROMPT_FILE):
            with open(config.SYSTEM_PROMPT_FILE, 'w', encoding='utf-8') as f:
                f.write("System prompt not configured.")

    def get_system_prompt(self) -> str:
        """Read the system prompt"""
        with open(config.SYSTEM_PROMPT_FILE, 'r', encoding='utf-8') as f:
            return f.read()

    def add_log(self, user_id: int, username: str, message: str, is_bot: bool = False):
        """Add a message to logs"""
        logs = self._read_logs()

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "username": username,
            "message": message,
            "is_bot": is_bot
        }

        logs.append(log_entry)

        # Keep only last N messages
        if len(logs) > config.MAX_LOG_MESSAGES:
            logs = logs[-config.MAX_LOG_MESSAGES:]

        with open(config.LOGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)

    def get_recent_logs(self, limit: Optional[int] = None) -> List[Dict]:
        """Get recent log messages"""
        logs = self._read_logs()

        if limit:
            return logs[-limit:]
        return logs

    def _read_logs(self) -> List[Dict]:
        """Read logs from file"""
        try:
            with open(config.LOGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def update_participant(self, user_id: int, username: str, role: Optional[str] = None):
        """Update or add participant information"""
        participants_data = self._read_participants()

        user_key = str(user_id)
        if user_key not in participants_data["participants"]:
            participants_data["participants"][user_key] = {
                "username": username,
                "first_seen": datetime.now().isoformat(),
                "role": role or "member",
                "message_count": 0
            }

        participants_data["participants"][user_key]["username"] = username
        participants_data["participants"][user_key]["message_count"] += 1
        participants_data["participants"][user_key]["last_seen"] = datetime.now().isoformat()

        if role:
            participants_data["participants"][user_key]["role"] = role

        with open(config.PARTICIPANTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(participants_data, f, ensure_ascii=False, indent=2)

    def get_participants(self) -> Dict:
        """Get all participants information"""
        return self._read_participants()["participants"]

    def _read_participants(self) -> Dict:
        """Read participants from file"""
        try:
            with open(config.PARTICIPANTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"participants": {}}

    def get_last_post_info(self) -> Dict:
        """Get information about last daily post"""
        try:
            with open(config.LAST_POST_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"last_post_date": None, "scheduled_time": None}

    def update_last_post(self, scheduled_time: Optional[str] = None):
        """Update last post timestamp"""
        data = {
            "last_post_date": datetime.now().date().isoformat(),
            "scheduled_time": scheduled_time
        }

        with open(config.LAST_POST_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def format_logs_for_context(self, limit: int = None) -> str:
        """Format recent logs as context for Claude"""
        logs = self.get_recent_logs(limit or config.MAX_CONTEXT_MESSAGES)

        if not logs:
            return "Нет предыдущих сообщений в логах."

        formatted = "## Недавние сообщения в чате:\n\n"
        for log in logs:
            timestamp = datetime.fromisoformat(log["timestamp"]).strftime("%H:%M")
            sender = "Бот" if log["is_bot"] else log["username"]
            formatted += f"[{timestamp}] {sender}: {log['message']}\n"

        return formatted

    def format_participants_for_context(self) -> str:
        """Format participants info for Claude"""
        participants = self.get_participants()

        if not participants:
            return "Нет информации об участниках."

        formatted = "## Участники чата:\n\n"
        for user_id, info in participants.items():
            formatted += f"- {info['username']}: {info.get('role', 'member')} "
            formatted += f"(сообщений: {info.get('message_count', 0)})\n"

        return formatted
