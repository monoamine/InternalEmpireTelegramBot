from chatterbox.tts import ChatterboxTTS
from task import Task
from util import Environment

import openai
import torch
import torchaudio

# ----------------------------------------------------------------------------------------------------------------------

class VoiceGenerator:
    def __init__(self, env: Environment):
        is_mac = torch.backends.mps.is_available()
        device = "mps" if is_mac else "cpu"

        self.model = ChatterboxTTS.from_pretrained(device=device)
        self.ref_audio = "ref_audio.mp3"
        self.chatgpt = openai.Client(api_key=env.get("OPENAI_API_KEY"))

    def generate_reminder(self, task: Task):
        request = f"Generate a short reminder in sarcastic tone for the task: {task.description}."
        reminder_text = self.chatgpt.responses.create(model="gpt-4", input=request).output_text
        return reminder_text

    def generate_voice(self, task: Task):
        result_filename = f"voice-{task.id()}.wav"
        reminder_text = self.generate_reminder(task)
        wav_file = self.model.generate(reminder_text, audio_prompt_path=self.ref_audio)

        torchaudio.save(result_filename, wav_file, self.model.sr)
        return result_filename