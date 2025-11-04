from scheduler import TaskScheduler
from task_manager import *
from tg_bot import *
from util import Environment

# ----------------------------------------------------------------------------------------------------------------------

import asyncio
import datetime
import logging
import sys
import operator

# ----------------------------------------------------------------------------------------------------------------------

from aiogram.filters import Command, CommandStart
from aiogram.fsm.state import State, StatesGroup

from aiogram.types import (
    CallbackQuery,
    Message
)

# ----------------------------------------------------------------------------------------------------------------------

from aiogram_dialog import (
    Dialog,
    DialogManager,
    Window,
    StartMode,
    ShowMode
)

from aiogram_dialog.widgets.common import Whenable

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
    Row
)

from aiogram_dialog.widgets.input import MessageInput, TextInput
from aiogram_dialog.widgets.text import Const, Format, List, Multi, Jinja

# ----------------------------------------------------------------------------------------------------------------------

env = Environment()
bot = TgBot(env)
task_manager = TaskManager()
new_task_mgr = NewTaskManager()
scheduler = TaskScheduler(bot, task_manager)
calendar_cfg = CalendarConfig(firstweekday=6, min_date=datetime.date.today())

# ----------------------------------------------------------------------------------------------------------------------

async def go_back(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.back()

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

async def get_all_tasks(**kwargs):
    all_tasks = []
    index = 1
    for (task_id, task) in task_manager.all_tasks().items():
        entry = (index, str(task))
        all_tasks.append(entry)
        index += 1

    return {
        "list": all_tasks
    }

async def get_today_tasks(**kwargs):
    today_tasks = []
    for (when, task_id) in task_manager.today_tasks():
        task = task_manager.get_task(task_id)
        entry = (when, task.description)
        today_tasks.append(entry)

    return {
        "list": today_tasks
    }

def is_empty_list(data: dict, widget: Whenable, manager: DialogManager):
    return len(data.get("list")) == 0

def is_non_empty_list(data: dict, widget: Whenable, manager: DialogManager):
    return len(data.get("list")) > 0

# ----------------------------------------------------------------------------------------------------------------------

class AllTasksForm(StatesGroup):
    task_list = State()

class TodayTasksForm(StatesGroup):
    task_list = State()

class NewTaskForm(StatesGroup):
    description = State()
    start_date = State()
    remind_times = State()
    summary = State()

# ----------------------------------------------------------------------------------------------------------------------

async def on_bot_start(message):
    bot.set_chat_id(message.chat.id)

async def all_tasks_form(message: Message, dialog_manager: DialogManager):
    bot.set_chat_id(message.chat.id)
    await dialog_manager.start(AllTasksForm.task_list, mode=StartMode.RESET_STACK)

async def today_tasks_form(message: Message, dialog_manager: DialogManager):
    bot.set_chat_id(message.chat.id)
    await dialog_manager.start(TodayTasksForm.task_list, mode=StartMode.RESET_STACK)

async def new_task_form(message: Message, dialog_manager: DialogManager):
    new_task_mgr.create()
    bot.set_chat_id(message.chat.id)
    await dialog_manager.start(NewTaskForm.description, mode=StartMode.RESET_STACK)

async def on_description_input(message: Message, widget, manager: DialogManager, data):
    last_msg_id = manager.current_stack().last_message_id
    bot.add_message(last_msg_id)

    description = message.text
    new_task_mgr.task().set_description(description)
    manager.dialog_data["description"] = description

    bot.add_message(message.message_id)
    await manager.next()

async def on_description_edit(callback: CallbackQuery, button: Button, manager: DialogManager):
    chat_id = callback.message.chat.id
    await bot.delete_last_messages(chat_id, 2)
    await manager.switch_to(NewTaskForm.description, ShowMode.EDIT)

async def on_date_selected(callback: CallbackQuery, widget, manager: DialogManager, selected_date: datetime.date):
    new_task_mgr.task().set_start_date(selected_date)
    await manager.next()

async def on_times_selected(callback: CallbackQuery, button, manager: DialogManager):
    selected_times = manager.find("multiselect_remind_times").get_checked()
    new_task_mgr.task().set_remind_times(selected_times)
    await manager.next()

async def on_task_confirmed(callback: CallbackQuery, button: Button, manager: DialogManager):
    msg = callback.message
    chat_id = msg.chat.id
    is_ok = new_task_mgr.confirm(task_manager)
    await msg.answer("Confirmed.")
    await manager.done()

async def on_task_form_cancel(callback: CallbackQuery, button: Button, manager: DialogManager):
    new_task_mgr.cancel()
    await on_cancel(callback, button, manager)

# ----------------------------------------------------------------------------------------------------------------------

description_window = Window(
    Const("Task description:"),
    Cancel(on_click=on_task_form_cancel),
    TextInput(id="description_input", on_success=on_description_input, on_error=on_error),
    state=NewTaskForm.description
)

start_date_window = Window(
    Const("Start date:"),
    Calendar(
        id="start_date_calendar",
        on_click=on_date_selected,
        config=calendar_cfg
    ),
    Row(
        Button(text=Const("Back"), id="back_to_desc_button", on_click=on_description_edit),
        Cancel(on_click=on_task_form_cancel)
    ),
    state=NewTaskForm.start_date
)

remind_times_window = Window(
    Const("Notification time (multiselect):"),
    Group(
        Multiselect(
            checked_text=Format("✓ {item[label]}"),
            unchecked_text=Format("{item[label]}"),
            id="multiselect_remind_times",
            item_id_getter=operator.itemgetter("value"),
            items="times"
        ),
        width=4
    ),
    Row(
        Back(),
        Cancel(on_click=on_task_form_cancel)
    ),
    Button(text=Const("Confirm"), id="confirm_times", on_click=on_times_selected),
    state=NewTaskForm.remind_times,
    getter=get_times
)

summary_window = Window(
    Jinja("<b>Here is a summary of your task:</b>\n{{summary}}"),
    Row(Back(), Cancel()),
    Button(text=Const("Confirm"), id="confirm", on_click=on_task_confirmed),
    state=NewTaskForm.summary,
    getter=get_summary,
    parse_mode="html"
)

# ----------------------------------------------------------------------------------------------------------------------

all_tasks_dialog = Dialog(
    Window(
        List(
            Format("{item[0]}: {item[1]}"),
            items="list",
            when=is_non_empty_list
        ),
        Const("You haven't created any tasks yet! Use /new command.", when=is_empty_list),
        state=AllTasksForm.task_list,
        getter=get_all_tasks
    )
)

today_tasks_dialog = Dialog(
    Window(
        List(
            Format("- {item[0]}: {item[1]}"),
            items="list",
            when=is_non_empty_list
        ),
        Const("No remaining tasks for today.", when=is_empty_list),
        state=TodayTasksForm.task_list,
        getter=get_today_tasks
    )
)

new_task_dialog = Dialog(
    description_window,
    start_date_window,
    remind_times_window,
    summary_window
)

# ----------------------------------------------------------------------------------------------------------------------

async def main():
    bot.register_command(on_bot_start, CommandStart())

    bot.include_router(all_tasks_dialog)
    bot.register_command(all_tasks_form, Command("all"))

    bot.include_router(new_task_dialog)
    bot.register_command(new_task_form, Command("new"))

    bot.include_router(today_tasks_dialog)
    bot.register_command(today_tasks_form, Command("today"))

    await scheduler.start()
    await bot.start()

# ----------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    try:
        asyncio.run(main())
    finally:
        new_task_dialog.shutdown()