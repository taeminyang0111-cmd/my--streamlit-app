import streamlit as st
import requests
from openai import OpenAI

# =========================
# 기본 설정
# =========================
st.set_page_config(page_title="취향 기반 도서 추천", page_icon="📚")
st.title("📚 취향 기반 도서 추천")
st.write("연령, 취향, 관심 분야까지 고려해 지금 당신에게 가장 잘 맞는 책을 추천해드려요.")

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
        res = requests.get(
            "https://dapi.kakao.com/v3/search/book",
            headers={"Authorization": f"KakaoAK {KAKAO_API_KEY}"},
            params={"query": keyword, "size": size},
            timeout=10
        )
        res.raise_for_status()
        return res.json().get("documents", [])
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
        info = items[0]["volumeInfo"]
        return {
            "description": info.get("description", ""),
            "year": info.get("publishedDate", "")[:4]
        }
    except requests.RequestException:
        return {"description": "", "year": ""}

# =========================
# 프롬프트
# =========================
def build_main_prompt(user_input):
    return f"""
너는 한국 독서 추천 서비스의 전문 큐레이터다.
아래 사용자 정보를 종합적으로 분석하여,
특히 '연령대'와 '선호하는 책의 분야'를 가장 중요한 기준으로 삼아
이 사용자에게 지금 가장 잘 맞는 책 추천 방향을 설정하라.

출력 형식:
독서성향: <한 문장>
대표추천: <키워드 1개>
보조추천: <키워드 1>, <키워드 2>

사용자 정보:
{user_input}
"""

def build_reason_prompt(profile, title, description):
    return f"""
독서 성향:
{profile}

책 제목:
{title}

책 설명:
{description}

이 사용자에게 이 책을 추천하는 이유를
한 문장으로 설명하라.
"""

# =========================
# 질문 UI
# =========================
age = st.radio("연령대", ["10대", "20대 초반", "20대 후반", "30대", "40대", "50대 이상"])

st.subheader("📚 선호하는 책의 분야")
book_fields = st.multiselect(
    "관심 있거나 자주 고르는 분야를 선택해주세요",
    [
        "소설·문학", "에세이", "자기계발", "인문·철학",
        "사회·시사", "경제·경영", "과학·기술",
        "역사", "판타지/SF", "추리·스릴러", "가볍게 읽는 교양"
    ]
)

mood = st.radio(
    "요즘 상태는 어떤가요?",
    ["지치고 위로가 필요함", "잔잔하지만 공허함", "새로운 자극이 필요함", "비교적 안정적"]
)

story_pref = st.radio(
    "이야기에서 더 중요한 것은?",
    ["감정과 관계", "사건과 전개", "메시지와 생각"]
)

volume = st.radio(
    "읽을 수 있는 분량은?",
    ["얇은 책이 좋다", "보통", "두꺼워도 괜찮다"]
)

music = st.multiselect("음악 취향 🎶", ["발라드", "인디/밴드", "힙합/R&B", "클래식"])
movie = st.multiselect("영화 취향 🎬", ["드라마", "로맨스", "판타지/SF", "스릴러"])
goal = st.radio("독서 목적", ["힐링 / 위로", "몰입감", "자기성찰", "공부 / 성장", "가볍게"])

# =========================
# 추천 실행
# =========================
if st.button("📖 도서 추천 받기"):
    user_profile = {
        "연령대": age,
        "선호 분야": book_fields,
        "현재 상태": mood,
        "서사 선호": story_pref,
        "분량 허용도": volume,
        "음악 취향": music,
        "영화 취향": movie,
        "독서 목적": goal
    }

    with st.spinner("추천 분석 중..."):
        res = client.responses.create(
            model="gpt-4o-mini",
            input=build_main_prompt(user_profile),
            temperature=0.6
        )

        lines = res.output_text.splitlines()
        profile = lines[0].replace("독서성향:", "").strip()
        main_kw = lines[1].replace("대표추천:", "").strip()

    st.info(f"📌 당신의 독서 성향\n\n{profile}")
    st.subheader("⭐ 지금 가장 추천하는 책")

    books = search_kakao_books(main_kw, 3)

    for book in books:
        google_info = get_google_book_info(book["title"])
        year = book.get("datetime", "")[:4] or google_info["year"]

        reason_res = client.responses.create(
            model="gpt-4o-mini",
            input=build_reason_prompt(profile, book["title"], google_info["description"]),
            temperature=0.7
        )

        reason = reason_res.output_text.strip()

        cols = st.columns([1, 4])
        with cols[0]:
            if book["thumbnail"]:
                st.image(book["thumbnail"], width=90)
        with cols[1]:
            st.markdown(f"**{book['title']}** ({year})")
            st.caption(reason)

        st.divider()
