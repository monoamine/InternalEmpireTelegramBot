import json

# ----------------------------------------------------------------------------------------------------------------------

def generate_json(key_value_data: dict, file_name: str):
    with open(file_name, mode="w", encoding="utf-8") as out_file:
        json.dump(key_value_data, out_file, indent=4)

def read_json(file_name: str):
    with open(file_name, mode="r", encoding="utf-8") as in_file:
        key_value_data = json.load(in_file)
        return key_value_data

# ----------------------------------------------------------------------------------------------------------------------

class Environment:
    def __init__(self):
        self.env_data : dict = read_json("env.json")

    def get(self, key: str):
        if key in self.env_data:
            return self.env_data[key]
        return ""