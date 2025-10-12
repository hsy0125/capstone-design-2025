import os
import argparse
from flask import Flask, request, jsonify
from flask_cors import CORS

from ask_rag import ask_with_db_context  # RAG + GPT
# 기존 ask_question 도 사용하려면 import 유지 가능
# from ask import ask_question

app = Flask(__name__)
CORS(app)  # 프론트(5173)에서 호출 허용

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
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "5050")))
    args = parser.parse_args()

    if args.cli:
        run_cli()
    else:
        # 기본: API 서버로 실행 (프론트에서 호출)
        app.run(host="0.0.0.0", port=args.port)