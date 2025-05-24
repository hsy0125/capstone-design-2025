from google.cloud import speech
from dotenv import load_dotenv
import os
import pyaudio
import wave
from voice_db import find_voice_answer, save_voice_answer
import openai
from gtts import gTTS
from playsound import playsound
import re
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
## tts 속도 조절
def change_speed(sound, speed=2.0):
    return sound._spawn(sound.raw_data, overrides={
        "frame_rate": int(sound.frame_rate * speed)
    }).set_frame_rate(sound.frame_rate)

def speak_text(text):
    tts = gTTS(text=text, lang='ko')
    tts.save("response.mp3")

    sound = AudioSegment.from_file("response.mp3", format="mp3")
    faster_sound = change_speed(sound, speed=1.3)  # 1.3배속 재생
    play(faster_sound)
    
load_dotenv()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
openai.api_key = os.getenv("OPENAI_API_KEY")

def record_audio(filename="temp.wav", seconds=5):
    RATE = 16000
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1

    print("🎙️ 말해주세요...")
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                    input=True, frames_per_buffer=CHUNK)

    frames = []
    for _ in range(0, int(RATE / CHUNK * seconds)):
        data = stream.read(CHUNK)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    p.terminate()

    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
    print("✅ 녹음 완료")

def extract_main_content(text):
    # 설명과 해결 방법만 추출
    설명 = re.search(r"⚠️ 설명:\n(.+?)\n\n", text, re.DOTALL)
    해결 = re.search(r"🛠 해결 방법:\n(.+)$", text, re.DOTALL)
    parts = []
    if 설명:
        parts.append(설명.group(1).strip())
    if 해결:
        parts.append(해결.group(1).strip())
    return "\n".join(parts) if parts else text

def speak_text(text):
    tts = gTTS(text=text, lang='ko')
    tts.save("response.mp3")
    playsound("response.mp3")

def transcribe_and_answer(filename="temp.wav", car_model="아반떼"):
    client = speech.SpeechClient()

    with open(filename, 'rb') as audio_file:
        audio_bytes = audio_file.read()

    audio = speech.RecognitionAudio(content=audio_bytes)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="ko-KR"
    )

    response = client.recognize(config=config, audio=audio)

    for result in response.results:
        question = result.alternatives[0].transcript
        print(f"🧠 인식된 질문: {question}")

        # 1. DB 검색 시도
        answer = find_voice_answer(question)

        # 2. GPT fallback
        if not answer:
            print("🤖 GPT 호출 중...")
            gpt_response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"You are a car assistant for model: {car_model}."},
                    {"role": "user", "content": question}
                ]
            )
            answer = gpt_response.choices[0].message.content.strip()
            print("💬 GPT 응답:")

        # 3. 출력 및 저장 + 음성 재생 (내용만 말하기)
        print(answer)
        speak_text(extract_main_content(answer))
        save_voice_answer(question, answer, car_model)
        print("✅ 질문과 답변 저장 완료")

record_audio()
transcribe_and_answer()