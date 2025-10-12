import openai
import os
from dotenv import load_dotenv
from db import find_similar_answer, save_answer
from public.ask_rag import search_all_tables
from public.korean_query_normalizer import normalize_query
from utils import normalize_question, is_similar
## GPT 호출, DB 검색 통합, 중복 방지, 출력 제어

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


def ask_with_db_context(question, car_model="아반떼", interactive=True):
    # norm_question = normalize_question(question)
    norm_question, canon_key = normalize_query(question)
    print(f"[정규화] 원문: {question}  →  표준: {norm_question} (canon={canon_key})")

    answer, source, matched_q = find_similar_answer(norm_question, car_model)
    if answer:
        print(f"\n📦 DB 답변 (출처: {source}) [Q: {matched_q}]\n{answer}")

        # ✅ API(비대화식)에서는 input()을 절대 호출하지 않도록
        if not interactive:
            return answer

        use_gpt = input("\n🤖 GPT 보완 설명도 들을까요? (Y/N): ").strip().lower()
        if use_gpt != 'y':
            return answer

    # 아래는 GPT 보완 설명 흐름 (DB가 없거나, 보완 설명을 원할 때)
    db_result = search_all_tables(norm_question)
    if db_result:
        context = f"다음 정보를 참고해서 사용자 질문에 답변해줘:\n{db_result}"
    else:
        context = "DB에 관련 정보가 없습니다. 사용자의 질문에 직접 답변해줘."

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    "당신은 차량 AI 정비 도우미입니다. "
                    "표현 차이(띄어쓰기, 조사, 구어체)가 있어도 의미가 같다면 같은 답을 주세요. "
                    "예: ‘경고등/불 들어옴/램프 켜짐/아이콘’은 동의어로 간주합니다. "
                    f"{context}"
                ),
            },
            {"role": "user", "content": question},
        ],
    )

    gpt_answer = response.choices[0].message.content.strip()
    gpt_answer += "\n\n🔎 참고: 이 정보는 일반적인 설명이며, 실제 차량 매뉴얼도 확인하세요."

    print("\n💬 GPT 생성 응답:\n", gpt_answer)
    save_answer(norm_question, gpt_answer, car_model)
    return gpt_answer