# public/ask_rag.py

import openai
import os
import sys
from dotenv import load_dotenv

# ✅ 루트 경로를 추가 — 이 세 줄은 꼭 있어야 함!
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from db import find_similar_answer, save_answer, get_connection
from utils import normalize_question
from korean_query_normalizer import normalize_query

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


# =========================
#  동의어(표준키) 간단 매핑
# =========================
# ※ 나중에 DB 테이블로 옮겨도 됨. (synonyms 테이블)
CANON_MAP = {
    "에어백 경고등": {
        "에어백 경고등", "에어백 불 들어옴", "에어백 램프", "에어백 아이콘", "에어백 경고 불",
        "에어백 경고", "에어백 표시등"
    },
    "에어컨 냄새": {
        "에어컨 냄새", "에어컨에서 냄새", "쿨러 냄새", "송풍구 냄새", "에어컨 악취", "에어컨 곰팡이 냄새",
        "에어컨에서 나는 냄새", "에어컨 킨 후 냄새"
    },
    "엔진오일 경고등": {
        "엔진오일 경고등", "오일 경고등", "엔진오일 불", "오일 아이콘", "오일 램프"
    },
}

def map_to_canon(q: str):
    for canon, keys in CANON_MAP.items():
        if any(k in q for k in keys):
            return canon
    return None


# =========================
#  키워드 추출 (아주 가볍게)
# =========================
def _extract_keywords(text: str) -> list[str]:
    # 공백/구두점 기준 토큰화
    noisy = "?,.!;:/()[]{}'\""
    t = text
    for ch in noisy:
        t = t.replace(ch, " ")
    toks = [tok.strip() for tok in t.split() if tok.strip()]

    # 불용어와 너무 짧은 것 제거 
    stop = {
        "을", "를", "이", "가", "은", "는", "에", "에서", "로", "과", "와", "또는", "그리고",
        "같은", "하는", "하다", "있다", "나요", "어떻게", "왜",
        "이상한", "좀", "너무", "큰", "작은", "약간"
    }
    toks = [tok for tok in toks if (len(tok) >= 2 and tok not in stop)]

    # 중복 제거 + 상위 5개만
    return list(dict.fromkeys(toks))[:5]


# ==========================================================
#  테이블별 검색: ILIKE + (가능하면) similarity(pg_trgm) 활용
#  - pg_trgm 미설치/권한문제면 자동으로 ILIKE-only 폴백
#  - 여러 테이블에서 최고 점수 하나를 뽑아서 반환
# ==========================================================
def search_all_tables(question_or_keyword: str):
    conn = get_connection()
    cur = conn.cursor()

    # (1) 표준키 매핑 시도
    canon = map_to_canon(question_or_keyword)

    # (2) 키워드 추출 대상: 표준키가 있으면 그걸 우선
    base_text = canon or question_or_keyword
    kws = _extract_keywords(base_text) or [base_text]

    # similarity() 사용 가능 여부 점검
    use_trgm = True
    try:
        cur.execute("SELECT similarity('abc','abd');")
        _ = cur.fetchone()
    except Exception:
        use_trgm = False

    def like_clause(cols):
        ors = []
        for c in cols:
            ors.extend([f"{c} ILIKE %s"] * len(kws))
        return " OR ".join(ors)

    def params_for_like():
        return [f"%{kw}%" for kw in kws]

    # similarity용
    def trgm_clause(cols):
        ors = []
        for c in cols:
            ors.extend([f"similarity({c}, %s) > 0.30"] * len(kws))
        return " OR ".join(ors)

    def params_for_trgm():
        return kws

    results = []

    # 공통 실행 도우미
    def run_query(category, table, cols_select, cols_search):
        if use_trgm:
            # 점수: 각 컬럼과 키워드들의 similarity 최대값을 GREATEST로 평가
            score_expr = "GREATEST(" + ", ".join([f"max(similarity({c}, kw))" for c in cols_search]) + ")"
            # 키워드 배열을 UNNEST해 max(similarity()) 얻기
            sql = f"""
            WITH kw AS (
                SELECT UNNEST(ARRAY[{",".join(["%s"]*len(kws))}]) AS kw
            )
            SELECT %s AS category,
            {cols_select},
            {score_expr} AS score
            FROM {table}, kw
            WHERE ({like_clause(cols_search)} OR {trgm_clause(cols_search)})
            GROUP BY {cols_select}
            ORDER BY score DESC NULLS LAST
            LIMIT 1
            """
            params = [*kws, category, *params_for_like() * len(cols_search), *params_for_trgm() * len(cols_search)]
        else:
            # ILIKE-only: 단순히 매칭되면 점수 1.0으로 고정
            sql = f"""
            SELECT %s AS category,
                {cols_select},
                1.0 AS score
            FROM {table}
            WHERE ({like_clause(cols_search)})
            LIMIT 1
            """
            params = [category, *params_for_like() * len(cols_search)]

        try:
            cur.execute(sql, params)
            row = cur.fetchone()
            if row:
                results.append(row)
        except Exception as e:
            # 특정 테이블 에러 시 무시하고 다음 테이블 진행
            print(f"⚠️ 검색 중 오류({category}): {e}")

    # 각 테이블 검색
    run_query(
        "경고등",
        "warning_lights",
        "warning_name, warning_desc, solution",
        ["warning_name", "warning_desc", "solution"],
    )
    run_query(
        "비상조치",
        "emergency_tips",
        "situation, NULL::text, NULL::text",
        ["situation"],
    )
    run_query(
        "응급단계",
        "emergency_steps",
        "step_desc, NULL::text, NULL::text",
        ["step_desc"],
    )
    run_query(
        "정비가이드",
        "maintenance_guide",
        "item_name, note, NULL::text",
        ["item_name", "note"],
    )
    run_query(
        "차량정보",
        "vehicles",
        "model_name, engine_type, NULL::text",
        ["model_name", "engine_type"],
    )

    conn.close()

    if not results:
        return None

    # 점수 최고 결과 선택
    # row 구조: (category, f1, f2, f3, score)
    best = sorted(results, key=lambda r: (r[-1] or 0), reverse=True)[0]
    cat, f1, f2, f3, score = best
    detail = " / ".join([str(x) for x in [f1, f2, f3] if x and str(x).strip()])
    return f"[키워드·유사도 매칭: {score:.2f}] [{cat}] {detail}"


# ask_rag.py

def ask_with_db_context(question, car_model="아반떼"):
    # 1) 질문 정규화
    norm_question, canon_key = normalize_query(question)
    print(f"[정규화] 원문: {question}  →  표준: {norm_question} (canon={canon_key})")

    # 2) DB 캐시/유사도에서 먼저 찾기
    answer, source, matched_q = find_similar_answer(norm_question, car_model)
    if answer:
        # 👉 DB에서 찾았으면 여기서 끝!
        print(f"\n📦 DB 답변 (출처: {source}) [Q: {matched_q}]\n{answer}")
        # 필요하면 캐시 갱신/로그만 하고 반환
        return answer

    # 3) DB 키워드 매칭(테이블 검색) → 컨텍스트 구성
    db_result = search_all_tables(norm_question)
    if db_result:
        context = f"다음 정보를 참고해서 사용자 질문에 답변해줘:\n{db_result}"
        print(f"\n✅ DB 키워드/유사도 매칭 결과:\n{db_result}")
    else:
        context = "DB에 관련 정보가 없습니다. 사용자의 질문에 직접 답변해줘."
        print("\n⚠️ DB 매칭 없음 → GPT 생성으로 진행")

    # 4) GPT 생성 (입력 대기/분기 없음)
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

    # 5) 생성 답변은 캐시에 저장해 다음엔 DB에서 바로 나가게
    save_answer(norm_question, gpt_answer, car_model)

    return gpt_answer