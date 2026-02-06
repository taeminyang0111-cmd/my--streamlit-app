import streamlit as st
import requests
from openai import OpenAI
from datetime import datetime

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

CURRENT_YEAR = datetime.now().year

# =========================
# 🔑 API KEY 입력
# =========================
st.sidebar.header("🔑 API 설정")

KAKAO_API_KEY = st.sidebar.text_input("Kakao REST API Key", type="password")
OPENAI_API_KEY = st.sidebar.text_input("OpenAI API Key", type="password")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# =========================
# 📚 Kakao Book Search API
# =========================
def search_kakao_books(keyword, year_range, size=10):
    if not KAKAO_API_KEY:
        return []

    try:
        response = requests.get(
            "https://dapi.kakao.com/v3/search/book",
            headers={"Authorization": f"KakaoAK {KAKAO_API_KEY}"},
            params={
                "query": keyword,
                "size": size,
                "sort": "accuracy"
            },
            timeout=10
        )
        response.raise_for_status()

        books = response.json().get("documents", [])
        filtered = []

        for book in books:
            if not book.get("datetime"):
                continue

            publish_year = int(book["datetime"][:4])
            if year_range[0] <= publish_year <= year_range[1]:
                filtered.append(book)

        return filtered

    except requests.RequestException:
        return []

# =========================
# 🧠 LLM 프롬프트
# =========================
def build_prompt(user_input):
    return f"""
아래 사용자 정보를 바탕으로
카카오 도서 검색에 바로 사용할 수 있는
구체적인 한국어 검색 키워드 3개를 만들어주세요.

조건:
- 한국 서점에서 실제로 많이 쓰이는 표현
- 장르 / 분위기 / 주제 중심
- 한 키워드는 2~4단어 이내
- 추상적인 단어 단독 사용 금지

사용자 정보:
{user_input}

출력 형식:
키워드1, 키워드2, 키워드3
"""

# =========================
# ❗ 질문 UI
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

if reading_level.startswith(("📖", "🙂")):
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

# =========================
# 📅 출판 연도 선택 (🔥 추가)
# =========================
st.divider()
st.subheader("📅 출판 연도 선호")

year_range = st.slider(
    "읽고 싶은 책의 출판 연도 범위를 선택하세요",
    min_value=1980,
    max_value=CURRENT_YEAR,
    value=(2018, CURRENT_YEAR)
)

st.caption(f"선택한 범위: {year_range[0]}년 ~ {year_range[1]}년")

# =========================
# 취향 보조 질문
# =========================
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
    ["힐링 / 위로", "생각의 폭 확장", "몰입감", "자기성찰", "가볍게"]
)

# =========================
# ✅ 추천 버튼
# =========================
if st.button("📖 도서 추천 받기"):
    if not KAKAO_API_KEY or not client:
        st.warning("Kakao API Key와 OpenAI API Key를 모두 입력해주세요!")
    else:
        user_profile = {
            "독서 습관": reading_level,
            "선호 장르": favorite_genres if reading_level.startswith(("📖", "🙂")) else None,
            "독서 고민": worry if not reading_level.startswith(("📖", "🙂")) else None,
            "출판 연도 선호": f"{year_range[0]}~{year_range[1]}",
            "음악 취향": music_genres,
            "영화 취향": movie_genres,
            "독서 목적": reading_goal
        }

        with st.spinner("취향 분석 중..."):
            response = client.responses.create(
                model="gpt-4o-mini",
                input=build_prompt(user_profile),
                temperature=0.7
            )

            keywords = list(dict.fromkeys(
                [k.strip() for k in response.output_text.split(",") if k.strip()]
            ))[:3]

        st.subheader("🔍 추천 키워드")
        st.write(keywords)

        st.subheader("📚 추천 도서")

        for kw in keywords:
            books = search_kakao_books(kw, year_range)

            st.markdown(f"### 🔑 {kw}")

            if not books:
                st.caption("해당 연도 범위의 도서를 찾지 못했어요 😢")
                continue

            for book in books:
                cols = st.columns([1, 4])

                with cols[0]:
                    if book.get("thumbnail"):
                        st.image(book["thumbnail"], width=90)

                with cols[1]:
                    year = book["datetime"][:4] if book.get("datetime") else "미상"
                    st.write(f"**{book['title']}** ({year})")
                    st.caption(
                        f"저자: {', '.join(book['authors'])} | 출판사: {book['publisher']}"
                    )

            st.divider()
