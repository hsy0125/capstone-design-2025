import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        dbname=os.getenv("DB_NAME")
    )

# 질문에 해당하는 답변 찾기 (경고등, 정비, 비상조치 등 통합 검색)
def find_voice_answer(question):
    conn = get_connection()
    cursor = conn.cursor()

    # 경고등 테이블 검색 (전체 정보 출력)
    cursor.execute("""
        SELECT warning_name, warning_desc, solution FROM warning_lights
        WHERE warning_name ILIKE %s OR warning_desc ILIKE %s
        LIMIT 1
    """, (f"%{question}%", f"%{question}%"))
    result = cursor.fetchone()
    if result:
        name, desc, solution = result
        conn.close()
        return f"\U0001F6A8 [{name}]\n\n⚠️ 설명:\n{desc}\n\n🛠 해결 방법:\n{solution}"

    # 유지보수 가이드
    cursor.execute("""
        SELECT item_name, action_type, interval_km, interval_month, note
        FROM maintenance_guide
        WHERE item_name ILIKE %s OR note ILIKE %s
        LIMIT 1
    """, (f"%{question}%", f"%{question}%"))
    result = cursor.fetchone()
    if result:
        conn.close()
        item, action, km, month, note = result
        return f"\U0001F9F0 [{item} - {action}]\n📌 주기: {km}km / {month}개월\n📝 {note}"

    # 비상 상황 안내
    cursor.execute("""
        SELECT situation FROM emergency_tips
        WHERE situation ILIKE %s
        LIMIT 1
    """, (f"%{question}%",))
    result = cursor.fetchone()
    if result:
        situation = result[0]
        cursor.execute("""
            SELECT step_order, step_desc FROM emergency_steps
            WHERE tip_id = (SELECT tip_id FROM emergency_tips WHERE situation = %s LIMIT 1)
            ORDER BY step_order ASC
        """, (situation,))
        steps = cursor.fetchall()
        conn.close()
        step_text = "\n".join([f"{order}. {desc}" for order, desc in steps])
        return f"\U0001F6A8 [비상상황: {situation}]\n\n🧭 응급조치 단계:\n{step_text}"

    conn.close()
    return None  # 못 찾은 경우

def save_voice_answer(question, answer, car_model):
    conn = get_connection()
    cursor = conn.cursor()

    # 1. chat_log 테이블에 저장
    cursor.execute(
        "INSERT INTO chat_log (question, answer, car_model) VALUES (%s, %s, %s)",
        (question, answer, car_model)
    )

    # 2. solution 테이블에도 저장 (필요하다면)
    cursor.execute(
        "INSERT INTO solution (question, answer, car_model) VALUES (%s, %s, %s)",
        (question, answer, car_model)
    )

    conn.commit()
    conn.close()