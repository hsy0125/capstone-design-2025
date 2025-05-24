from ask import ask_question
## CLI , 사용자 질문 입력 받기 + 전체 흐름 실행

from ask_rag import ask_with_db_context

if __name__ == "__main__":
    print("🚘 차량 AI 비서에게 질문하세요 (RAG 기반)\n")
    car_model = input("🚗 차량 모델을 입력하세요: ")

    while True:
        q = input("\n❓ 질문: ")
        if q.strip().lower() in ['종료', 'exit', 'quit']:
            print("👋 종료합니다. 안전 운전 하세요!")
            break
        ask_with_db_context(q, car_model)