import streamlit as st
import requests
from openai import OpenAI

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

KAKAO_API_KEY = st.sidebar.text_input(
    "Kakao REST API Key",
    type="password"
)

OPENAI_API_KEY = st.sidebar.text_input(
    "OpenAI API Key",
    type="password"
)

client = None
if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)

# =========================
# 📚 Kakao Book Search API
# =========================
def search_kakao_books(keyword, size=5):
    url = "https://dapi.kakao.com/v3/search/book"
    headers = {
        "Authorization": f"KakaoAK {KAKAO_API_KEY}"
    }
    params = {
        "query": keyword,
        "size": size,
        "sort": "accuracy"
    }

    response = requests.get(url, headers=headers, params=params, timeout=10)
    if response.status_code != 200:
        return []

    return response.json().get("documents", [])

# =========================
# LLM 프롬프트
# =========================
def build_prompt(user_input):
    return f"""
사용자의 취향을 바탕으로
도서 검색에 적합한 키워드 3개를 만들어주세요.

조건:
- 한국 도서 검색에 적합
- 장르 / 분위기 / 주제 중심
- 너무 추상적이지 않게

사용자 정보:
{user_input}

출력 형식:
키워드1, 키워드2, 키워드3
"""

# =========================
# ❗ 질문 UI (그대로 유지)
# =========================
st.divider()

st.subheader("1. 독서 경험")
reading_level = st.radio(
    "평소 독서 습관에 가장 가까운 것은?",
    [
        "📖 책 읽는 걸 좋아하고, 종종 읽는다",
        "🙂 가끔 읽긴 하지만 습관은 아니다",
        "😅 거의 읽지 않지만, 한번 시작해보고 싶다",
        "🆕 최근에 독서를 시작해보고 싶어졌다"
    ]
)

st.divider()
st.subheader("2. 독서 취향")

if reading_level.startswith("📖") or reading_level.startswith("🙂"):
    recent_book = st.text_input("최근에 인상 깊게 읽은 책 (선택)")
    favorite_genres = st.multiselect(
        "선호 장르",
        [
            "소설(한국)", "소설(해외)", "에세이", "인문·철학",
            "경제·자기계발", "과학·기술", "사회·시사",
            "역사", "판타지/SF", "추리/스릴러"
        ]
    )
else:
    worry = st.radio(
        "책 읽을 때 걱정되는 점",
        [
            "너무 어려울까 봐",
            "재미없을까 봐",
            "분량이 부담됨",
            "끝까지 못 읽을까 봐",
            "뭘 골라야 할지 모름"
        ]
    )

st.divider()
st.subheader("3. 음악 취향 🎶")
music_genres = st.multiselect(
    "좋아하는 음악 장르",
    ["발라드", "힙합/R&B", "인디/밴드", "팝", "클래식", "재즈"]
)

st.divider()
st.subheader("4. 영화 취향 🎬")
movie_genres = st.multiselect(
    "좋아하는 영화 장르",
    ["드라마", "로맨스", "액션", "판타지/SF", "스릴러"]
)

st.divider()
st.subheader("5. 독서 목적")
reading_goal = st.radio(
    "책을 읽고 싶은 이유",
    [
        "힐링 / 위로",
        "생각의 폭 확장",
        "몰입감",
        "자기성찰",
        "공부 / 성장",
        "가볍게"
    ]
)

# =========================
# ✅ 추천 버튼 (1개)
# =========================
if st.button("📖 도서 추천 받기", key="recommend"):
    if not KAKAO_API_KEY or not client:
        st.warning("Kakao API Key와 OpenAI API Key를 입력해주세요!")
    else:
        user_profile = {
            "독서 습관": reading_level,
            "음악 취향": music_genres,
            "영화 취향": movie_genres,
            "독서 목적": reading_goal
        }

        with st.spinner("취향 분석 중..."):
            prompt = build_prompt(user_profile)

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )

            keywords = [
                k.strip()
                for k in response.choices[0].message.content.split(",")
            ]

        st.subheader("🔍 추천 키워드")
        st.write(keywords)

        st.subheader("📚 추천 도서")
        for kw in keywords:
            books = search_kakao_books(kw)
            if not books:
                continue

            st.markdown(f"### 🔑 {kw}")
            for book in books:
                st.write(f"**{book['title']}**")
                st.caption(
                    f"저자: {', '.join(book['authors'])} | "
                    f"출판사: {book['publisher']}"
                )
                st.write("―" * 15)
