import datetime
import schedule
import threading
import time
import uuid
import asyncio

from task import Task
from task_manager import TaskManager
from tg_bot import TgBot

# ----------------------------------------------------------------------------------------------------------------------

class TaskScheduler:
    def __init__(self, bot: TgBot, task_manager: TaskManager):
        self.task_mgr = task_manager
        self.bot = bot
        self.today = datetime.date.today()

    async def start(self):
        loop = asyncio.get_running_loop()

        def worker():
            fut = asyncio.run_coroutine_threadsafe(self.__run_scheduler(), loop)
            fut.result()

        threading.Thread(target=worker, daemon=True).start()

    async def __run_voice_generator(self):
        time_list = self.task_mgr.today_tasks()
        if len(time_list) == 0:
            return

        next_reminder = time_list[0]
        target_time = next_reminder[0]
        task_id = str(next_reminder[1])

        task = self.task_mgr.get_task(task_id)
        if task is None:
            self.task_mgr.today_tasks().pop(0)
            return

        current_datetime = datetime.datetime.now()
        target_datetime = datetime.datetime.combine(datetime.date.today(), target_time)
        time_remaining = target_datetime - current_datetime

        if time_remaining < datetime.timedelta(seconds=5 * 60):
            task_list = self.task_mgr.today_tasks()
            task_list.pop(0)
            print(f"Remaining tasks for today:\n{task_list}")
            print(f"Generating voice for task:\n{task}")
            await self.bot.generate_voice(chat_id=self.bot.chat_id, task=task)

    async def __run_scheduler(self):
        while True:
            await asyncio.sleep(60)

            if datetime.date.today() > self.today:
                self.today = datetime.date.today()
                self.task_mgr.update()

            if self.bot.chat_id != 0:
                await self.__run_voice_generator()