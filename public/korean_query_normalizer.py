# korean_query_normalizer.py
# -*- coding: utf-8 -*-
"""
한국어 질의 정규화 모듈
- 띄어쓰기·조사·말투 차이/오탈자/영문표현을 완화
- 의미가 같은 표현을 "표준 질의어"로 매핑
- 외부 라이브러리 없이 동작 (정규식/룰 기반)
"""

from __future__ import annotations
import re
from typing import Tuple, Dict, List

# 불용 조사/어미(최소 침습: 너무 공격적으로 지우지 않음)
_JOSA = r"(이|가|은|는|을|를|에|에서|으로|와|과|의|도|만|보다|부터|까지|쯤|처럼|라고|라고요|나요|죠|요)$"

# 자주 나오는 군말/추임새/채팅체 축약 제거
_FILLER_PAT = re.compile(r"(그냥|혹시|일단|약간|진짜|너무|좀|좀요|뭔가|아무튼|근데|그리고|그러면|그럼|말인데|같은데|같은데요|같음|요즘|지금|방금)\s*", re.I)

# 기초 정규화: 소문자화, 특수문자/중복 공백 정리
def _basic_clean(t: str) -> str:
    t = (t or "").strip().lower()
    t = _FILLER_PAT.sub("", t)
    t = re.sub(r"[~!?,.(){}\[\]<>:;\"'`·…─—–_|\\/=＋+＊*%@#^&$]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

# 조사 제거(단어 말미의 조사만 최소 제거)
def _strip_trailing_josa(t: str) -> str:
    return " ".join([re.sub(_JOSA, "", w) for w in t.split()])

# 표준 질의어(정답 카테고리) 사전
# 필요한 항목을 계속 확장해 나가면 됩니다.
_ALIAS: Dict[str, List[str]] = {
    # --- 경고등(대분류 예시) ---
    "에어백 경고등": [
        "에어백 불", "에어백 램프", "에어백 라이트", "에어백 모양",
        "에어백 깜빡이", "에어 백", "airbag", "airbag warning", "airbag light",
        "에어백 경고 등", "에어백 표시", "에어백등", "에어백 들어오", "에어백 켜지",
    ],
    "엔진 경고등": [
        "엔진불", "엔진 램프", "엔진 라이트", "체크 엔진", "check engine",
        "엔진 경고", "엔진등", "엔진 표시", "엔진 들어오", "엔진 켜지",
    ],
    "시트벨트 경고등": ["시트벨트 불", "벨트 불", "seat belt", "시트 벨트"],
    "브레이크 경고등": ["브레이크 불", "brake warning", "브레이크 경고", "브레이크등"],
    "배터리 경고등": ["배터리 불", "충전 경고", "battery light", "발전기 경고"],
    "오일 압력 경고등": ["오일 불", "오일 램프", "oil pressure", "엔진 오일 경고"],
    "abs 경고등": ["abs 불", "abs 램프", "anti lock"],
    "tpms 경고등": ["타이어 공기압", "공기압 경고", "tpms", "tire pressure"],
}

# 빠른 힌트 패턴(띄어쓰기/오탈자/섞어쓰기 허용)
_HINT_PATTERNS: List[Tuple[str, str]] = [
    # (정규식, 표준 질의어)
    (r"에\s*어\s*백.*(경고|불|램프|라이트|아이콘|표시|모양|깜빡|켜|들어오)", "에어백 경고등"),
    (r"(체크|check).*엔진|엔진.*(경고|불|램프|라이트|표시|켜|들어오)", "엔진 경고등"),
    (r"(시트\s*벨트|벨트).*(경고|불|램프|라이트|표시|켜|들어오)", "시트벨트 경고등"),
    (r"(브레이크).*(경고|불|램프|라이트|표시|켜|들어오)", "브레이크 경고등"),
    (r"(배터리|충전|제너레이터|발전기).*(경고|불|램프|라이트|표시|켜|들어오)", "배터리 경고등"),
    (r"(오일|oil).*(압|프레셔|pressure|경고|불|램프|라이트|표시|켜|들어오)", "오일 압력 경고등"),
    (r"\babs\b|anti\s*lock", "abs 경고등"),
    (r"\btpms\b|타이어.*(공기압|압력)", "tpms 경고등"),
]

def _alias_lookup(t: str) -> str | None:
    # 1) 정확/부분 매칭
    for canon, variants in _ALIAS.items():
        if canon in t:
            return canon
        for v in variants:
            if v in t:
                return canon
    # 2) 힌트 정규식
    for pat, canon in _HINT_PATTERNS:
        if re.search(pat, t):
            return canon
    return None

def normalize_query(user_text: str) -> Tuple[str, str]:
    """
    Returns:
        normalized: 검색/임베딩에 보낼 표준화 질의(가능하면 canonical key)
        canonical_key: 사전 매핑 결과(없으면 빈 문자열)
    """
    raw = user_text or ""
    t = _basic_clean(raw)
    t = _strip_trailing_josa(t)
    # 중복 공백 정리
    t = re.sub(r"\s+", " ", t).strip()

    canon = _alias_lookup(t)
    normalized = canon if canon else t
    return normalized, (canon or "")

# 옵션: 런타임에 동의어 추가(관리 콘솔 등에서 확장하고 싶을 때)
def register_alias(canonical: str, variants: List[str]) -> None:
    _ALIAS.setdefault(canonical, [])
    _ALIAS[canonical].extend([v for v in variants if v not in _ALIAS[canonical]])