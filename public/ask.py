import openai
import os
from dotenv import load_dotenv
from db import find_similar_answer, save_answer
from utils import normalize_question, is_similar
## GPT 호출, DB 검색 통합, 중복 방지, 출력 제어

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def ask_question(question, car_model="아반떼"):
    norm_question = normalize_question(question)

    # 1. DB 유사도 검색
    answer, source, matched_q = find_similar_answer(norm_question, car_model)

    if answer:
        print(f"\n📦 DB Response (from {source}):\n(Q: {matched_q})")
        print(answer)

        use_gpt = input("\n🤖 GPT 보완 설명을 추가로 들을까요? (Y/N): ").strip().lower()
        if use_gpt != 'y':
            return answer

    # 2. GPT 생성
    print("🧠 GPT 생성 중...")
    prompt = f"""당신은 차량 모델 '{car_model}'에 대한 AI 정비 도우미입니다.
질문에 대해 운전자가 쉽게 이해할 수 있도록 간결하고 명확하게 설명해주세요.

[답변 형식 예시]
⚠️ 설명: 엔진오일 부족을 알리는 경고등입니다.
🛠 해결 방법: 차량을 정차한 후, 엔진오일을 점검하고 보충하세요.

답변 마지막에 참고 안내 문구도 포함하세요."""

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": question}
        ]
    )
    gpt_answer = response.choices[0].message.content.strip()

    # 출처 문구 추가
    gpt_answer += "\n\n🔎 참고: 이 정보는 일반적인 기준에 기반한 설명이며, 차량 매뉴얼을 함께 참고하세요."

    print("\n💬 GPT 응답:")
    print(gpt_answer)

    # DB 저장
    save_answer(norm_question, gpt_answer, car_model)
    return gpt_answer