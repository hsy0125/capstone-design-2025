# # api.py  — 텍스트/음성 모두 지원 (public 내부 모듈만 사용)
# import base64
# from io import BytesIO
# from gtts import gTTS
# from urllib.parse import quote      #추가함

# # from __future__ import annotations
# from typing import Optional
# import os, sys, io, contextlib, builtins

# from fastapi import FastAPI, UploadFile, File
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel

# import re

# # ----------------- public 폴더 import 경로 추가 -----------------
# PUBLIC_DIR = os.path.join(os.path.dirname(__file__), "public")
# if PUBLIC_DIR not in sys.path:
#     sys.path.insert(0, PUBLIC_DIR)

# def _safe_import(name):
#     try:
#         return __import__(name)   # e.g. "ask_rag" -> public/ask_rag.py
#     except Exception as e:
#         print(f"[IMPORT FAIL] {name}: {e}")
#         return None

# rag_mod   = _safe_import("ask_rag")       # ask_with_db_context(q, car)
# ask_mod   = _safe_import("ask")           # ask_question(q)  (시그니처 1개 기준)
# voice_mod = _safe_import("test_voice_2")  # (참고용 import, 직접 로직은 아래 STT 사용)

# # ----------------- 유틸: print/입력 방어 + stdout 캡처 -----------------
# def _call_and_capture(func, *args, **kwargs) -> Optional[str]:
#     """return이 없고 print만 하는 함수도 stdout을 문자열로 회수.
#        내부에서 input()을 호출하면 'n'으로 자동응답해 서버가 멈추지 않게 함."""
#     if not callable(func):
#         return None
#     buf = io.StringIO()
#     orig_input = builtins.input
#     try:
#         builtins.input = lambda *a, **k: "n"
#         with contextlib.redirect_stdout(buf):
#             res = func(*args, **kwargs)
#     except Exception as e:
#         return f"(내부 오류) {e}"
#     finally:
#         builtins.input = orig_input
#     text = res if isinstance(res, str) else buf.getvalue()
#     text = (text or "").strip()
#     return text or None

# def _to_text(x) -> Optional[str]:
#     if x is None: return None
#     s = str(x).strip()
#     return s or None

# # ----------------- STT: Google Speech (webm/ogg/wav 대응) -----------------
# def stt_from_bytes(raw: bytes, content_type: str = "", language: str = "ko-KR") -> Optional[str]:
#     """
#     브라우저 녹음(webm/ogg/pcm wav)을 그대로 Google Speech로 인식.
#     content_type 예: 'audio/webm', 'audio/ogg', 'audio/wav'
#     """
#     try:
#         from google.cloud import speech
#     except Exception as e:
#         print("[STT] google-cloud-speech import 실패:", e)
#         return None

#     # .env의 GOOGLE_APPLICATION_CREDENTIALS 적용
#     try:
#         from dotenv import load_dotenv
#         load_dotenv()
#         cred = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
#         if cred:
#             os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred
#     except Exception:
#         pass

#     ct = (content_type or "").lower()
#     encoding = None
#     sr = None          # ⚠️ OPUS 계열은 샘플레이트 '지정하지 않음'이 안전

#     if "ogg" in ct:
#         encoding = speech.RecognitionConfig.AudioEncoding.OGG_OPUS
#         # sr = 48000  # 지정하지 않음
#     elif "webm" in ct:
#         # 버전에 따라 WEBM_OPUS가 없을 수 있음
#         encoding = getattr(speech.RecognitionConfig.AudioEncoding, "WEBM_OPUS", None)
#         if encoding is None:
#             # 라이브러리가 WEBM_OPUS를 모르면, 프론트에서 OGG로 보내게 하는 게 정답.
#             print("[STT] WEBM_OPUS 미지원 → OGG 사용 권장 (프론트에서 audio/ogg로 녹음하도록 설정).")
#             return None
#         # sr = 48000  # 지정하지 않음
#     elif "wav" in ct or "x-wav" in ct or "wave" in ct:
#         encoding = speech.RecognitionConfig.AudioEncoding.LINEAR16
#         sr = 16000  # WAV(PCM)일 때만 지정
#     else:
#         # 모르면 OGG_OPUS로 가정
#         encoding = speech.RecognitionConfig.AudioEncoding.OGG_OPUS

#     try:
#         client = speech.SpeechClient()
#         audio = speech.RecognitionAudio(content=raw)

#         # ⚠️ OPUS 계열(OGG/WEBM)은 sample_rate_hertz를 넘기지 않는다.
#         cfg_kwargs = dict(
#             encoding=encoding,
#             language_code=language,
#             enable_automatic_punctuation=True,
#         )
#         if sr is not None:
#             cfg_kwargs["sample_rate_hertz"] = sr

#         config = speech.RecognitionConfig(**cfg_kwargs)
#         print(f"[STT] content_type={ct}, encoding={encoding}, sr={sr}")

#         resp = client.recognize(config=config, audio=audio)
#         texts = [r.alternatives[0].transcript for r in resp.results if r.alternatives]
#         return (" ".join(texts)).strip() if texts else None
#     except Exception as e:
#         print("[STT] 인식 실패:", e)
#         return None

# def detect_accessory_keyword(text: str):
#     kw_map = {
#         "타이어": ["타이어", "스노우타이어", "휠", "공기압"],
#         "엔진오일": ["엔진오일", "오일", "오일필터"],
#         "와이퍼": ["와이퍼", "와이퍼블레이드"],
#         "배터리": ["배터리", "축전지"],
#         "블랙박스": ["블랙박스", "대시캠"],
#         "네비게이션": ["네비", "네비게이션", "내비"],
#         "에어필터": ["에어필터", "캐빈필터", "공조필터", "에어컨필터"],
#         "체인": ["체인", "스노우체인"],
#         "세차용품": ["세차", "왁스", "광택", "폼건", "워시"],
#         "방향제": ["방향제", "탈취"],
#         "충전기": ["충전기", "시거잭", "USB충전기", "usb 충전기"],
#     }
#     lower = text.lower()
#     for key, alts in kw_map.items():
#         for alt in alts:
#             if alt in text or alt.lower() in lower:
#                 return key
#     return None

# def build_naver_shopping_link(keyword: str, car_model: str | None = None):
#     query = f"{car_model} {keyword}" if car_model else keyword
#     return f"https://search.shopping.naver.com/search/all?query={quote(query)}"


# # ----------------- FastAPI -----------------
# app = FastAPI(title="Capstone Backend")
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
#     allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
# )

# class AskReq(BaseModel):
#     question: str
#     carModel: Optional[str] = None

# class AskRes(BaseModel):
#     answer: str
#     carModel: Optional[str] = None

# @app.get("/api/ping")
# def ping():
#     return {"ok": True}

# # ---------- 텍스트 → 답변 ----------
# @app.post("/api/ask")
# def ask_text(req: AskReq):
#     car = req.carModel or "DEFAULT"
#     ans = None

#     # 1) RAG 우선
#     if rag_mod and hasattr(rag_mod, "ask_with_db_context"):
#         ans = _to_text(_call_and_capture(rag_mod.ask_with_db_context, req.question, car))

#     # 2) 실패 시 기본 LLM 질의
#     if ans is None and ask_mod and hasattr(ask_mod, "ask_question"):
#         ans = _to_text(_call_and_capture(ask_mod.ask_question, req.question))

#     # 3) 폴백
#     if ans is None:
#         ans = f"(임시) 질문을 받았어요: {req.question}"

#     # ---------- 차량용품 키워드 감지 ----------
#     keyword = detect_accessory_keyword(req.question)
#     if keyword:
#         link = build_naver_shopping_link(keyword, car)
#         ans += f"\n\n🛒 관련 용품 쇼핑 링크: {link}"

#     # ----- TTS는 쇼핑 링크 제거 -----
#     tts_text = ans.split("🛒")[0].strip()

#     # 2) 링크(URL) 제거
#     tts_text = re.sub(r"https?://\S+", "", tts_text)

#     # 3) 아이콘/이모지 제거
#     tts_text = re.sub(r"[^\w\s가-힣.,!?]", "", tts_text)

#     # 4) 빈 칸 정리
#     tts_text = tts_text.strip()  

#     # ---------- TTS 음성 생성 ----------
#     audio_b64 = None
#     try:
#         tts = gTTS(text=tts_text, lang='ko')
#         buf = BytesIO()
#         tts.write_to_fp(buf)
#         buf.seek(0)
#         audio_b64 = base64.b64encode(buf.read()).decode("ascii")
#     except Exception as e:
#         print("[ASK TTS 생성 오류]:", e)

#     # ---------- 텍스트 + 음성 반환 ----------
#     return {
#         "answer": ans,
#         "carModel": car,
#         "audio": audio_b64,   # ← Chat.jsx에서 재생하는 용도
#     }

# # ---------- 음성(STT) → 텍스트 → 답변 ----------
# @app.post("/api/voice")
# async def voice(file: UploadFile = File(...), carModel: Optional[str] = None):
#     raw = await file.read()
#     ct = file.content_type or ""
#     text = stt_from_bytes(raw, ct)

#     if not text:
#         text = "(음성 인식 실패: STT 변환 실패)"

#     # ask_text 는 dict 반환
#     data = ask_text(AskReq(question=text, carModel=carModel))
#     answer = data["answer"]

#     # -------------------------
#     # 🔊 TTS: 쇼핑 링크/아이콘 제거
#     # -------------------------
#     import re

#     # 1) 쇼핑 링크 아이콘 뒤 내용 제거
#     tts_text = answer.split("🛒")[0].strip()

#     # 2) URL 제거
#     tts_text = re.sub(r"https?://\S+", "", tts_text)

#     # 3) 이모지/아이콘 제거
#     tts_text = re.sub(r"[^\w\s가-힣.,!?]", "", tts_text)

#     # 4) 공백 정리
#     tts_text = tts_text.strip()

#     # -------------------------
#     # gTTS 생성
#     # -------------------------
#     audio_b64 = None
#     try:
#         tts = gTTS(text=tts_text, lang='ko')
#         buf = BytesIO()
#         tts.write_to_fp(buf)
#         buf.seek(0)
#         audio_b64 = base64.b64encode(buf.read()).decode("ascii")
#     except Exception as e:
#         print("[VOICE TTS 생성 오류]:", e)

#     # -------------------------
#     # 반환
#     # -------------------------
#     return {
#         "text": text,
#         "answer": answer,
#         "carModel": data["carModel"],
#         "audio": audio_b64
#     }

# # ================================================================
# # api.py — 텍스트/음성 + 차량 RAG + Google STT + gTTS + 알람모드
# # ================================================================


# # -------------------- 알람 모델 --------------------
# from fastapi import BackgroundTasks
# import psycopg2
# import psycopg2.extras
# from datetime import datetime, timezone

# DB_URL = os.getenv("DATABASE_URL")

# def db():
#     conn = psycopg2.connect(DB_URL)
#     return conn

# # -------------------------------------------------------
# # 1) 알람 생성
# # -------------------------------------------------------
# class AlarmReq(BaseModel):
#     session_id: str
#     message: str
#     scheduled_at: str  # ISO string

# @app.post("/api/alarm/create")
# def create_alarm(req: AlarmReq):
#     conn = db()
#     cur = conn.cursor()

#     cur.execute("""
#         INSERT INTO alarms(session_id, message, scheduled_at)
#         VALUES (%s, %s, %s)
#         RETURNING id
#     """, (req.session_id, req.message, req.scheduled_at))

#     alarm_id = cur.fetchone()[0]
#     conn.commit()

#     return {"ok": True, "id": alarm_id}

# # -------------------------------------------------------
# # 2) 세션 알람 목록 조회
# # -------------------------------------------------------
# @app.get("/api/alarms")
# def list_alarms(session_id: str):
#     conn = db()
#     cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
#     cur.execute("""
#         SELECT * FROM alarms
#         WHERE session_id=%s
#         ORDER BY scheduled_at ASC
#     """, (session_id,))
#     rows = cur.fetchall()
#     return rows

# # -------------------------------------------------------
# # 3) 알람 삭제
# # -------------------------------------------------------
# @app.delete("/api/alarm/{alarm_id}")
# def delete_alarm(alarm_id: int):
#     conn = db()
#     cur = conn.cursor()
#     cur.execute("DELETE FROM alarms WHERE id=%s", (alarm_id,))
#     conn.commit()
#     return {"ok": True}

# # -------------------------------------------------------
# # 4) 알람 체크 (프론트용 폴링)
# # -------------------------------------------------------
# @app.get("/api/alarm/pending")
# def check_alarm(session_id: str):
#     now = datetime.now(timezone.utc)

#     conn = db()
#     cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

#     cur.execute("""
#         SELECT * FROM alarms
#         WHERE session_id=%s
#         AND fired = FALSE
#         AND scheduled_at <= %s
#         ORDER BY scheduled_at ASC
#         LIMIT 1
#     """, (session_id, now))

#     row = cur.fetchone()
#     if not row:
#         return {"alarm": None}

#     # fired=true로 변경
#     cur.execute("UPDATE alarms SET fired=TRUE WHERE id=%s", (row["id"],))
#     conn.commit()

#     return {"alarm": row}


# ============================================================
#  api.py — 차량용 AI + RAG + Google STT + gTTS + 알람 기능 통합본
# ============================================================

# import base64
# import os, sys, io, contextlib, builtins, re
# from io import BytesIO
# from typing import Optional
# from datetime import datetime, timezone, timedelta

# from fastapi import FastAPI, UploadFile, File
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from gtts import gTTS
# from urllib.parse import quote

# # ============================================================
# #  public 폴더 import
# # ============================================================
# PUBLIC_DIR = os.path.join(os.path.dirname(__file__), "public")
# if PUBLIC_DIR not in sys.path:
#     sys.path.insert(0, PUBLIC_DIR)

# def _safe_import(name):
#     try:
#         return __import__(name)
#     except Exception as e:
#         print(f"[IMPORT FAIL] {name}: {e}")
#         return None

# rag_mod   = _safe_import("ask_rag")
# ask_mod   = _safe_import("ask")
# voice_mod = _safe_import("test_voice_2")

# # ============================================================
# #  유틸: stdout capture
# # ============================================================
# def _call_and_capture(func, *args, **kwargs) -> Optional[str]:
#     if not callable(func): return None
#     buf = io.StringIO()
#     orig_input = builtins.input
#     try:
#         builtins.input = lambda *a, **k: "n"
#         with contextlib.redirect_stdout(buf):
#             res = func(*args, **kwargs)
#     except Exception as e:
#         return f"(내부 오류) {e}"
#     finally:
#         builtins.input = orig_input

#     text = res if isinstance(res, str) else buf.getvalue()
#     return (text or "").strip() or None

# def _to_text(x) -> Optional[str]:
#     if x is None: return None
#     return str(x).strip() or None


# # ============================================================
# #  Google STT
# # ============================================================
# def stt_from_bytes(raw: bytes, content_type: str = "", language="ko-KR") -> Optional[str]:
#     try:
#         from google.cloud import speech
#     except Exception as e:
#         print("[STT] import error:", e)
#         return None

#     # GOOGLE_APPLICATION_CREDENTIALS 자동 적용 (.env)
#     try:
#         from dotenv import load_dotenv
#         load_dotenv()
#         cred = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
#         if cred:
#             os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred
#     except:
#         pass

#     ct = (content_type or "").lower()

#     encoding = None
#     sr = None

#     if "ogg" in ct:
#         encoding = speech.RecognitionConfig.AudioEncoding.OGG_OPUS
#     elif "webm" in ct:
#         encoding = getattr(speech.RecognitionConfig.AudioEncoding, "WEBM_OPUS", None)
#         if encoding is None:
#             print("[STT] WEBM_OPUS 미지원 → 프론트에서 audio/ogg 권장.")
#             return None
#     elif "wav" in ct:
#         encoding = speech.RecognitionConfig.AudioEncoding.LINEAR16
#         sr = 16000
#     else:
#         encoding = speech.RecognitionConfig.AudioEncoding.OGG_OPUS

#     try:
#         client = speech.SpeechClient()
#         audio = speech.RecognitionAudio(content=raw)

#         cfg = dict(
#             encoding=encoding,
#             language_code=language,
#             enable_automatic_punctuation=True,
#         )
#         if sr:
#             cfg["sample_rate_hertz"] = sr

#         config = speech.RecognitionConfig(**cfg)

#         resp = client.recognize(config=config, audio=audio)
#         texts = [
#             r.alternatives[0].transcript
#             for r in resp.results if r.alternatives
#         ]
#         return (" ".join(texts)).strip() if texts else None

#     except Exception as e:
#         print("[STT 실패]", e)
#         return None


# # ============================================================
# #  차량용품 키워드 감지
# # ============================================================
# def detect_accessory_keyword(text: str):
#     kw_map = {
#         "타이어": ["타이어", "스노우타이어", "휠", "공기압"],
#         "엔진오일": ["엔진오일", "오일", "오일필터"],
#         "와이퍼": ["와이퍼"],
#         "배터리": ["배터리"],
#         "블랙박스": ["블랙박스"],
#         "네비게이션": ["네비"],
#         "에어필터": ["에어필터", "캐빈필터"],
#         "체인": ["체인"],
#         "세차용품": ["세차"],
#         "방향제": ["방향제"],
#         "충전기": ["충전기"],
#     }
#     lower = text.lower()
#     for k, arr in kw_map.items():
#         for a in arr:
#             if a in text or a.lower() in lower:
#                 return k
#     return None

# def build_naver_shopping_link(keyword, car):
#     q = f"{car} {keyword}" if car else keyword
#     return f"https://search.shopping.naver.com/search/all?query={quote(q)}"


# # ============================================================
# #  FastAPI 기본 설정
# # ============================================================
# app = FastAPI(title="Capstone Backend")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
#     allow_methods=["*"],
#     allow_headers=["*"],
#     allow_credentials=True,
# )


# @app.get("/api/ping")
# def ping():
#     return {"ok": True}


# # ============================================================
# #  자연어 → 알람 시간 파싱
# # ============================================================
# def parse_alarm_time(text: str):
#     now = datetime.now(timezone.utc)

#     m = re.search(r"(\d+)\s*분\s*뒤", text)
#     if m:
#         return now + timedelta(minutes=int(m.group(1)))

#     m = re.search(r"(\d+)\s*시간\s*뒤", text)
#     if m:
#         return now + timedelta(hours=int(m.group(1)))

#     return None


# # ============================================================
# #  Ask 모델
# # ============================================================
# class AskReq(BaseModel):
#     question: str
#     carModel: Optional[str] = None


# # ============================================================
# #  DB 연결 (알람 기능)
# # ============================================================
# import psycopg2
# import psycopg2.extras

# DB_URL = os.getenv("DATABASE_URL")

# def db():
#     return psycopg2.connect(DB_URL)


# # ============================================================
# #  ask_text() — 자연어 알람 + RAG + TTS 통합
# # ============================================================
# @app.post("/api/ask")
# def ask_text(req: AskReq):
#     question = req.question
#     car = req.carModel or "DEFAULT"

#     # ----------------------------
#     # 1) 자연어 알람 인식
#     # ----------------------------
#     if "알람" in question:
#         alarm_at = parse_alarm_time(question)

#         if alarm_at:
#             try:
#                 conn = db()
#                 cur = conn.cursor()
#                 cur.execute("""
#                     INSERT INTO alarms(session_id, message, scheduled_at)
#                     VALUES (%s, %s, %s)
#                 """, ("demo-session", question, alarm_at))
#                 conn.commit()
#                 print("[ALARM 저장]", alarm_at)
#             except Exception as e:
#                 print("[ALARM ERROR]", e)

#             local_t = alarm_at.astimezone().strftime("%H시 %M분")
#             ans = f"{local_t}에 알람을 설정했습니다."

#             # TTS 생성
#             audio_b64 = None
#             try:
#                 tts = gTTS(text=ans, lang='ko')
#                 buf = BytesIO()
#                 tts.write_to_fp(buf)
#                 buf.seek(0)
#                 audio_b64 = base64.b64encode(buf.read()).decode()
#             except:
#                 pass

#             return {
#                 "answer": ans,
#                 "carModel": car,
#                 "audio": audio_b64
#             }

#     # ----------------------------
#     # 2) 일반 질의 응답 (RAG → ask)
#     # ----------------------------
#     ans = None

#     if rag_mod and hasattr(rag_mod, "ask_with_db_context"):
#         ans = _to_text(_call_and_capture(rag_mod.ask_with_db_context, question, car))

#     if ans is None and ask_mod and hasattr(ask_mod, "ask_question"):
#         ans = _to_text(_call_and_capture(ask_mod.ask_question, question))

#     if ans is None:
#         ans = f"(임시 응답) 질문을 받았습니다: {question}"

#     # ----------------------------
#     # 3) 차량 액세서리 추천
#     # ----------------------------
#     kw = detect_accessory_keyword(question)
#     if kw:
#         link = build_naver_shopping_link(kw, car)
#         ans += f"\n\n🛒 관련 용품 링크: {link}"

#     # ----------------------------
#     # 4) TTS 텍스트 정제
#     # ----------------------------
#     tts_text = ans.split("🛒")[0].strip()
#     tts_text = re.sub(r"https?://\S+", "", tts_text)
#     tts_text = re.sub(r"[^\w\s가-힣.,!?]", "", tts_text)
#     tts_text = tts_text.strip()

#     # ----------------------------
#     # 5) TTS 생성
#     # ----------------------------
#     audio_b64 = None
#     try:
#         tts = gTTS(text=tts_text, lang='ko')
#         buf = BytesIO()
#         tts.write_to_fp(buf)
#         buf.seek(0)
#         audio_b64 = base64.b64encode(buf.read()).decode()
#     except:
#         pass

#     return {
#         "answer": ans,
#         "carModel": car,
#         "audio": audio_b64
#     }


# # ============================================================
# #  /api/voice — 음성(STT) → ask_text()
# # ============================================================
# @app.post("/api/voice")
# async def voice(file: UploadFile = File(...), carModel: Optional[str] = None):
#     raw = await file.read()
#     text = stt_from_bytes(raw, file.content_type)

#     if not text:
#         text = "(음성 인식 실패)"

#     data = ask_text(AskReq(question=text, carModel=carModel))
#     return {
#         "text": text,
#         "answer": data["answer"],
#         "carModel": data["carModel"],
#         "audio": data["audio"]
#     }


# # ============================================================
# #  알람 API (프론트 폴링용)
# # ============================================================
# class AlarmReq(BaseModel):
#     session_id: str
#     message: str
#     scheduled_at: str


# @app.post("/api/alarm/create")
# def create_alarm(req: AlarmReq):
#     conn = db()
#     cur = conn.cursor()
#     cur.execute("""
#         INSERT INTO alarms(session_id, message, scheduled_at)
#         VALUES (%s, %s, %s)
#         RETURNING id
#     """, (req.session_id, req.message, req.scheduled_at))
#     alarm_id = cur.fetchone()[0]
#     conn.commit()
#     return {"ok": True, "id": alarm_id}


# @app.get("/api/alarms")
# def list_alarms(session_id: str):
#     conn = db()
#     cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
#     cur.execute("""
#         SELECT * FROM alarms
#         WHERE session_id=%s
#         ORDER BY scheduled_at ASC
#     """, (session_id,))
#     return cur.fetchall()


# @app.delete("/api/alarm/{alarm_id}")
# def delete_alarm(alarm_id: int):
#     conn = db()
#     cur = conn.cursor()
#     cur.execute("DELETE FROM alarms WHERE id=%s", (alarm_id,))
#     conn.commit()
#     return {"ok": True}


# @app.get("/api/alarm/pending")
# def check_alarm(session_id: str):
#     now = datetime.now(timezone.utc)

#     conn = db()
#     cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

#     cur.execute("""
#         SELECT * FROM alarms
#         WHERE session_id=%s
#         AND fired = FALSE
#         AND scheduled_at <= %s
#         ORDER BY scheduled_at ASC
#         LIMIT 1
#     """, (session_id, now))

#     row = cur.fetchone()
#     if not row:
#         return {"alarm": None}

#     cur.execute("UPDATE alarms SET fired=TRUE WHERE id=%s", (row["id"],))
#     conn.commit()

#     return {"alarm": row}


# ============================================================
#  api.py — 텍스트/음성 + 차량용 RAG + Google STT + gTTS + 알람 기능 통합본
# ============================================================

import base64
import os, sys, io, contextlib, builtins, re
from io import BytesIO
from typing import Optional
from datetime import datetime, timezone, timedelta

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from gtts import gTTS
from urllib.parse import quote

# ============================================================
#  public 폴더 import
# ============================================================
PUBLIC_DIR = os.path.join(os.path.dirname(__file__), "public")
if PUBLIC_DIR not in sys.path:
    sys.path.insert(0, PUBLIC_DIR)

def _safe_import(name):
    try:
        return __import__(name)
    except Exception as e:
        print(f"[IMPORT FAIL] {name}: {e}")
        return None

rag_mod   = _safe_import("ask_rag")
ask_mod   = _safe_import("ask")
voice_mod = _safe_import("test_voice_2")

# ============================================================
#  유틸: STDOUT 캡처
# ============================================================
def _call_and_capture(func, *args, **kwargs) -> Optional[str]:
    if not callable(func): return None
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
    return (text or "").strip() or None


# ============================================================
#  Google STT
# ============================================================
def stt_from_bytes(raw: bytes, content_type: str = "", language="ko-KR"):
    try:
        from google.cloud import speech
    except:
        print("[STT] google-cloud-speech import 실패")
        return None

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except:
        pass

    ct = (content_type or "").lower()
    encoding = None
    sr = None

    from google.cloud import speech
    if "ogg" in ct:
        encoding = speech.RecognitionConfig.AudioEncoding.OGG_OPUS
    elif "webm" in ct:
        encoding = getattr(speech.RecognitionConfig.AudioEncoding, "WEBM_OPUS", None)
        if encoding is None:
            return None
    elif "wav" in ct:
        encoding = speech.RecognitionConfig.AudioEncoding.LINEAR16
        sr = 16000
    else:
        encoding = speech.RecognitionConfig.AudioEncoding.OGG_OPUS

    try:
        client = speech.SpeechClient()
        audio = speech.RecognitionAudio(content=raw)

        cfg = dict(
            encoding=encoding,
            language_code=language,
            enable_automatic_punctuation=True
        )
        if sr:
            cfg["sample_rate_hertz"] = sr

        config = speech.RecognitionConfig(**cfg)
        resp = client.recognize(config=config, audio=audio)
        texts = [
            r.alternatives[0].transcript
            for r in resp.results if r.alternatives
        ]

        return (" ".join(texts)).strip() if texts else None
    except Exception as e:
        print("[STT 오류]", e)
        return None


# ============================================================
#  차량용품 키워드 감지
# ============================================================
def detect_accessory_keyword(text: str):
    kw_map = {
        "타이어": ["타이어", "스노우타이어", "공기압"],
        "엔진오일": ["엔진오일"],
        "와이퍼": ["와이퍼"],
        "배터리": ["배터리"],
        "블랙박스": ["블랙박스"],
        "네비게이션": ["네비"],
        "에어필터": ["에어필터", "캐빈필터"],
        "체인": ["체인"],
        "세차용품": ["세차"],
        "방향제": ["방향제"],
        "충전기": ["충전기"],
    }
    lower = text.lower()
    for k, arr in kw_map.items():
        for a in arr:
            if a in text or a.lower() in lower:
                return k
    return None


def build_naver_shopping_link(keyword, car):
    q = f"{car} {keyword}" if car else keyword
    return f"https://search.shopping.naver.com/search/all?query={quote(q)}"


# ============================================================
#  FastAPI 설정
# ============================================================
app = FastAPI(title="Capstone Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)


# ============================================================
#  자연어 → 알람 시간 파싱
# ============================================================
def parse_alarm_time(text: str):
    raw = text
    no_space = raw.replace(" ", "")
    now = datetime.now()   # ✅ timezone 없이 로컬 시간

    # --------------------------------------
    # 상대시간
    # --------------------------------------
    m = re.search(r"(\d+)\s*분\s*뒤", raw)
    if m:
        return now + timedelta(minutes=int(m.group(1)))

    m = re.search(r"(\d+)\s*시간\s*뒤", raw)
    if m:
        return now + timedelta(hours=int(m.group(1)))

    # --------------------------------------
    # 절대시간 (오전/오후 포함)
    # --------------------------------------
    m = re.search(r"(오전|오후)\s*(\d+)\s*시\s*(\d*)\s*분?", raw)
    if m:
        ampm = m.group(1)
        hour = int(m.group(2))
        minute = int(m.group(3)) if m.group(3) else 0

        if ampm == "오후" and hour != 12:
            hour += 12
        if ampm == "오전" and hour == 12:
            hour = 0

        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        return target

    # --------------------------------------
    # 절대시간 (오전/오후 없음 → 24시간 기준)
    # --------------------------------------
    m = re.search(r"(\d+)\s*시\s*(\d*)\s*분?", raw)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2)) if m.group(2) else 0

        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        return target

    return None


# ============================================================
#  DB 연결
# ============================================================
import psycopg2
import psycopg2.extras

DB_URL = os.getenv("DATABASE_URL")

def db():
    return psycopg2.connect(DB_URL)


# ============================================================
#  AskReq 모델
# ============================================================
class AskReq(BaseModel):
    question: str
    carModel: Optional[str] = None


# ============================================================
#  ask_text — 알람 + RAG + 답변 + TTS
# ============================================================
@app.post("/api/ask")
def ask_text(req: AskReq):

    question_raw = req.question
    question = question_raw.strip()
    no_space = question.replace(" ", "")
    car = req.carModel or "DEFAULT"

    # -----------------------------------------
    # 1) 알람 문장인지 검사 (음성 문제 해결)
    # -----------------------------------------
    if ("알람" in question) or ("알람" in no_space):

        alarm_at = parse_alarm_time(question)
        if alarm_at:
            try:
                conn = db()
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO alarms(session_id, message, scheduled_at)
                    VALUES (%s, %s, %s)
                    """,
                    ("demo-session", question_raw, alarm_at)
                )
                conn.commit()
                print("[ALARM SAVED]", alarm_at)
            except Exception as e:
                print("[ALARM ERROR]", e)

            local_t = alarm_at.astimezone().strftime("%H시 %M분")
            ans = f"{local_t}에 알람을 설정했습니다."

            # TTS 생성
            audio_b64 = None
            try:
                tts = gTTS(text=ans, lang="ko")
                buf = BytesIO()
                tts.write_to_fp(buf)
                buf.seek(0)
                audio_b64 = base64.b64encode(buf.read()).decode()
            except:
                pass

            return {"answer": ans, "carModel": car, "audio": audio_b64}

    # -----------------------------------------
    # 2) 일반 질문 처리 (RAG → ask)
    # -----------------------------------------
    ans = None

    if rag_mod and hasattr(rag_mod, "ask_with_db_context"):
        ans = _call_and_capture(rag_mod.ask_with_db_context, question, car)

    if not ans and ask_mod and hasattr(ask_mod, "ask_question"):
        ans = _call_and_capture(ask_mod.ask_question, question)

    if not ans:
        ans = f"(임시응답) 질문을 받았습니다: {question}"

    # -----------------------------------------
    # 3) 차량용품 키워드
    # -----------------------------------------
    kw = detect_accessory_keyword(question)
    if kw:
        link = build_naver_shopping_link(kw, car)
        ans += f"\n\n🛒 관련 용품 링크: {link}"

    # -----------------------------------------
    # 4) TTS 정제
    # -----------------------------------------
    tts_text = ans.split("🛒")[0]
    tts_text = re.sub(r"https?://\S+", "", tts_text)
    tts_text = re.sub(r"[^\w\s가-힣.,!?]", "", tts_text).strip()

    audio_b64 = None
    try:
        tts = gTTS(text=tts_text, lang="ko")
        buf = BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        audio_b64 = base64.b64encode(buf.read()).decode()
    except:
        pass

    return {"answer": ans, "carModel": car, "audio": audio_b64}


# ============================================================
#  음성 → STT → ask_text
# ============================================================
@app.post("/api/voice")
async def voice(file: UploadFile = File(...), carModel: Optional[str] = None):

    raw = await file.read()
    text = stt_from_bytes(raw, file.content_type)

    if not text:
        text = "(음성인식 실패)"

    print("[STT RESULT]:", text)

    data = ask_text(AskReq(question=text, carModel=carModel))

    return {
        "text": text,
        "answer": data["answer"],
        "carModel": data["carModel"],
        "audio": data["audio"]
    }


# ============================================================
#  알람 관련 API
# ============================================================
class AlarmReq(BaseModel):
    session_id: str
    message: str
    scheduled_at: str


@app.post("/api/alarm/create")
def create_alarm(req: AlarmReq):
    conn = db()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO alarms(session_id, message, scheduled_at)
        VALUES (%s, %s, %s)
        RETURNING id
        """,
        (req.session_id, req.message, req.scheduled_at)
    )
    alarm_id = cur.fetchone()[0]
    conn.commit()
    return {"ok": True, "id": alarm_id}


@app.get("/api/alarms")
def list_alarms(session_id: str):
    conn = db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT * FROM alarms WHERE session_id=%s ORDER BY scheduled_at ASC",
        (session_id,)
    )
    return cur.fetchall()


@app.delete("/api/alarm/{aid}")
def delete_alarm(aid: int):
    conn = db()
    cur = conn.cursor()
    cur.execute("DELETE FROM alarms WHERE id=%s", (aid,))
    conn.commit()
    return {"ok": True}


@app.get("/api/alarm/pending")
def pending_alarm(session_id: str):
    now = datetime.now()

    conn = db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        """
        SELECT * FROM alarms
        WHERE session_id=%s
          AND fired=false
          AND scheduled_at <= %s
        ORDER BY scheduled_at ASC
        LIMIT 1
        """,
        (session_id, now)
    )
    row = cur.fetchone()

    if not row:
        return {"alarm": None}

    # 🔻 울린 알람은 바로 삭제 (또는 필요하면 fired=true로만 업데이트)
    cur.execute("DELETE FROM alarms WHERE id=%s", (row["id"],))
    conn.commit()

    return {"alarm": row}
