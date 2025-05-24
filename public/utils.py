import re
from fuzzywuzzy import fuzz
## 텍스트 정규화, 유사도 판단 등 재사용 함수 (유사한 질문이 다시 gpt에게 가지 않도록 
# ex) 엔진 경고등이 들어왔어요 / 엔진 경고등 = 이 둘을 이전에는 다른 질문으로 여겨 지피티로 보냄(중복) )

def normalize_question(text):
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)  # 특수문자 제거
    text = re.sub(r"\s+", " ", text).strip()
    return text

def is_similar(q1, q2, threshold=80):
    return fuzz.partial_ratio(normalize_question(q1), normalize_question(q2)) >= threshold
