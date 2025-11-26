import os
import argparse
from datetime import datetime, timedelta, timezone

from flask import Flask, request, jsonify
from flask_cors import CORS

from ask_rag import ask_with_db_context  # RAG

# 🔔 알람 관련 – 최소한만 사용
from alarm_old.alarm_db import fetch_due_alarms, add_alarm   # DB 접근
from alarm_old.mode_state import Mode, get_mode, set_mode    # 모드 관리
from alarm_old.alarm_handler import is_alarm_trigger, handle_alarm_mode  # 알람 대화 처리
app = Flask(__name__)
CORS(app)


# =======================================================
#  기존 기능: /api/ask
# =======================================================
@app.post("/api/ask")
def api_ask():
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    car_model = (data.get("carModel") or "아반떼").strip()

    if not question:
        return jsonify({"error": "question is required"}), 400

    answer = ask_with_db_context(question, car_model)
    return jsonify({"answer": answer})


# =======================================================
#  🔥 새 기능: /chat — 알람 모드 + RAG
# =======================================================
@app.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id")
    text = (data.get("message") or "").strip()

    if not session_id or not text:
        return jsonify({"error":"session_id과 message가 필요합니다."}), 400

    # 1) 만료된 알람 정리
    mode = get_mode(session_id)

    # 2) ALARM 모드 처리
    if mode == Mode.ALARM:
        reply, new_mode = handle_alarm_mode(session_id, text)
        set_mode(session_id, new_mode)
        return jsonify({"reply": reply})

    # 3) CHAT 모드 → 알람 트리거 감지
    if is_alarm_trigger(text):
        set_mode(session_id, Mode.ALARM)
        return jsonify({"reply": "알람을 설정할게요. 언제 알람을 맞출까요?"})

    # 4) 기본 차량 RAG 처리
    answer = ask_with_db_context(text, "DEFAULT")
    return jsonify({"reply": answer})

# =======================================================
#  🔥 main.py 직접 실행 테스트: 알람 기능 확인용
# =======================================================
def test_alarm_feature():
    print("=== 알람 기능 테스트 시작 ===")
    session_id = "test-session"

    # STEP 1) 트리거 문장
    text1 = "알람 설정할게"
    print(f"\n입력1: {text1}")
    if is_alarm_trigger(text1):
        set_mode(session_id, Mode.ALARM)
        print("알람 모드 진입!")

    # STEP 2) 실제 시간 파싱
    text2 = "1분 후"
    print(f"\n입력2: {text2}")
    reply, new_mode = handle_alarm_mode(session_id, text2)
    print("AI 응답:", reply)
    set_mode(session_id, new_mode)

    # STEP 3) 알람을 즉시 울리도록 조정
    print("\ntrigger_at을 NOW()로 조정 중...")
    from db import get_connection
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE alarms SET trigger_at = NOW() WHERE session_id=%s;", (session_id,))
    conn.commit()
    cur.close()
    conn.close()

    # STEP 4) 만료된 알람 조회
    print("\n지금 울릴 알람 조회:")
    due = get_due_alarms(session_id, datetime.now())
    print(due)

    # STEP 5) TRIGGERED로 변경
    for a in due:
        mark_triggered(a["id"])
        print(f"알람 {a['id']} TRIGGERED 변경 완료")

    print("\n=== 알람 기능 단독 테스트 종료 ===")

KST = timezone(timedelta(hours=9))

@app.get("/alarms/due")
def alarms_due():
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"messages": []})

    now = datetime.now(KST)
    due = fetch_due_alarms(session_id, now)

    messages = []
    now_str = now.strftime("%m월 %d일 %p %I시 %M분")

    for a in due:
        msg = (
            f"⏰ 알람이 울립니다!\n"
            f"현재 시각은 {now_str} 입니다.\n"
            "5분 후에 다시 알람을 맞추려면 '5분 후 알람' 또는 '5분 후 다시'라고 말하세요."
        )
        messages.append(msg)

    return jsonify({"messages": messages})
# =======================================================
#  🔥 /api/voice — 음성 파일 업로드 + STT + 차량 RAG
# =======================================================
from io import BytesIO

@app.post("/api/voice")
def api_voice():
    from openai import OpenAI

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # 1) 파일 체크
    if "file" not in request.files:
        return jsonify({"error": "file missing"}), 400

    upload = request.files["file"]   # FileStorage 객체

    # 2) FileStorage → BytesIO 로 변환
    audio_bytes = upload.read()
    audio_file = BytesIO(audio_bytes)
    audio_file.name = upload.filename or "voice.webm"  # SDK가 내부에서 쓰는 이름

    # 3) Whisper STT 호출
    transcript = client.audio.transcriptions.create(
        model="gpt-4o-mini-transcribe",   # 또는 "whisper-1"
        file=audio_file,
    )

    text = (transcript.text or "").strip()

    if not text:
        return jsonify({"error": "no text recognized"}), 500

    # 4) 차량 RAG 답변 생성
    answer = ask_with_db_context(text, "아반떼")

    return jsonify({
        "text": text,
        "answer": answer,
    })
    

# =======================================================
#  진입점
# =======================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cli", action="store_true", help="CLI 모드로 실행")
    parser.add_argument("--test-alarm", action="store_true", help="알람 기능 테스트")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "5050")))
    args = parser.parse_args()

    if args.test_alarm:
        test_alarm_feature()
    elif args.cli:
        print("CLI 모드 실행 불가 (알람 제외).")
    else:
        app.run(host="0.0.0.0", port=args.port)

# app = Flask(__name__)
# CORS(app)  # 프론트(5173)에서 호출 허용

@app.post("/api/ask")
def api_ask():
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    car_model  = (data.get("carModel") or "아반떼").strip()
    if not question:
        return jsonify({"error": "question is required"}), 400

    # ✅ 비대화식 호출: input() 절대 안 씀
    answer = ask_with_db_context(question, car_model)
    return jsonify({"answer": answer})


def run_cli():
    """이전처럼 터미널에서 직접 묻고 답하는 모드"""
    print("🚘 차량 AI 비서에게 질문하세요 (RAG 기반)\n")
    car_model = input("🚗 차량 모델을 입력하세요: ").strip() or "아반떼"

    while True:
        q = input("\n❓ 질문: ")
        if q.strip().lower() in ["종료", "exit", "quit"]:
            print("👋 종료합니다. 안전 운전 하세요!")
            break
        print(ask_with_db_context(q, car_model))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cli", action="store_true", help="CLI 모드로 실행")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "8000")))
    args = parser.parse_args()

    if args.cli:
        run_cli()
    else:
        # 기본: API 서버로 실행 (프론트에서 호출)
        app.run(host="0.0.0.0", port=args.port)