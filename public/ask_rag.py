import openai
import os
from dotenv import load_dotenv
from db import find_similar_answer, save_answer, get_connection
from utils import normalize_question

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def search_all_tables(keyword):
    conn = get_connection()
    cursor = conn.cursor()

    queries = [
        ("경고등", """
            SELECT '경고등' AS category, warning_name, warning_desc, solution
            FROM warning_lights
            WHERE warning_name ILIKE %s OR warning_desc ILIKE %s OR solution ILIKE %s
            LIMIT 1
        """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%")),

        ("비상조치", """
            SELECT '비상조치' AS category, situation
            FROM emergency_tips
            WHERE situation ILIKE %s
            LIMIT 1
        """, (f"%{keyword}%",)),

        ("응급단계", """
            SELECT '응급단계' AS category, step_desc
            FROM emergency_steps
            WHERE step_desc ILIKE %s
            LIMIT 1
        """, (f"%{keyword}%",)),

        ("정비가이드", """
            SELECT '정비가이드' AS category, item_name, action_type, interval_km, interval_month, note
            FROM maintenance_guide
            WHERE item_name ILIKE %s OR note ILIKE %s
            LIMIT 1
        """, (f"%{keyword}%", f"%{keyword}%")),

        ("차량정보", """
            SELECT '차량정보' AS category, model_name, engine_type, fuel_type, engine_oil
            FROM vehicles
            WHERE model_name ILIKE %s OR engine_type ILIKE %s
            LIMIT 1
        """, (f"%{keyword}%", f"%{keyword}%"))
    ]

    for category, query, params in queries:
        cursor.execute(query, params)
        result = cursor.fetchone()
        if result:
            conn.close()
            return f"[{category}] 관련 정보:\n" + "\n".join(str(field) for field in result[1:])

    conn.close()
    return None

def ask_with_db_context(question, car_model="아반떼"):
    norm_question = normalize_question(question)

    answer, source, matched_q = find_similar_answer(norm_question, car_model)
    if answer:
        print(f"\n📦 DB 답변 (출처: {source}) [Q: {matched_q}]\n{answer}")
        use_gpt = input("\n🤖 GPT 보완 설명도 들을까요? (Y/N): ").strip().lower()
        if use_gpt != 'y':
            return answer

    db_result = search_all_tables(norm_question)
    if db_result:
        context = f"다음 정보를 참고해서 사용자 질문에 답변해줘:\n{db_result}"
    else:
        context = "DB에 관련 정보가 없습니다. 사용자의 질문에 직접 답변해줘."

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"당신은 차량 AI 정비 도우미입니다. {context}"},
            {"role": "user", "content": question}
        ]
    )

    gpt_answer = response.choices[0].message.content.strip()
    gpt_answer += "\n\n🔎 참고: 이 정보는 일반적인 설명이며, 실제 차량 매뉴얼도 확인하세요."

    print("\n💬 GPT 생성 응답:\n", gpt_answer)
    save_answer(norm_question, gpt_answer, car_model)
    return gpt_answer