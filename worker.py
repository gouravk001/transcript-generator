import whisper
import torch

device = "cpu"
model = whisper.load_model("base", device=device)

def transcribe_job(audio_path: str):
    result = model.transcribe(audio_path,task="translate")
    return result["text"]
