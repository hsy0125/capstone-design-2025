# from google.cloud import speech
# from dotenv import load_dotenv
# import os
# import pyaudio
# import wave
# from voice_db import find_voice_answer, save_voice_answer
# import openai
# from gtts import gTTS
# from playsound import playsound
# import re

# load_dotenv()
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
# openai.api_key = os.getenv("OPENAI_API_KEY")

# def record_audio(filename="temp.wav", seconds=5):
#     RATE = 16000                                                    # 샘플링레이트 초당16000프레임
#     CHUNK = 1024                                                    # 1024프레임
#     FORMAT = pyaudio.paInt16                                        # 16비트 오디오 포멧
#     CHANNELS = 1                                                    # 채널수

#     print("🎙️ 말해주세요...")
#     p = pyaudio.PyAudio()                                           # PyAudio 객체 생성
#     stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,    # 입력스트림을 설정해 오디오입력
#                     input=True, frames_per_buffer=CHUNK)

#     frames = []                                                     # 5초동안 읽어서 frames 리스트에 저장
#     for _ in range(0, int(RATE / CHUNK * seconds)):
#         data = stream.read(CHUNK)
#         frames.append(data)

#     stream.stop_stream()                                            # 입력 종료
#     stream.close()
#     p.terminate()

#     with wave.open(filename, 'wb') as wf:                           # wav파일생성 저장
#         wf.setnchannels(CHANNELS)
#         wf.setsampwidth(p.get_sample_size(FORMAT))
#         wf.setframerate(RATE)
#         wf.writeframes(b''.join(frames))
#     print("✅ 녹음 완료")

# def extract_main_content(text):
#     # 설명과 해결 방법 또는 응급조치 단계만 추출
#     설명 = re.search(r"⚠️ 설명:\n(.+?)\n\n", text, re.DOTALL)
#     해결 = re.search(r"🛠 해결 방법:\n(.+)$", text, re.DOTALL)
#     응급 = re.search(r"🧭 응급조치 단계:\n(.+)$", text, re.DOTALL)

#     if 설명 or 해결:
#         parts = []
#         if 설명:
#             parts.append(설명.group(1).strip())
#         if 해결:
#             parts.append(해결.group(1).strip())
#         return "\n".join(parts)
#     elif 응급:
#         return 응급.group(1).strip()
#     else:
#         return text

# def speak_text(text):
#     tts = gTTS(text=text, lang='ko')
#     tts.save("response.mp3")
#     playsound("response.mp3")

# def transcribe_and_answer(filename="temp.wav", car_model="아반떼"):
#     client = speech.SpeechClient()

#     with open(filename, 'rb') as audio_file:
#         audio_bytes = audio_file.read()

#     audio = speech.RecognitionAudio(content=audio_bytes)
#     config = speech.RecognitionConfig(
#         encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
#         sample_rate_hertz=16000,
#         language_code="ko-KR"
#     )

#     response = client.recognize(config=config, audio=audio)

#     for result in response.results:
#         question = result.alternatives[0].transcript
#         print(f"🧠 인식된 질문: {question}")

#         # 1. DB 검색 시도
#         answer = find_voice_answer(question)

#         # 2. GPT fallback
#         if not answer:
#             print("🤖 GPT 호출 중...")
#             gpt_response = openai.chat.completions.create(
#                 model="gpt-3.5-turbo",
#                 messages=[
#                     {"role": "system", "content": f"You are a car assistant for model: {car_model}."},
#                     {"role": "user", "content": question}
#                 ]
#             )
#             answer = gpt_response.choices[0].message.content.strip()
#             print("💬 GPT 응답:")

#         # 3. 출력 및 저장 + 음성 재생 (내용만 말하기)
#         print(answer)
#         speak_text(extract_main_content(answer))
#         save_voice_answer(question, answer, car_model)
#         print("✅ 질문과 답변 저장 완료")

# record_audio()
# transcribe_and_answer()

# test_voice_2.py  — 차량용품 키워드 감지 → 네이버 쇼핑 링크 자동 첨부 (음성은 링크 미낭독)

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
from urllib.parse import quote

# -------------------- 설정 --------------------
ACCESSORY_LINK_ONLY = False  # True: 링크만 응답 / False: 원래 답변 + 링크 덧붙임
DEFAULT_CAR_MODEL = "아반떼"
SAMPLE_RATE = 16000
CHUNK = 1024
CHANNELS = 1

# -------------------- 초기화 --------------------
load_dotenv()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
openai.api_key = os.getenv("OPENAI_API_KEY")

# -------------------- 유틸 함수 --------------------
def record_audio(filename="temp.wav", seconds=5):
    print("🎙️ 말해주세요...")
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=CHANNELS, rate=SAMPLE_RATE,
                    input=True, frames_per_buffer=CHUNK)
    frames = []
    for _ in range(0, int(SAMPLE_RATE / CHUNK * seconds)):
        data = stream.read(CHUNK)
        frames.append(data)
    stream.stop_stream()
    stream.close()
    p.terminate()
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(b''.join(frames))
    print("✅ 녹음 완료")

def extract_main_content(text: str) -> str:
    """답변 포맷(설명/해결/응급단계)이 있을 경우 핵심만 추출해서 음성으로 읽기 좋게 정리."""
    설명 = re.search(r"⚠️ 설명:\n(.+?)\n\n", text, re.DOTALL)
    해결 = re.search(r"🛠 해결 방법:\n(.+)$", text, re.DOTALL)
    응급 = re.search(r"🧭 응급조치 단계:\n(.+)$", text, re.DOTALL)
    if 설명 or 해결:
        parts = []
        if 설명: parts.append(설명.group(1).strip())
        if 해결: parts.append(해결.group(1).strip())
        return "\n".join(parts)
    elif 응급:
        return 응급.group(1).strip()
    return text

def speak_text(text: str):
    """gTTS로 음성 재생"""
    tts = gTTS(text=text, lang='ko')
    tts.save("response.mp3")
    playsound("response.mp3")

# -------------------- 차량용품 키워드 & 링크 --------------------
def detect_accessory_keyword(text: str):
    """질문에서 차량용품 관련 키워드 감지"""
    kw_map = {
        "타이어": ["타이어", "스노우타이어", "휠", "공기압"],
        "엔진오일": ["엔진오일", "오일", "오일필터"],
        "와이퍼": ["와이퍼", "와이퍼블레이드"],
        "배터리": ["배터리", "축전지"],
        "블랙박스": ["블랙박스", "대시캠"],
        "네비게이션": ["네비", "네비게이션", "내비"],
        "에어필터": ["에어필터", "캐빈필터", "공조필터", "에어컨필터"],
        "체인": ["체인", "스노우체인"],
        "세차용품": ["세차", "왁스", "광택", "폼건", "워시"],
        "방향제": ["방향제", "탈취"],
        "충전기": ["충전기", "시거잭", "USB충전기", "usb 충전기"],
        # 필요 시 계속 추가
    }
    lower = text.lower()
    for key, alts in kw_map.items():
        for alt in alts:
            if alt in text or alt.lower() in lower:
                return key
    return None

def build_naver_shopping_link(keyword: str, car_model: str | None = None) -> str:
    query = f"{car_model} {keyword}" if car_model else keyword
    return f"https://search.shopping.naver.com/search/all?query={quote(query)}"

# -------------------- 메인 로직 --------------------
def transcribe_and_answer(filename="temp.wav", car_model: str = DEFAULT_CAR_MODEL):
    client = speech.SpeechClient()
    with open(filename, 'rb') as f:
        audio_bytes = f.read()

    audio = speech.RecognitionAudio(content=audio_bytes)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=SAMPLE_RATE,
        language_code="ko-KR",
    )

    response = client.recognize(config=config, audio=audio)

    for result in response.results:
        question = result.alternatives[0].transcript
        print(f"🧠 인식된 질문: {question}")

        # 1) DB에서 우선 답변 찾기
        answer = find_voice_answer(question)

        # 2) 없으면 GPT로 보완
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

        # 3) 차량용품 키워드면 네이버 쇼핑 링크 추가/대체
        keyword = detect_accessory_keyword(question)
        if keyword:
            link = build_naver_shopping_link(keyword, car_model)
            if ACCESSORY_LINK_ONLY:
                answer = f"{keyword} 관련 네이버 쇼핑 링크입니다:\n{link}"
            else:
                answer = f"{answer}\n\n🛒 관련 용품 쇼핑: {link}"

        # 4) 출력 + 음성 재생(링크는 음성에서 제거) + 저장
        print(answer)
        spoken = extract_main_content(answer)
        spoken = re.sub(r"https?://\S+", "", spoken)  # 음성에서는 URL 제거
        speak_text(spoken)

        save_voice_answer(question, answer, car_model)
        print("✅ 질문과 답변 저장 완료")

# -------------------- 실행 --------------------
if __name__ == "__main__":
    print("🎧 음성 기반 차량 AI 비서 (DB 우선 + GPT 보완 + 네이버 쇼핑 링크)\n")
    print(f"🚗 기본 차량 모델: {DEFAULT_CAR_MODEL}")
    record_audio()               # 5초 녹음
    transcribe_and_answer()      # 음성 인식 → 답변 생성/재생/저장
