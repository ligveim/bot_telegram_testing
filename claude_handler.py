import anthropic
import config
from memory_manager import MemoryManager


class ClaudeHandler:
    """Handles interactions with Claude API"""

    def __init__(self, memory_manager: MemoryManager):
        self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        self.memory = memory_manager

    async def generate_response(self, user_message: str, include_context: bool = True) -> str:
        """
        Generate a response using Claude

        Args:
            user_message: The user's message to respond to
            include_context: Whether to include chat logs and participants in context

        Returns:
            Claude's response
        """
        # Build the system prompt
        system_prompt = self.memory.get_system_prompt()

        if include_context:
            system_prompt += "\n\n" + self.memory.format_logs_for_context()
            system_prompt += "\n\n" + self.memory.format_participants_for_context()

        # Call Claude API
        try:
            message = self.client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=1024,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )

            return message.content[0].text

        except Exception as e:
            print(f"Error calling Claude API: {e}")
            return f"Ошибка при обращении к Claude: {str(e)}"

    async def generate_daily_news(self) -> str:
        """
        Generate a daily news post

        Returns:
            A formatted news post
        """
        system_prompt = self.memory.get_system_prompt()
        system_prompt += "\n\n" + self.memory.format_participants_for_context()
        system_prompt += "\n\nТакже вот последние новости, которые ты постил (чтобы не повторяться):\n"
        system_prompt += self.memory.format_logs_for_context(limit=5)

        user_prompt = """Создай один ежедневный пост с интересной новостью про AI, технологии, e/acc или сингулярность.

ВАЖНО:
- Новость должна быть реальной и актуальной
- Используй формат из системного промпта
- Добавь ироничный комментарий с отсылкой к участникам чата (если уместно)
- Будь краток и остроумен

Если не можешь найти хорошую новость, напиши: "не было хорошей новости сегодня" и добавь ироничный комментарий."""

        try:
            message = self.client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=500,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            return message.content[0].text

        except Exception as e:
            print(f"Error generating daily news: {e}")
            return "не было хорошей новости сегодня (и я сломался пытаясь её найти)"

    async def fact_check(self, claim: str) -> str:
        """
        Fact-check a claim or news article

        Args:
            claim: The claim or news to fact-check

        Returns:
            Fact-check result
        """
        system_prompt = self.memory.get_system_prompt()
        system_prompt += "\n\nТебя попросили проверить факты. Будь объективным, но сохраняй стиль общения чата."

        user_prompt = f"Проверь эту информацию и дай свой комментарий:\n\n{claim}"

        try:
            message = self.client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=800,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            return message.content[0].text

        except Exception as e:
            print(f"Error fact-checking: {e}")
            return f"Не смог проверить, сорян: {str(e)}"
