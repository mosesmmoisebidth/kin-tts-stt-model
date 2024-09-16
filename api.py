from fastapi import FastAPI, Request, File, Form
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from num2words import num2words
import translators as ts
import re
from backend_logic import Generator, Transcriber
from typing import Annotated
from starlette.responses import RedirectResponse
import gradio as gr


api = FastAPI(
    title="Text to Speech API",
    summary="A simple API that transcribes text to speech",
    version="1.0.1",
    contact={
        "name": "NaviGO LTD",
        "url": "https://navigo.rw",
        "email": "team.navigo@gmail.com",
    },
    license_info={"name": "GNU GENERAL PUBLIC LICENSE",},
    openapi_url="/openapi.json",
    docs_url="/swagger",
    redoc_url="/docs"
)
class AudioObject(BaseModel):
    audio_bytes: Annotated[bytes, Form(...)]
    audio_bytes_size: int | None
    auto_segment: bool = False

class ResponseObj(BaseModel):
    text: str
    
class Text(BaseModel):
    text: str

def replace_numbers_with_placeholders(text):
    word_map = {}
    counter = 1
    
    def num_to_placeholder(match):
        nonlocal counter
        number = int(match.group(0))
        placeholder = f"{{NUM{counter}}}"
        word_map[placeholder] = num2words(number)
        counter += 1
        return placeholder
    
    replaced_text = re.sub(r'\b\d+\b', num_to_placeholder, text)
    return replaced_text, word_map

def translate_placeholders(word_map):
    print("the word map is: {}".format(word_map))
    translated_map = {}
    for placeholder, word in word_map.items():
        try:
            translated_word = ts.translate_text(word, from_language='en', to_language='rw', translator='google')
            translated_map[placeholder] = translated_word
        except Exception as e:
            print(f"Error translating word '{word}': {e}")
            translated_map[placeholder] = word  # Fallback to original if translation fails
    return translated_map

def replace_placeholders_in_text(text, translated_map):
    for placeholder, translated_word in translated_map.items():
        text = text.replace(placeholder, translated_word)
    return text

@api.get("/")
async def handle_default():
    return RedirectResponse(url="/docs")

@api.post("/transcribe",
          summary="Transcribe Speech",
          description="Transcribe the audio file into text file audio(kinyarwanda)",
          tags=["Speech to Text"],
          responses={
              200:{
                  "description": "Successfull transcription",
                  "content": { "application/json": { "example": { "text": "Transcribed text", "stats": 0}}}
              },
              500: {
                  "description": "Transcription error",
                  "content": { "application/json": { "example": { "text": "Sorry, we could not transcribe your audio, Please try again.", "Error": "<error_message>"}}}
              }
    }
          )
async def transcribe_speech(audio_bytes: bytes = File(...)) -> JSONResponse:
    try:
        speech = Transcriber(audio_bytes)
        return JSONResponse(
            status_code=200,
            content={
                "text": speech.transcription,
                "stats": 0  # log.log,
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "text": f"Sorry, we could not transcribe your audio. Please try again. Error: {str(e)}"
            }
        )
        
@api.post("/generate",
          summary="Generate Speech",
          description="Generate an audio file from the given text using a text-to-speech model.",
          tags=["Text to Speech"],
          responses={
              200: {
                  "description": "Successful audio generation",
                  "content": { "application/octet-stream": { "exampe": "audio.wav"}}
              },
              500: {
                  "description": "Audio generation error",
                  "content": { "application/json": { "example": { "text": "Sorry, we could not generate audio from your text. Please try again with matching language", "error": "<error_message>", "stats": 0}}}
              }
          }
          )
async def tts(request: Request, text: Text) -> FileResponse:
    """
    This function generates an audio file from the given text using a text-to-speech model.
    The generated audio file is returned as a response.
    """
    sentence = text.text
    sentence_with_placeholders, word_map = replace_numbers_with_placeholders(sentence)
    translated_map = translate_placeholders(word_map)
    final_sentence = replace_placeholders_in_text(sentence_with_placeholders, translated_map)
    try:
        audio = Generator(text=final_sentence)
        return FileResponse(
            audio.file_path, 
            media_type="application/octet-stream", 
            filename="audio.wav"
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "text": "Sorry, we could not generate audio from your text. Please try again.",
                "error": str(e),
                "stats": 0
            }
        )
async def tts_gradio(text: str) -> FileResponse:
    sentence = text
    sentence_with_placeholders, word_map = replace_numbers_with_placeholders(sentence)
    translated_map = translate_placeholders(word_map)
    final_sentence = replace_placeholders_in_text(sentence_with_placeholders, translated_map)
    try:
        audio = Generator(text=final_sentence)
        with open(audio.file_path, "rb") as f:
            audio_bytes = f.read()
        return audio_bytes
        # return FileResponse(
        #     audio.file_path, 
        #     media_type="application/octet-stream", 
        #     filename="audio.wav"
        # )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "text": "Sorry, we could not generate audio from your text. Please try again.",
                "error": str(e),
                "stats": 0
            }
        )
    
demo_examples = [
    ["Turimo kwiga isomo ryikinyarwanda ndabasuhuje cyane kuba mwese mwabashije kurikurikira neza"],
    ["Turabishimiye cyane ku bwa serivisi nziza mukomeje kutugezaho murakoze cyane!"]
]    
#Demo for the Gradio Interface
text_to_speech_demo = gr.Interface(
    fn=tts_gradio,
    inputs='text',
    outputs='audio',
    title='Kin Text to Speech Translation',
    description='This is the Kinyarwanda text to speech translation model',
    examples=demo_examples
    )

# @api.on_event("startup")
# async def handle_startup():
#     print("SERVER UP AND RUNNING ON http://127.0.0.1:8001")

# @api.on_event("shutdown")
# async def handle_shutdown():
#     print("SERVER RUNNING CANCELLED. SERVER DOWN")

if __name__ =="__main__":
    text_to_speech_demo.launch(share=True)

