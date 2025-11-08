import jsonpickle
import os.path

from task import *

# ----------------------------------------------------------------------------------------------------------------------

class TaskManager:
    def __init__(self):
        self.tasks: dict[str, Task] = {}
        self.remind_times: list[tuple[datetime.time, uuid.UUID]] = []
        self.__used_times: list[datetime.time] = []
        self.last_task_id = None

        self.__load_tasks()

    def get_task(self, task_id):
        if task_id not in self.tasks:
            return None

        return self.tasks[task_id]

    def add_task(self, task: Task):
        self.last_task_id = task.id()
        self.tasks[task.id()] = task

        if datetime.date.today() >= task.start_date:
            self.__add_task_reminders(task)

        self.remind_times.sort(key=lambda x: x[0])
        print(self.remind_times)
        self.__save_tasks()

    def remove_tasks(self, indices: list):
        for index in indices:
            self.__remove_task(index)

        self.__save_tasks()
        self.__reload_tasks()

    def disable_tasks(self, indices: list):
        for index in indices:
            self.__enable_task(index, False)

        self.__save_tasks()
        self.__reload_tasks()

    def enable_tasks(self, indices: list):
        for index in indices:
            self.__enable_task(index, True)

        self.__save_tasks()
        self.__reload_tasks()

    def all_tasks(self):
        return self.tasks

    def today_tasks(self):
        return self.remind_times

    def used_times(self):
        return self.__used_times

    def last_task(self):
        last_id = self.last_task_id
        if (last_id is None) or (last_id not in self.tasks):
            return None

        return self.tasks[last_id]

    def update(self):
        self.__reload_tasks()

    def __remove_task(self, index: int):
        i = 0
        for (task_id, task) in self.tasks.items():
            if str(i) != index:
                i += 1
                continue

            self.tasks.pop(task_id)
            break

    def __enable_task(self, index: int, enabled: bool):
        i = 0
        for (task_id, task) in self.tasks.items():
            if str(i) != index:
                i += 1
                continue

            self.tasks.get(task_id).enabled = enabled
            break

    def __add_task_reminders(self, task: Task):
        for time_str in task.remind_times:
            remind_time = datetime.time.fromisoformat(time_str)
            current_time = datetime.datetime.now().time()
            self.__used_times.append(remind_time)

            if remind_time > current_time:
                time_and_id = (remind_time, task.id())
                self.remind_times.append(time_and_id)

    def __load_tasks(self):
        if not os.path.exists("tasks.json"):
            return

        with open("tasks.json") as in_file:
            self.tasks = jsonpickle.decode(in_file.read())
            for task_id in self.tasks.keys():
                task = self.tasks[task_id]

                if not task.is_enabled():
                    continue

                if datetime.date.today() < task.start_date:
                    continue

                for time_str in sorted(task.remind_times):
                    remind_time = datetime.time.fromisoformat(time_str)
                    current_time = datetime.datetime.now().time()
                    self.__used_times.append(remind_time)

                    if remind_time > current_time:
                        time_and_id = (remind_time, task.id())
                        self.remind_times.append(time_and_id)

        self.remind_times.sort(key=lambda x: x[0])
        self.__used_times.sort()
        print(self.remind_times)

    def __reload_tasks(self):
        self.remind_times = []
        self.__used_times = []
        self.__load_tasks()

    def __save_tasks(self):
        with open("tasks.json", "w") as out_file:
            json_str = jsonpickle.encode(self.tasks)
            out_file.write(json_str)

# ----------------------------------------------------------------------------------------------------------------------

class NewTaskManager:
    def __init__(self):
        self.new_task = None

    def create(self):
        self.new_task = Task()

    def task(self):
        return self.new_task

    def cancel(self):
        self.new_task = None

    def confirm(self, task_mgr: TaskManager):
        if self.new_task is None:
            return False

        task_mgr.add_task(self.new_task)
        self.new_task = None
        return True