import streamlit as st
import requests
from openai import OpenAI

# =========================
# 기본 설정
# =========================
st.set_page_config(page_title="취향 기반 도서 추천", page_icon="📚")
st.title("📚 취향 기반 도서 추천")
st.write("독서 경험과 취향, 연령대와 감성까지 고려해 지금 당신에게 맞는 책을 추천해드려요.")

# =========================
# API KEY
# =========================
st.sidebar.header("🔑 API 설정")
KAKAO_API_KEY = st.sidebar.text_input("Kakao REST API Key", type="password")
OPENAI_API_KEY = st.sidebar.text_input("OpenAI API Key", type="password")

if not KAKAO_API_KEY or not OPENAI_API_KEY:
    st.info("🔑 사이드바에서 API Key를 입력해주세요.")
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)

# =========================
# ❌ 문제집 / 수험서 필터
# =========================
BANNED_KEYWORDS = [
    "문제", "기출", "토익", "토플", "수능", "자격증",
    "시험", "연습", "워크북", "Workbook", "교과서",
    "EBS", "개정", "한국사능력검정", "한능검",
    # 연령 관련 차단
    "유아", "아동", "어린이", "초등", "저학년"
]

def is_study_book(book):
    title = book.get("title", "")
    return any(bad in title for bad in BANNED_KEYWORDS)

# =========================
# 🔞 연령대 하한선 로직
# =========================
AGE_FLOOR = {
    "10대": "teen",
    "20대 초반": "adult_entry",
    "20대 후반": "adult",
    "30대": "adult",
    "40대": "adult",
    "50대 이상": "adult"
}

def get_book_target_level(title):
    title = title.lower()
    if any(k in title for k in ["유아", "아동", "어린이", "초등", "저학년"]):
        return "child"
    if any(k in title for k in ["청소년", "중학생", "고등학생"]):
        return "teen"
    return "adult"

def is_allowed_by_age(title, age_group):
    user_floor = AGE_FLOOR.get(age_group, "adult")
    book_level = get_book_target_level(title)

    if user_floor == "adult":
        return book_level == "adult"
    if user_floor == "adult_entry":
        return book_level in ["adult", "teen"]
    if user_floor == "teen":
        return book_level in ["teen", "adult"]

    return True

# =========================
# Fallback 키워드
# =========================
FALLBACK_KEYWORDS = {
    "과학·기술": "교양 과학 입문",
    "역사": "이야기로 읽는 역사",
    "경제·경영": "경제 교양서",
    "사회·시사": "사회 이야기 책",
    "인문·철학": "쉽게 읽는 인문학"
}

# =========================
# UX 보조 맵
# =========================
LEVEL_MAP = {
    "📚 자주 읽는다": "★★★☆☆",
    "🙂 가끔 읽는다": "★★☆☆☆",
    "😅 거의 읽지 않는다": "★★☆☆☆",
    "🆕 최근 관심이 생겼다": "★☆☆☆☆"
}

MOOD_ICON = {
    "지치고 위로가 필요함": "🫂",
    "차분함": "🌿",
    "에너지가 넘침": "🔥",
    "특별한 기분은 아님": "📖"
}

# =========================
# Kakao Book API
# =========================
def search_kakao_books(keyword, age_group, size=6):
    try:
        res = requests.get(
            "https://dapi.kakao.com/v3/search/book",
            headers={"Authorization": f"KakaoAK {KAKAO_API_KEY}"},
            params={"query": keyword, "size": size},
            timeout=10
        )
        res.raise_for_status()
        books = res.json().get("documents", [])
        return [
            b for b in books
            if not is_study_book(b)
            and is_allowed_by_age(b.get("title", ""), age_group)
        ]
    except requests.RequestException:
        return []

# =========================
# Google Books API
# =========================
def get_google_book_info(title):
    try:
        res = requests.get(
            "https://www.googleapis.com/books/v1/volumes",
            params={"q": title, "maxResults": 1},
            timeout=10
        )
        res.raise_for_status()
        items = res.json().get("items", [])
        if not items:
            return {"description": "", "year": ""}
        info = items[0].get("volumeInfo", {})
        return {
            "description": info.get("description", ""),
            "year": info.get("publishedDate", "")[:4]
        }
    except requests.RequestException:
        return {"
