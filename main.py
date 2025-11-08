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
    Counter,
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
    used_times = task_manager.used_times()
    times = []
    for hour in range(6, 24):  # 9 AM to 4 PM
        for minute in (0, 30):
            time_obj = datetime.time(hour, minute)

            if time_obj in used_times:
                continue

            times.append({
                "label": time_obj.strftime("%H:%M"),
                "value": time_obj
            })

    return {"times": times}

async def get_summary(**kwargs):
    return {"summary": new_task_mgr.task()}

async def get_history(**kwargs):
    history = await bot.get_chat_history()
    result = []
    for item in history:
        entry = (item["query"], item["response"])
        result.append(entry)

    return {"list": result}

async def get_all_tasks(**kwargs):
    all_tasks = []
    index = 1
    for (task_id, task) in task_manager.all_tasks().items():
        entry = (index, str(task))
        all_tasks.append(entry)
        index += 1

    return {"list": all_tasks}

async def get_today_tasks(**kwargs):
    today_tasks = []
    for (when, task_id) in task_manager.today_tasks():
        task = task_manager.get_task(task_id)
        entry = (when, task.description)
        today_tasks.append(entry)

    return {"list": today_tasks}

async def get_tasks_description(**kwargs):
    all_tasks = []
    index = -1

    for (task_id, task) in task_manager.all_tasks().items():
        index += 1
        if not task.is_enabled():
            continue

        label = task.description
        if len(label) > 21:
            label = label[:-3] + "..."

        all_tasks.append({
            "label": label,
            "value": index
        })

    return {"list": all_tasks}

async def get_disabled_tasks_description(**kwargs):
    all_tasks = []
    index = -1

    for (task_id, task) in task_manager.all_tasks().items():
        index += 1
        if task.is_enabled():
            continue

        label = task.description
        if len(label) > 21:
            label = label[:-3] + "..."

        all_tasks.append({
            "label": label,
            "value": index
        })

    return {"list": all_tasks}

def is_empty_list(data: dict, widget: Whenable, manager: DialogManager):
    lst = data["list"]
    return len(lst) == 0

def is_non_empty_list(data: dict, widget: Whenable, manager: DialogManager):
    lst = data.get("list")
    return len(lst) > 0

# ----------------------------------------------------------------------------------------------------------------------

class NewTaskForm(StatesGroup):
    description = State()
    start_date = State()
    remind_times = State()
    summary = State()

class ChatForm(StatesGroup):
    query = State()

class VoiceForm(StatesGroup):
    query = State()
    response = State()

class HistoryForm(StatesGroup):
    history = State()

class AllTasksForm(StatesGroup):
    task_list = State()

class TodayTasksForm(StatesGroup):
    task_list = State()

class RemoveTasksForm(StatesGroup):
    task_list = State()

class DisableTasksForm(StatesGroup):
    task_list = State()

class EnableTasksForm(StatesGroup):
    task_list = State()

# ----------------------------------------------------------------------------------------------------------------------

async def on_bot_start(message):
    bot.set_chat_id(message.chat.id)

async def new_task_form(message: Message, dialog_manager: DialogManager):
    new_task_mgr.create()
    bot.set_chat_id(message.chat.id)
    await dialog_manager.start(NewTaskForm.description, mode=StartMode.RESET_STACK)

async def chat_form(message: Message, dialog_manager: DialogManager):
    bot.set_chat_id(message.chat.id)
    await dialog_manager.start(ChatForm.query, mode=StartMode.RESET_STACK)

async def voice_form(message: Message, dialog_manager: DialogManager):
    bot.set_chat_id(message.chat.id)
    await dialog_manager.start(VoiceForm.query, mode=StartMode.RESET_STACK)

async def history_form(message: Message, dialog_manager: DialogManager):
    bot.set_chat_id(message.chat.id)
    await dialog_manager.start(HistoryForm.history, mode=StartMode.RESET_STACK)

async def today_tasks_form(message: Message, dialog_manager: DialogManager):
    bot.set_chat_id(message.chat.id)
    await dialog_manager.start(TodayTasksForm.task_list, mode=StartMode.RESET_STACK)

async def all_tasks_form(message: Message, dialog_manager: DialogManager):
    bot.set_chat_id(message.chat.id)
    await dialog_manager.start(AllTasksForm.task_list, mode=StartMode.RESET_STACK)

async def remove_tasks_form(message: Message, dialog_manager: DialogManager):
    bot.set_chat_id(message.chat.id)
    await dialog_manager.start(RemoveTasksForm.task_list, mode=StartMode.RESET_STACK)

async def disable_tasks_form(message: Message, dialog_manager: DialogManager):
    bot.set_chat_id(message.chat.id)
    await dialog_manager.start(DisableTasksForm.task_list, mode=StartMode.RESET_STACK)

async def enable_tasks_form(message: Message, dialog_manager: DialogManager):
    bot.set_chat_id(message.chat.id)
    await dialog_manager.start(EnableTasksForm.task_list, mode=StartMode.RESET_STACK)

# ----------------------------------------------------------------------------------------------------------------------

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
    selected_times = manager.find("remind_times_multiselect").get_checked()
    new_task_mgr.task().set_remind_times(selected_times)
    await manager.next()

async def on_task_confirmed(callback: CallbackQuery, button: Button, manager: DialogManager):
    msg = callback.message
    chat_id = msg.chat.id
    is_ok = new_task_mgr.confirm(task_manager)
    await msg.answer("Confirmed.")
    await manager.done()

async def on_cancel_new_task(callback: CallbackQuery, button: Button, manager: DialogManager):
    new_task_mgr.cancel()
    await on_cancel(callback, button, manager)

# ----------------------------------------------------------------------------------------------------------------------

async def on_chat_input(message: Message, widget, manager: DialogManager, data):
    query = message.text
    await bot.query_chat_gpt(message.chat.id, query)
    await manager.done()

async def on_voice_input(message: Message, widget, manager: DialogManager, data):
    query = message.text
    await message.answer("Please wait, generating a voice message...")
    await bot.generate_voice_from_text(message.chat.id, query)
    await manager.done()

async def on_tasks_removed(callback: CallbackQuery, button, manager: DialogManager):
    selected_tasks = manager.find("remove_tasks_multiselect").get_checked()
    task_manager.remove_tasks(selected_tasks)
    msg = callback.message
    await msg.answer("Confirmed.")
    await manager.done()

async def on_tasks_disabled(callback: CallbackQuery, button, manager: DialogManager):
    selected_tasks = manager.find("disable_tasks_multiselect").get_checked()
    task_manager.disable_tasks(selected_tasks)
    msg = callback.message
    await msg.answer("Confirmed.")
    await manager.done()

async def on_tasks_enabled(callback: CallbackQuery, button, manager: DialogManager):
    selected_tasks = manager.find("enable_tasks_multiselect").get_checked()
    task_manager.enable_tasks(selected_tasks)
    msg = callback.message
    await msg.answer("Confirmed.")
    await manager.done()

# ----------------------------------------------------------------------------------------------------------------------

description_window = Window(
    Const("Task description:"),
    Button(
        text=Const("Cancel"),
        id="cancel_new_task_button1",
        on_click=on_cancel_new_task
    ),
    TextInput(
        id="description_input",
        on_success=on_description_input,
        on_error=on_error
    ),
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
        Button(
            text=Const("Back"),
            id="back_to_desc_button",
            on_click=on_description_edit
        ),
        Button(
            text=Const("Cancel"),
            id="cancel_new_task_button2",
            on_click=on_cancel_new_task
        )
    ),
    state=NewTaskForm.start_date
)

remind_times_window = Window(
    Const("Notification time (multiselect):"),
    Group(
        Multiselect(
            checked_text=Format("✓ {item[label]}"),
            unchecked_text=Format("{item[label]}"),
            id="remind_times_multiselect",
            item_id_getter=operator.itemgetter("value"),
            items="times"
        ),
        width=4
    ),
    Row(
        Back(),
        Button(
            Const("Cancel"),
            id="cancel_new_task_button3",
            on_click=on_cancel_new_task
        )
    ),
    Button(
        text=Const("Confirm"),
        id="confirm_remind_times_button",
        on_click=on_times_selected
    ),
    state=NewTaskForm.remind_times,
    getter=get_times
)

summary_window = Window(
    Jinja("<b>Here is a summary of your task:</b>\n{{summary}}"),
    Row(
        Back(),
        Cancel()
    ),
    Button(
        text=Const("Confirm"),
        id="confirm",
        on_click=on_task_confirmed
    ),
    state=NewTaskForm.summary,
    getter=get_summary,
    parse_mode="html"
)

# ----------------------------------------------------------------------------------------------------------------------

new_task_dialog = Dialog(
    description_window,
    start_date_window,
    remind_times_window,
    summary_window
)

chat_dialog = Dialog(
    Window(
        Const("Ask anything from ChatGPT:"),
        Button(
            text=Const("Cancel"),
            id="cancel_chat_button",
            on_click=on_cancel
        ),
        TextInput(
            id="chat_input",
            on_success=on_chat_input,
            on_error=on_error
        ),
        state=ChatForm.query
    )
)

history_dialog = Dialog(
    Window(
        List(
            Format("Q: {item[0]}\nA: {item[1]}\n\n"),
            items="list",
            when=is_non_empty_list
        ),
        Const(
            "Your chat history is empty. Use /chat to start a new chat.",
            when=is_empty_list
        ),
        state=HistoryForm.history,
        getter=get_history
    )
)

voice_dialog = Dialog(
    Window(
        Const("Text to generate a voice message from:"),
        Button(
            text=Const("Cancel"),
            id="cancel_voice_button",
            on_click=on_cancel
        ),
        TextInput(
            id="voice_input",
            on_success=on_voice_input,
            on_error=on_error
        ),
        state=VoiceForm.query
    )
)

all_tasks_dialog = Dialog(
    Window(
        List(
            Format("{item[0]}: {item[1]}"),
            items="list",
            when=is_non_empty_list
        ),
        Const(
            "You haven't created any tasks yet! Use /new command.",
            when=is_empty_list
        ),
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
        Const(
            "No remaining tasks for today.",
            when=is_empty_list
        ),
        state=TodayTasksForm.task_list,
        getter=get_today_tasks
    )
)

remove_tasks_dialog = Dialog(
    Window(
        Const(
            "Select tasks to remove:",
            when=is_non_empty_list
        ),
        Const(
            "You haven't created any tasks yet! Use /new command.",
            when=is_empty_list
        ),
        Group(
            Multiselect(
                checked_text=Format("✓ {item[label]}"),
                unchecked_text=Format("{item[label]}"),
                id="remove_tasks_multiselect",
                item_id_getter=operator.itemgetter("value"),
                items="list"
            ),
            when=is_non_empty_list,
            width=1
        ),
        Button(
            text=Const("Confirm"),
            id="confirm_remove_tasks_button",
            on_click=on_tasks_removed,
            when=is_non_empty_list
        ),
        state=RemoveTasksForm.task_list,
        getter=get_tasks_description
    )
)

disable_tasks_dialog = Dialog(
    Window(
        Const(
            "Select tasks to disable:",
            when=is_non_empty_list
        ),
        Const(
            "You haven't created any tasks yet! Use /new command.",
            when=is_empty_list
        ),
        Column(
            Multiselect(
                checked_text=Format("✓ {item[label]}"),
                unchecked_text=Format("{item[label]}"),
                id="disable_tasks_multiselect",
                item_id_getter=operator.itemgetter("value"),
                items="list"
            ),
            when=is_non_empty_list
        ),
        Button(
            text=Const("Confirm"),
            id="confirm_disable_tasks_button",
            on_click=on_tasks_disabled,
            when=is_non_empty_list
        ),
        state=DisableTasksForm.task_list,
        getter=get_tasks_description
    )
)

enable_tasks_dialog = Dialog(
    Window(
        Const(
            "Select tasks to enable:",
            when=is_non_empty_list
        ),
        Const(
            "You have no disabled tasks.",
            when=is_empty_list
        ),
        Column(
            Multiselect(
                checked_text=Format("✓ {item[label]}"),
                unchecked_text=Format("{item[label]}"),
                id="enable_tasks_multiselect",
                item_id_getter=operator.itemgetter("value"),
                items="list"
            ),
            when=is_non_empty_list
        ),
        Button(
            text=Const("Confirm"),
            id="confirm_enable_tasks_button",
            on_click=on_tasks_enabled,
            when=is_non_empty_list
        ),
        state=EnableTasksForm.task_list,
        getter=get_disabled_tasks_description
    )
)

# ----------------------------------------------------------------------------------------------------------------------

async def main():
    bot.register_command(on_bot_start, CommandStart())

    bot.include_router(new_task_dialog)
    bot.register_command(new_task_form, Command("new"))

    bot.include_router(chat_dialog)
    bot.register_command(chat_form, Command("chat"))

    bot.include_router(history_dialog)
    bot.register_command(history_form, Command("history"))

    bot.include_router(voice_dialog)
    bot.register_command(voice_form, Command("voice"))

    bot.include_router(today_tasks_dialog)
    bot.register_command(today_tasks_form, Command("today"))

    bot.include_router(all_tasks_dialog)
    bot.register_command(all_tasks_form, Command("all"))

    bot.include_router(remove_tasks_dialog)
    bot.register_command(remove_tasks_form, Command("remove"))

    bot.include_router(disable_tasks_dialog)
    bot.register_command(disable_tasks_form, Command("disable"))

    bot.include_router(enable_tasks_dialog)
    bot.register_command(enable_tasks_form, Command("enable"))

    await scheduler.start()
    await bot.start()

# ----------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    try:
        asyncio.run(main())
    finally:
        new_task_dialog.shutdown()