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
# 🔑 API KEY 입력 (사이드바)
# =========================
st.sidebar.header("🔑 API 설정")

KAKAO_API_KEY = st.sidebar.text_input(
    "Kakao REST API Key",
    type="password",
    placeholder="카카오 REST API 키"
)

OPENAI_API_KEY = st.sidebar.text_input(
    "OpenAI API Key",
    type="password",
    placeholder="sk-..."
)

if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

# =========================
# Kakao 도서 검색 API 함수
# =========================
def search_kakao_books(query, size=5):
    url = "https://dapi.kakao.com/v3/search/book"

    headers = {
        "Authorization": f"KakaoAK {KAKAO_API_KEY}"
    }

    params = {
        "query": query,
        "size": size,
        "target": "title"
    }

    response = requests.get(url, headers=headers, params=params, timeout=10)
    if response.status_code != 200:
        return []

    return response.json().get("documents", [])

# =========================
# LLM 프롬프트 생성
# =========================
def build_prompt(user_input):
    return f"""
사용자의 취향을 바탕으로
한국 도서 검색에 적합한 키워드 3개를 만들어주세요.

조건:
- 너무 추상적이지 않게
- 장르 / 분위기 / 주제 중심
- 실제 서점 검색에 쓸 수 있는 단어

사용자 정보:
{user_input}

출력 형식:
키워드1, 키워드2, 키워드3
"""

# =========================
# 질문 UI
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
    favorite_genres = st.multiselect(
        "선호하는 도서 분야",
        ["소설", "에세이", "인문·철학", "자기계발", "판타지/SF", "추리"]
    )
else:
    worry = st.radio(
        "책 읽을 때 가장 걱정되는 점",
        ["어려울까 봐", "재미없을까 봐", "분량이 부담"]
    )

st.divider()

st.subheader("3. 음악 취향 🎶")
music_genres = st.multiselect(
    "좋아하는 음악 장르",
    ["발라드", "인디", "팝", "힙합/R&B", "OST"]
)

st.divider()

st.subheader("4. 영화 취향 🎬")
movie_genres = st.multiselect(
    "좋아하는 영화 장르",
    ["드라마", "로맨스", "판타지/SF", "성장 영화", "스릴러"]
)

st.divider()

st.subheader("5. 독서 목적")
reading_goal = st.radio(
    "책을 읽고 싶은 이유",
    ["힐링 / 위로", "재미와 몰입", "생각의 확장", "자기 성장", "가볍게 읽기"]
)

st.divider()

# =========================
# ✅ 최종 추천 버튼 (하나만!)
# =========================
if st.button("📖 도서 추천 받기", key="recommend_final"):

    if not KAKAO_API_KEY or not OPENAI_API_KEY:
        st.warning("API Key를 모두 입력해주세요!")
        st.stop()

    user_profile = {
        "독서 습관": reading_level,
        "음악 취향": music_genres,
        "영화 취향": movie_genres,
        "독서 목적": reading_goal
    }

    st.success("설문 완료! 취향을 분석 중이에요 ✨")
    st.json(user_profile)

    # 🔹 LLM 키워드 생성
    with st.spinner("추천 키워드 생성 중..."):
        prompt = build_prompt(user_profile)

        response = openai.ChatCompletion.create(
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

    # 🔹 Kakao 도서 추천
    st.subheader("📚 추천 도서")

    for kw in keywords:
        books = search_kakao_books(kw)
        if not books:
            continue

        st.markdown(f"### 🔑 {kw}")
        for book in books:
            st.markdown(f"**📘 {book['title']}**")
            st.caption(f"저자: {', '.join(book['authors'])}")
            st.write(book["contents"][:150] + "...")
            if book["thumbnail"]:
                st.image(book["thumbnail"], width=120)
            st.write("―" * 20)
