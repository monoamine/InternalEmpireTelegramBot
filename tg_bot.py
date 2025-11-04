from task import Task
from util import Environment
from voice import VoiceGenerator

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import FSInputFile

import aiogram_dialog

# ----------------------------------------------------------------------------------------------------------------------

class TgBot:
    def __init__(self, env: Environment):
        token = env.get("BOT_TOKEN")
        storage = MemoryStorage()

        self.bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        self.dispatcher = Dispatcher(storage=storage)
        self.tts = VoiceGenerator(env)
        self.msg_ids = []
        self.chat_id = 0

    def add_message(self, msg_id):
        self.msg_ids.append(msg_id)

    def include_router(self, router):
        self.dispatcher.include_router(router)

    def register_command(self, handler, cmd: Command):
        self.dispatcher.message.register(handler, cmd)

    def set_chat_id(self, chat_id):
        self.chat_id = chat_id

    async def start(self):
        aiogram_dialog.setup_dialogs(self.dispatcher)
        print("Bot is starting...")
        await self.dispatcher.start_polling(self.bot)

    async def generate_voice(self, chat_id, task: Task):
        print("chat_id = ", chat_id)
        voice_file = self.tts.generate_voice(task)
        voice = FSInputFile(voice_file)
        await self.bot.send_voice(chat_id=chat_id, voice=voice)

    async def delete_last_messages(self, chat_id, count=1):
        for i in range(0, count):
            msg_id = self.msg_ids.pop()
            await self.bot.delete_message(chat_id=chat_id, message_id=msg_id)