import openai
import os
from dotenv import load_dotenv
from db import find_answer, save_answer  # ✅ 반드시 수정된 find_answer 사용

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# gpt 기반 응답 --------------------------------------------------------------------
def ask_question(question, car_model="아반떼"):
    # 1. DB에서 먼저 찾기
    answer, source = find_answer(question, car_model)

    if answer:
        print(f"\n📦 DB Response (source: {source}):")
        print(answer)
        return answer  # ✅ GPT 호출 생략

    # 2. GPT로 생성
    print("❌ Not in DB. Asking GPT...")
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"You are a car assistant for model: {car_model}."},
            {"role": "user", "content": question}
        ]
    )
    answer = response.choices[0].message.content.strip()

    # 3. GPT가 생성한 답변 저장 (chat_log + solution)
    save_answer(question, answer, car_model)

    # 4. GPT 응답 출력
    print("\n💬 GPT Response:")
    print(answer)
    return answer

# 실행 부분 --------------------------------------------------------------------
if __name__ == "__main__":
    print("🚘 차량 AI 비서에게 질문하세요! (종료하려면 '종료'라고 입력하세요)\n")

    car_model = input("🚗 차량 모델을 입력하세요: ")

    while True:
        question = input("\n❓ 질문: ")

        if question.strip().lower() in ['종료', 'exit', 'quit']:
            print("👋 종료합니다. 안전 운전 하세요!")
            break

        ask_question(question, car_model)
    
# 디비에서만 검색 ------------------------------------------------------------------------------------------- 
# from db import search_all_tables
# import os

# def ask_anything(question):
#     result = search_all_tables(question)

#     if result:
#         print("✅ Found in DB:")
#         return result
#     else:
#         print("❌ DB에 관련 정보가 없습니다.")
#         return "죄송합니다. 질문에 해당하는 정보를 데이터베이스에서 찾을 수 없습니다."

# if __name__ == "__main__":
#     question = input("❓ Question: ")
#     response = ask_anything(question)
#     print("\n📘 Response:")
#     print(response)
# 디비 + 쳇 검색결과 병합 ------------------------------------------------------------------------------
# import openai
# import os
# from dotenv import load_dotenv
# from db import search_all_tables

# # 환경변수 로딩 (.env 파일)
# load_dotenv()
# openai.api_key = os.getenv("OPENAI_API_KEY")

# # ✅ DB + GPT 병합 응답 함수
# def ask_question_combined(question):
#     # 1. 먼저 DB에서 검색
#     db_result = search_all_tables(question)
    
#     # 2. GPT에게도 항상 질문해서 보완 설명 받기
#     print("🤖 GPT에도 질문 중...")
#     gpt_response = openai.chat.completions.create(
#         model="gpt-3.5-turbo",
#         messages=[
#             {"role": "system", "content": "너는 자동차 정비, 경고등, 응급상황 등에 대해 설명해주는 AI 도우미야."},
#             {"role": "user", "content": question}
#         ]
#     )
#     gpt_result = gpt_response.choices[0].message.content.strip()

#     # 3. 병합된 응답 반환
#     if db_result:
#         return f"""📘 [데이터베이스에 있는 정보]
# {db_result}

# 🤖 [GPT가 보완한 설명]
# {gpt_result}
# """
#     else:
#         return f"""❗️데이터베이스에 직접적인 정보는 없었습니다.

# 🤖 [GPT가 제공하는 설명]
# {gpt_result}
# """

# # ✅ 메인 실행
# if __name__ == "__main__":
#     question = input("❓ Question: ")
#     response = ask_question_combined(question)
#     print(response)
