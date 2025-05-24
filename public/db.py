from utils import is_similar
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
## DB 연결, 유사 질문 찾기, 답변 저장 처리

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        dbname=os.getenv("DB_NAME")
    )

def find_similar_answer(normalized_question, car_model):
    conn = get_connection()
    cursor = conn.cursor()

    # 모든 질문 불러와서 유사도 확인
    cursor.execute("SELECT question, answer FROM solution WHERE car_model = %s", (car_model,))
    for q, a in cursor.fetchall():
        if is_similar(q, normalized_question):
            conn.close()
            return a, "solution", q

    conn.close()
    return None, None, None

def save_answer(question, answer, car_model):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO solution (question, answer, car_model) VALUES (%s, %s, %s)",
        (question, answer, car_model)
    )
    conn.commit()
    conn.close()