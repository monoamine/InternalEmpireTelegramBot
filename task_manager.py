from task import *

#-----------------------------------------------------------------------------------------------------------------------

class TaskManager:
    def __init__(self):
        self.tasks : dict[str, Task] = {}
        self.remind_times : dict[datetime.time, str] = {}

    def add_task(self, task: Task):
        self.tasks[task.id()] = task

    def remove_task(self, task_id : str | uuid.UUID):
        self.tasks.pop(str(task_id))

    def tasks(self):
        return self.tasks

#-----------------------------------------------------------------------------------------------------------------------

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