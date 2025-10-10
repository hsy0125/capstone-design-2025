# api.py  — 텍스트/음성 모두 지원 (public 내부 모듈만 사용)
from __future__ import annotations
from typing import Optional
import os, sys, io, contextlib, builtins

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ----------------- public 폴더 import 경로 추가 -----------------
PUBLIC_DIR = os.path.join(os.path.dirname(__file__), "public")
if PUBLIC_DIR not in sys.path:
    sys.path.insert(0, PUBLIC_DIR)

def _safe_import(name):
    try:
        return __import__(name)   # e.g. "ask_rag" -> public/ask_rag.py
    except Exception as e:
        print(f"[IMPORT FAIL] {name}: {e}")
        return None

rag_mod   = _safe_import("ask_rag")       # ask_with_db_context(q, car)
ask_mod   = _safe_import("ask")           # ask_question(q)  (시그니처 1개 기준)
voice_mod = _safe_import("test_voice_2")  # (참고용 import, 직접 로직은 아래 STT 사용)

# ----------------- 유틸: print/입력 방어 + stdout 캡처 -----------------
def _call_and_capture(func, *args, **kwargs) -> Optional[str]:
    """return이 없고 print만 하는 함수도 stdout을 문자열로 회수.
       내부에서 input()을 호출하면 'n'으로 자동응답해 서버가 멈추지 않게 함."""
    if not callable(func):
        return None
    buf = io.StringIO()
    orig_input = builtins.input
    try:
        builtins.input = lambda *a, **k: "n"
        with contextlib.redirect_stdout(buf):
            res = func(*args, **kwargs)
    except Exception as e:
        return f"(내부 오류) {e}"
    finally:
        builtins.input = orig_input
    text = res if isinstance(res, str) else buf.getvalue()
    text = (text or "").strip()
    return text or None

def _to_text(x) -> Optional[str]:
    if x is None: return None
    s = str(x).strip()
    return s or None

# ----------------- STT: Google Speech (webm/ogg/wav 대응) -----------------
def stt_from_bytes(raw: bytes, content_type: str = "", language: str = "ko-KR") -> Optional[str]:
    """
    브라우저 녹음(webm/ogg/pcm wav)을 그대로 Google Speech로 인식.
    content_type 예: 'audio/webm', 'audio/ogg', 'audio/wav'
    """
    try:
        from google.cloud import speech
    except Exception as e:
        print("[STT] google-cloud-speech import 실패:", e)
        return None

    # .env의 GOOGLE_APPLICATION_CREDENTIALS 적용
    try:
        from dotenv import load_dotenv
        load_dotenv()
        cred = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if cred:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred
    except Exception:
        pass

    ct = (content_type or "").lower()
    encoding = None
    sr = None          # ⚠️ OPUS 계열은 샘플레이트 '지정하지 않음'이 안전

    if "ogg" in ct:
        encoding = speech.RecognitionConfig.AudioEncoding.OGG_OPUS
        # sr = 48000  # 지정하지 않음
    elif "webm" in ct:
        # 버전에 따라 WEBM_OPUS가 없을 수 있음
        encoding = getattr(speech.RecognitionConfig.AudioEncoding, "WEBM_OPUS", None)
        if encoding is None:
            # 라이브러리가 WEBM_OPUS를 모르면, 프론트에서 OGG로 보내게 하는 게 정답.
            print("[STT] WEBM_OPUS 미지원 → OGG 사용 권장 (프론트에서 audio/ogg로 녹음하도록 설정).")
            return None
        # sr = 48000  # 지정하지 않음
    elif "wav" in ct or "x-wav" in ct or "wave" in ct:
        encoding = speech.RecognitionConfig.AudioEncoding.LINEAR16
        sr = 16000  # WAV(PCM)일 때만 지정
    else:
        # 모르면 OGG_OPUS로 가정
        encoding = speech.RecognitionConfig.AudioEncoding.OGG_OPUS

    try:
        client = speech.SpeechClient()
        audio = speech.RecognitionAudio(content=raw)

        # ⚠️ OPUS 계열(OGG/WEBM)은 sample_rate_hertz를 넘기지 않는다.
        cfg_kwargs = dict(
            encoding=encoding,
            language_code=language,
            enable_automatic_punctuation=True,
        )
        if sr is not None:
            cfg_kwargs["sample_rate_hertz"] = sr

        config = speech.RecognitionConfig(**cfg_kwargs)
        print(f"[STT] content_type={ct}, encoding={encoding}, sr={sr}")

        resp = client.recognize(config=config, audio=audio)
        texts = [r.alternatives[0].transcript for r in resp.results if r.alternatives]
        return (" ".join(texts)).strip() if texts else None
    except Exception as e:
        print("[STT] 인식 실패:", e)
        return None

# ----------------- FastAPI -----------------
app = FastAPI(title="Capstone Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

class AskReq(BaseModel):
    question: str
    carModel: Optional[str] = None

class AskRes(BaseModel):
    answer: str
    carModel: Optional[str] = None

@app.get("/api/ping")
def ping():
    return {"ok": True}

# ---------- 텍스트 → 답변 ----------
@app.post("/api/ask", response_model=AskRes)
def ask_text(req: AskReq):
    car = req.carModel or "DEFAULT"
    ans = None

    # 1) RAG 우선
    if rag_mod and hasattr(rag_mod, "ask_with_db_context"):
        ans = _to_text(_call_and_capture(rag_mod.ask_with_db_context, req.question, car))

    # 2) 실패 시 기본 질의
    if ans is None and ask_mod and hasattr(ask_mod, "ask_question"):
        # ask_question 이 (q) 또는 (q, car_model) 중 무엇을 받든 캡처로 커버
        ans = _to_text(_call_and_capture(ask_mod.ask_question, req.question))

    # 3) 폴백
    if ans is None:
        ans = f"(임시) 질문을 받았어요: {req.question}"

    return AskRes(answer=ans, carModel=car)

# ---------- 음성(STT) → 텍스트 → 답변 ----------
@app.post("/api/voice")
async def voice(file: UploadFile = File(...), carModel: Optional[str] = None):
    raw = await file.read()
    ct  = file.content_type or ""
    text = stt_from_bytes(raw, ct)  # WEBM/OGG/WAV 자동 대응

    if not text:
        text = "(음성 인식 실패: 파일 형식/자격증명을 확인하세요)"

    data = ask_text(AskReq(question=text, carModel=carModel))
    return {"text": text, "answer": data.answer, "carModel": data.carModel}
