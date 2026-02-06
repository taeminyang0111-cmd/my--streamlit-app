import streamlit as st
import requests
import openai

# =========================
# 기본 설정
# =========================
st.set_page_config(
    page_title="취향 기반 도서 추천",
    page_icon="📚",
    layout="centered"
)

st.title("📚 취향 기반 도서 추천")
st.write("몇 가지 질문에 답하면 당신에게 맞는 책을 추천해드려요!")

# =========================
# 🔑 API KEY 입력
# =========================
st.sidebar.header("🔑 API 설정")

DATA4LIB_API_KEY = st.sidebar.text_input(
    "Data4Library API Key",
    type="password",
    placeholder="발급받은 키를 입력하세요"
)

OPENAI_API_KEY = st.sidebar.text_input(
    "OpenAI API Key",
    type="password",
    placeholder="sk-...",
)

if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

# =========================
# Data4Library API 함수
# =========================
def search_data4library(keyword, max_results=5):
    """
    Data4Library 도서 검색 (키워드 기반)
    """
    url = "https://api.data4library.kr/api/srchBooks"

    params = {
        "authKey": DATA4LIB_API_KEY,
        "keyword": keyword,
        "pageNo": 1,
        "pageSize": max_results,
        "format": "json"
    }

    response = requests.get(url, params=params, timeout=10)
    if response.status_code != 200:
        return []

    data = response.json()
    return data.get("response", {}).get("docs", [])

# =========================
# LLM 추천 프롬프트 생성
# =========================
def build_prompt(user_input):
    return f"""
사용자의 취향을 바탕으로 검색에 적합한 도서 키워드 3개를 만들어주세요.

조건:
- 너무 추상적이지 않게
- 한국 도서 검색에 적합한 키워드
- 장르 / 분위기 / 주제 중심

사용자 정보:
{user_input}

출력 형식:
키워드1, 키워드2, 키워드3
"""

# =========================
# 질문 UI
# =========================
st.divider()

reading_level = st.radio(
    "1. 평소 독서 습관은 어떤가요?",
    [
        "📖 책 읽는 걸 좋아하고 자주 읽는다",
        "🙂 가끔 읽는다",
        "😅 거의 안 읽지만 시작해보고 싶다",
        "🆕 독서를 막 시작하려고 한다"
    ]
)

st.divider()

music_genres = st.multiselect(
    "2. 좋아하는 음악 장르",
    ["발라드", "힙합/R&B", "인디", "팝", "클래식", "재즈", "OST"]
)

movie_genres = st.multiselect(
    "3. 좋아하는 영화 장르",
    ["드라마", "로맨스", "액션", "판타지/SF", "범죄/스릴러", "성장 영화"]
)

reading_goal = st.radio(
    "4. 독서 목적",
    [
        "힐링 / 위로",
        "재미 / 몰입",
        "생각의 확장",
        "자기 성장",
        "가볍게 읽기"
    ]
)

# =========================
# 추천 버튼
# =========================
if st.button("📖 도서 추천 받기"):
    if not DATA4LIB_API_KEY or not OPENAI_API_KEY:
        st.warning("API Key를 모두 입력해주세요!")
    else:
        user_profile = {
            "독서 습관": reading_level,
            "음악 취향": music_genres,
            "영화 취향": movie_genres,
            "독서 목적": reading_goal
        }

        with st.spinner("취향 분석 중..."):
            prompt = build_prompt(user_profile)

            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )

            keywords_text = response.choices[0].message.content
            keywords = [k.strip() for k in keywords_text.split(",")]

        st.subheader("🔍 추천 키워드")
        st.write(keywords)

        st.subheader("📚 추천 도서")

        for kw in keywords:
            books = search_data4library(kw)
            if not books:
                continue

            st.markdown(f"### 🔑 {kw}")
            for book in books:
                info = book.get("doc", {})
                st.write(f"**{info.get('bookname', '제목 없음')}**")
                st.caption(f"저자: {info.get('authors', '정보 없음')} | 출판사: {info.get('publisher', '')}")
                st.write("―" * 20)
