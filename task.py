import uuid
import datetime

#-----------------------------------------------------------------------------------------------------------------------

class Task:
    def __init__(self):
        self.uid: str = str(uuid.uuid4())
        self.description: str = ""
        self.start_date: datetime.date = datetime.date.today()
        self.remind_times = []
        self.enabled: bool = True

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

    def set_remind_times(self, remind_times: list[str]):
        self.remind_times = sorted(remind_times)

    def is_enabled(self):
        return self.enabled

    def set_status(self, enabled: bool):
        self.enabled = enabled

    def __str__(self):
        status = "Yes" if self.enabled else "No"

        text = f"Description: {self.description}\n" \
               f"Enabled: {status}\n" \
               f"Start date: {self.start_date.strftime("%d.%m.%Y")}\n" \
               f"Remind times:\n"

        for time in self.remind_times:
            text += f"- {time[:5]}\n"

        return text