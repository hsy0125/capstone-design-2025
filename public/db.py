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

def find_answer(question, car_model):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT answer FROM chat_log WHERE question = %s AND car_model = %s",
        (question, car_model)
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def save_answer(question, answer, car_model):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chat_log (question, answer, car_model) VALUES (%s, %s, %s)",
        (question, answer, car_model)
    )
    conn.commit()
    conn.close()
    ## db 검색 기반 추가 코드
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
