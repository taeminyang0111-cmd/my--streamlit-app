import streamlit as st
import requests
from openai import OpenAI

# =========================
# 기본 설정
# =========================
st.set_page_config(page_title="취향 기반 도서 추천", page_icon="📚")
st.title("📚 취향 기반 도서 추천")
st.write("연령과 취향을 함께 고려해, 지금 당신에게 가장 잘 맞는 책을 추천해드려요.")

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
# Kakao Book API
# =========================
def search_kakao_books(keyword, size=3):
    try:
        response = requests.get(
            "https://dapi.kakao.com/v3/search/book",
            headers={"Authorization": f"KakaoAK {KAKAO_API_KEY}"},
            params={"query": keyword, "size": size},
            timeout=10
        )
        response.raise_for_status()
        return response.json().get("documents", [])
    except requests.RequestException:
        return []

# =========================
# Google Books API
# =========================
def search_google_book_description(title):
    try:
        response = requests.get(
            "https://www.googleapis.com/books/v1/volumes",
            params={"q": title, "maxResults": 1},
            timeout=10
        )
        response.raise_for_status()
        items = response.json().get("items", [])
        if not items:
            return ""
        return items[0]["volumeInfo"].get("description", "")
    except requests.RequestException:
        return ""

# =========================
# 프롬프트
# =========================
def build_main_prompt(user_input):
    return f"""
너는 한국 독서 추천 서비스의 전문 큐레이터다.
연령대를 가장 중요하게 고려하고,
음악과 영화 취향은 감성 보조 신호로 활용해
이 사용자에게 가장 잘 맞는 독서 방향을 설정하라.

출력 형식:
독서성향: <한 문장>
대표추천: <키워드 1개>
보조추천: <키워드 1>, <키워드 2>

사용자 정보:
{user_input}
"""

def build_reason_prompt(user_profile, book_title, description):
    return f"""
아래 정보를 바탕으로
이 사용자에게 이 책을 추천하는 이유를
한 문장으로 설명해라.

사용자 정보:
{user_profile}

책 제목:
{book_title}

책 설명:
{description}
"""

# =========================
# 질문 UI
# =========================
age_group = st.radio("연령대", ["10대", "20대 초반", "20대 후반", "30대", "40대", "50대 이상"])
reading_goal = st.radio("독서 목적", ["힐링 / 위로", "몰입감", "자기성찰", "공부 / 성장", "가볍게"])
music = st.multiselect("음악 취향 🎶", ["발라드", "인디/밴드", "힙합/R&B", "클래식"])
movie = st.multiselect("영화 취향 🎬", ["드라마", "로맨스", "판타지/SF", "스릴러"])

# =========================
# 추천 실행
# =========================
if st.button("📖 도서 추천 받기"):
    user_profile = {
        "연령대": age_group,
        "독서 목적": reading_goal,
        "음악 취향": music,
        "영화 취향": movie
    }

    with st.spinner("추천 분석 중..."):
        response = client.responses.create(
            model="gpt-4o-mini",
            input=build_main_prompt(user_profile),
            temperature=0.6
        )

        lines = response.output_text.splitlines()
        profile = lines[0].replace("독서성향:", "").strip()
        main_kw = lines[1].replace("대표추천:", "").strip()

    st.info(f"📌 당신의 독서 성향\n\n{profile}")
    st.subheader("⭐ 지금 가장 추천하는 책")

    books = search_kakao_books(main_kw, 3)

    for book in books:
        description = search_google_book_description(book["title"])

        reason_res = client.responses.create(
            model="gpt-4o-mini",
            input=build_reason_prompt(profile, book["title"], description),
            temperature=0.7
        )

        reason = reason_res.output_text.strip()

        st.markdown(f"**{book['title']}**")
        st.caption(reason)
        st.divider()
