import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    print("🔐 DB 연결 정보 확인")
    print("🔐 DB_HOST:", os.getenv("DB_HOST"))
    print("🔐 DB_PORT:", os.getenv("DB_PORT"))
    print("🔐 DB_USER:", os.getenv("DB_USER"))
    print("🔐 DB_PASSWORD:", os.getenv("DB_PASSWORD"))
    print("🔐 DB_NAME:", os.getenv("DB_NAME"))

    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        dbname=os.getenv("DB_NAME")
    )
def find_answer(question, car_model):
    conn = get_connection()
    cursor = conn.cursor()

    # 1. warning_lights 테이블에서 검색
    cursor.execute("""
        SELECT solution FROM warning_lights
        WHERE warning_name ILIKE %s OR warning_desc ILIKE %s
        LIMIT 1
    """, (f"%{question}%", f"%{question}%"))
    result = cursor.fetchone()
    if result:
        conn.close()
        return result[0], "warning_lights"

    # 2. solution 테이블에서 검색
    cursor.execute("""
        SELECT answer FROM solution
        WHERE question = %s AND car_model = %s
        LIMIT 1
    """, (question, car_model))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0], "solution"

    # 3. 없으면 GPT로 넘어감
    return None, None

def save_answer(question, answer, car_model):
    conn = get_connection()
    cursor = conn.cursor()

    # chat_log 저장 (개발자용 로그 기록)
    cursor.execute(
        "INSERT INTO chat_log (question, answer, car_model) VALUES (%s, %s, %s)",
        (question, answer, car_model)
    )

    # solution 저장 (실제 답변 저장소)
    # → car_model이 없을 수도 있으므로 NULL 허용되게 테이블 생성 필요
    cursor.execute(
        "INSERT INTO solution (question, answer, car_model) VALUES (%s, %s, %s)",
        (question, answer, car_model)
    )

    conn.commit()
    conn.close()

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