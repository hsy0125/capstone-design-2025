from google.cloud import speech
from dotenv import load_dotenv
import os
import pyaudio
import wave
from db import save_answer  # DB 저장 함수만 사용

load_dotenv()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")  #구글api 호출 인증

def record_audio(filename="temp.wav", seconds=5):  #5초동안 음성받아 저장
    RATE = 16000
    CHUNK = 1024                                    #16000Hz, 16bit, mono 채널 구성 (Google STT 기본 권장 설정)
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

def transcribe_and_save(filename="temp.wav", car_model="아반데"):
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

        # 응답 없이 저장만 수행
        save_answer(question, "(응답 없음 - 기록 목적)", car_model)
        print("📎 질문 저장 완료")

record_audio()
transcribe_and_save()
