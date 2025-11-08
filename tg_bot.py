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
import json
import os.path

# ----------------------------------------------------------------------------------------------------------------------

class TgBot:
    def __init__(self, env: Environment):
        token = env.get("BOT_TOKEN")
        storage = MemoryStorage()

        self.bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        self.dispatcher = Dispatcher(storage=storage)
        self.tts = VoiceGenerator(env)
        self.__chat_history = []
        self.msg_ids = []
        self.chat_id = 0

        self.__load_chat_history()

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

    async def generate_voice_from_text(self, chat_id, text):
        print("chat_id = ", chat_id)
        voice_file = self.tts.generate_voice_from_text(text)
        voice = FSInputFile(voice_file)
        await self.bot.send_voice(chat_id=chat_id, voice=voice)

    async def query_chat_gpt(self, chat_id, query):
        print("chat_id = ", chat_id)
        response = self.tts.query_chat_gpt(query)

        entry = {
            "query": query,
            "response": response
        }

        self.__chat_history.append(entry)
        self.__save_chat_history()
        await self.bot.send_message(chat_id=chat_id, text=response)

    async def get_chat_history(self) -> list:
        return self.__chat_history

    async def delete_last_messages(self, chat_id, count=1):
        for i in range(0, count):
            msg_id = self.msg_ids.pop()
            await self.bot.delete_message(chat_id=chat_id, message_id=msg_id)

    def __save_chat_history(self):
        with open("history.json", "w") as out_file:
            data = {
                "history": self.__chat_history
            }
            json.dump(data, out_file)

    def __load_chat_history(self):
        if not os.path.exists("history.json"):
            return

        with open("history.json", "r") as in_file:
            data = json.load(in_file)
            self.__chat_history = data["history"]