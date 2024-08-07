from TTS.utils.synthesizer import Synthesizer
import os
from pydantic import BaseModel
from typing import ClassVar
import os
from speechbrain.inference.ASR import EncoderDecoderASR
asr_model = EncoderDecoderASR.from_hparams(source="speechbrain/asr-wav2vec2-commonvoice-rw")

class Transcriber:
    def __init__(self, audio_bytes: bytes) -> None:
        self.audio_bytes = audio_bytes
        # self.temp_audio_file_path = ""
        self.save_audio()
        self.transcription = self.transcribe()
        # os.remove(self.temp_audio_file_path)

    def save_audio(self):
        self.file_id = len(os.listdir('sounds/'))
        with open(f"sounds/sound-{self.file_id}.wav", "wb") as audio_file:
            audio_file.seek(0)
            audio_file.write(self.audio_bytes)
        #with tempfile.NamedTemporaryFile(delete=False) as audio_file:
        #   self.temp_audio_file_path = audio_file.name
        #   audio_file.write(self.audio_bytes) 
        #print("stored the audio temporarily to {}".format(self.temp_audio_file_path))
        
    def transcribe(self):
        try:
            file_path = f"sounds/sound-{self.file_id}.wav"
            result = asr_model.transcribe_file(file_path)
            return result
            #result = asr_model.transcribe_file(self.temp_audio_file_path)
            #return result
        except Exception as e:
            return str(e)
class tts_response(BaseModel):
    status_code: int = 10
    error: str = ""


class TTS_MODEL(BaseModel):
    MAX_TXT_LEN: int = os.getenv('TTS_MAX_TXT_LEN', 1000)
    SOUNDS_DIR: str = "sounds"
    MODEL_PATH: str = "./model.pth"
    CONFIG_PATH: str = "config.json"
    SPEAKERS_PATH: str = "speakers.pth"
    ENCODER_CHECKPOINT_PATH: str = "SE_checkpoint.pth.zip"
    ENCODER_CONFIG: str = "config_se.json"
    SPEAKER_WAV: ClassVar[str] = "conditioning_audio.wav"

# Initiate the model
engine_specs = TTS_MODEL()

engine = Synthesizer(
    engine_specs.MODEL_PATH,
    engine_specs.CONFIG_PATH,
    tts_speakers_file=engine_specs.SPEAKERS_PATH,
    encoder_checkpoint=engine_specs.ENCODER_CHECKPOINT_PATH,
    encoder_config=engine_specs.ENCODER_CONFIG,
)

class Generator:
    MAX_TXT_LEN: int = 1000  # os.getenv('TTS_MAX_TXT_LEN')
    SOUNDS_DIR: str = "sounds"
    MODEL_PATH: str = "./model.pth"
    CONFIG_PATH: str = "config.json"
    SPEAKERS_PATH: str = "speakers.pth"
    ENCODER_CHECKPOINT_PATH: str = "SE_checkpoint.pth.zip"
    ENCODER_CONFIG: str = "config_se.json"
    SPEAKER_WAV: ClassVar[str] = "conditioning_audio.wav"

    def __init__(self, text) -> None:
        self.response = tts_response()  # Initialize in __init__
        if len(text) > self.MAX_TXT_LEN:
            text = text[: self.MAX_TXT_LEN]  # cut off text to the limit
            self.response.status_code = 10
            self.response.error = f"Input text was cutoff since it went over the {self.MAX_TXT_LEN} character limit."

        self.audio_bytes: bytes = engine.tts(text, speaker_wav=self.SPEAKER_WAV)
        # save the audio
        self.save_audio()

    def save_audio(self) -> str:
        file_id = len(os.listdir(self.SOUNDS_DIR)) + 1
        file_path: str = f"{self.SOUNDS_DIR}/sound-{file_id}.wav"

        with open(file_path, "wb+") as audio_file:
            engine.save_wav(self.audio_bytes, audio_file)

        self.file_path = file_path