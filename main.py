from task_manager import *
from util import Environment

# ----------------------------------------------------------------------------------------------------------------------

import asyncio
import datetime
import logging
import sys
import operator
import uuid
import schedule
import time
import threading

# ----------------------------------------------------------------------------------------------------------------------

from aiogram import Bot, Dispatcher, F, Router, html

from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from aiogram.types import (
    CallbackQuery,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove, InlineKeyboardMarkup
)

# ----------------------------------------------------------------------------------------------------------------------

from aiogram_dialog import (
    Dialog,
    DialogManager,
    DialogProtocol,
    Window,
    StartMode,
    setup_dialogs,
    ShowMode
)

from aiogram_dialog.widgets.kbd import (
    Back,
    Button,
    Calendar,
    CalendarConfig,
    Cancel,
    Column,
    Group,
    ListGroup,
    Multiselect,
    Next,
    Row,
    CopyText
)

from aiogram_dialog.widgets.input import MessageInput, TextInput
from aiogram_dialog.widgets.kbd.button import OnClick
from aiogram_dialog.widgets.text import Const, Format, Multi, Jinja

#-----------------------------------------------------------------------------------------------------------------------

env = Environment()
task_manager = TaskManager()
new_task_mgr = NewTaskManager()
calendar_cfg = CalendarConfig(firstweekday=6, min_date=datetime.date.today())

# ----------------------------------------------------------------------------------------------------------------------

async def go_back(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(TaskForm.description, ShowMode.EDIT)

async def go_next(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.next()

async def on_cancel(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.message.answer("Canceled.")
    await manager.done()

async def on_error(message: Message, widget, manager: DialogManager, error_: ValueError):
    await message.answer(f"Error: error_text")

# ----------------------------------------------------------------------------------------------------------------------

async def get_times(**kwargs):
    times = []
    for hour in range(6, 24):  # 9 AM to 4 PM
        for minute in (0, 30):
            time_obj = datetime.time(hour, minute)
            times.append({
                "label": time_obj.strftime("%H:%M"),
                "value": time_obj
            })

    return {"times": times}

async def get_summary(**kwargs):
    return {"summary": new_task_mgr.task()}

# ----------------------------------------------------------------------------------------------------------------------

class TaskForm(StatesGroup):
    description = State()
    start_date = State()
    remind_times = State()
    summary = State()

# ----------------------------------------------------------------------------------------------------------------------

async def start_task_form(message, dialog_manager: DialogManager):
    new_task_mgr.create()
    await dialog_manager.start(TaskForm.description, mode=StartMode.RESET_STACK)

async def on_description_input(message: Message, widget, manager: DialogManager, data):
    description = message.text
    new_task_mgr.task().set_description(description)
    manager.dialog_data["description"] = description
    await manager.next()

async def on_date_selected(callback: CallbackQuery, widget, manager: DialogManager, selected_date: datetime.date):
    new_task_mgr.task().set_start_date(selected_date)
    await manager.next()

async def on_times_selected(callback: CallbackQuery, button, manager: DialogManager):
    selected_times = manager.find("remind_times_widget").get_checked()
    new_task_mgr.task().set_remind_times(selected_times)
    await manager.next()

async def on_task_confirmed(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.message.answer("Confirmed.")
    await manager.done()

async def on_task_form_cancel(callback: CallbackQuery, button: Button, manager: DialogManager):
    new_task_mgr.cancel()
    await on_cancel(callback, button, manager)

# ----------------------------------------------------------------------------------------------------------------------

description_window = Window(
    Const("Task description:"),
    Cancel(on_click=on_task_form_cancel),
    TextInput(id="description_input", on_success=on_description_input, on_error=on_error),
    state=TaskForm.description
)

start_date_window = Window(
    Const("Start date:"),
    Calendar(
        id="task_calendar",
        on_click=on_date_selected,
        config=calendar_cfg
    ),
    Row(
        Back(),
        Cancel(on_click=on_task_form_cancel)
    ),
    state=TaskForm.start_date
)

remind_times_window = Window(
    Const("Notification time (multiselect):"),
    Group(
        Multiselect(
            checked_text=Format("✓ {item[label]}"),
            unchecked_text=Format("{item[label]}"),
            id="remind_times_widget",
            item_id_getter=operator.itemgetter("value"),
            items="times"
        ),
        width=4
    ),
    Row(
        Back(),
        Cancel(on_click=on_task_form_cancel)
    ),
    Button(Const("Confirm"), id="confirm_times", on_click=on_times_selected),
    state=TaskForm.remind_times,
    getter=get_times
)

summary_window = Window(
    Jinja(
        "<b>Here is a summary of your task:</b>\n{{summary}}"
    ),
    Row(Back(), Cancel()),
    Button(Const("Confirm"), id="confirm", on_click=on_task_confirmed),
    state=TaskForm.summary,
    getter=get_summary,
    parse_mode="html"
)

# ----------------------------------------------------------------------------------------------------------------------

dialog = Dialog(
    description_window,
    start_date_window,
    remind_times_window,
    summary_window
)

# ----------------------------------------------------------------------------------------------------------------------

async def main():
    token = env.get("BOT_TOKEN")
    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.include_router(dialog)
    dp.message.register(start_task_form, Command("newtask"))
    setup_dialogs(dp)

    print("Bot is starting...")
    await dp.start_polling(bot)

# ----------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    try:
        asyncio.run(main())
        #scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        #scheduler_thread.start()
    finally:
        dialog.shutdown()