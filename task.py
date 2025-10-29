import uuid
import datetime

#-----------------------------------------------------------------------------------------------------------------------

class Task:
    def __init__(self):
        self.uid: str = str(uuid.uuid4())
        self.description: str = ""
        self.start_date: datetime.date = datetime.date.today()
        self.remind_times: list[datetime.time] = []
        self.completed: bool = False

    def id(self):
        return self.uid

    def has_valid_description(self):
        return len(self.description) > 0

    def has_valid_start_date(self):
        return self.start_date >= datetime.date.today()

    def set_description(self, description: str):
        self.description = description

    def set_start_date(self, start_date: datetime.date):
        self.start_date = start_date

    def set_remind_times(self, remind_times: list[datetime.time]):
        self.remind_times = remind_times

    def set_remind_time(self, remind_time: datetime.time):
        self.remind_times = [remind_time]

    def mark_completed(self):
        self.completed = True

    def __str__(self):
        status = "Done" if self.completed else "Pending"

        return f"Status: {status}\n" \
               f"Description: {self.description}\n" \
               f"Start date: {self.start_date}\n" \
               f"Remind times: {self.remind_times}\n"