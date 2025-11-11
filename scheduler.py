import random
from datetime import datetime, time, timedelta
import pytz
import config
from memory_manager import MemoryManager


class PostScheduler:
    """Manages scheduling of daily posts"""

    def __init__(self, memory_manager: MemoryManager):
        self.memory = memory_manager
        self.timezone = pytz.timezone(config.TIMEZONE)

    def should_post_today(self) -> bool:
        """
        Check if we should post today based on last post date

        Returns:
            True if we should schedule/post today
        """
        last_post_info = self.memory.get_last_post_info()
        today = datetime.now(self.timezone).date().isoformat()

        # If we haven't posted today, return True
        if last_post_info["last_post_date"] != today:
            return True

        return False

    def get_scheduled_time(self) -> datetime:
        """
        Get the scheduled posting time for today.
        If already scheduled, return that time.
        Otherwise, generate a random time between POST_TIME_START and POST_TIME_END

        Returns:
            Datetime object for scheduled post
        """
        last_post_info = self.memory.get_last_post_info()
        today = datetime.now(self.timezone).date().isoformat()

        # If we already have a scheduled time for today, use it
        if (last_post_info["last_post_date"] == today and
                last_post_info["scheduled_time"]):
            scheduled_time_str = last_post_info["scheduled_time"]
            return datetime.fromisoformat(scheduled_time_str).astimezone(self.timezone)

        # Otherwise, generate a new random time
        return self._generate_random_post_time()

    def _generate_random_post_time(self) -> datetime:
        """
        Generate a random posting time between POST_TIME_START and POST_TIME_END

        Returns:
            Datetime object for the random time today
        """
        # Parse start and end times
        start_hour, start_min = map(int, config.POST_TIME_START.split(':'))
        end_hour, end_min = map(int, config.POST_TIME_END.split(':'))

        # Create time objects
        start_time = time(start_hour, start_min)
        end_time = time(end_hour, end_min)

        # Get today's date in the configured timezone
        now = datetime.now(self.timezone)
        today = now.date()

        # Create datetime objects for start and end
        start_dt = datetime.combine(today, start_time)
        end_dt = datetime.combine(today, end_time)

        # Make them timezone-aware
        start_dt = self.timezone.localize(start_dt)
        end_dt = self.timezone.localize(end_dt)

        # Calculate random time in seconds
        time_diff = (end_dt - start_dt).total_seconds()
        random_seconds = random.randint(0, int(time_diff))

        scheduled_time = start_dt + timedelta(seconds=random_seconds)

        # Save the scheduled time
        self.memory.update_last_post(scheduled_time.isoformat())

        print(f"📅 Запланирован пост на {scheduled_time.strftime('%H:%M')} MSK")

        return scheduled_time

    def is_time_to_post(self) -> bool:
        """
        Check if it's time to post now

        Returns:
            True if current time >= scheduled time
        """
        if not self.should_post_today():
            return False

        scheduled_time = self.get_scheduled_time()
        current_time = datetime.now(self.timezone)

        return current_time >= scheduled_time

    def mark_post_completed(self):
        """Mark today's post as completed"""
        self.memory.update_last_post(None)
        print(f"✅ Пост опубликован: {datetime.now(self.timezone).strftime('%H:%M:%S')}")

    def get_time_until_post(self) -> timedelta:
        """
        Get time remaining until next scheduled post

        Returns:
            Timedelta object
        """
        scheduled_time = self.get_scheduled_time()
        current_time = datetime.now(self.timezone)

        return scheduled_time - current_time
