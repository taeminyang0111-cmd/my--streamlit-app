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
st.write("연령과 취향을 함께 고려해, 지금 당신에게 가장 잘 맞는 책을 추천해드려요.")

# =========================
# 🔑 API KEY 입력
# =========================
st.sidebar.header("🔑 API 설정")

KAKAO_API_KEY = st.sidebar.text_input("Kakao REST API Key", type="password")
OPENAI_API_KEY = st.sidebar.text_input("OpenAI API Key", type="password")

if not KAKAO_API_KEY or not OPENAI_API_KEY:
    st.info("🔑 사이드바에서 Kakao API Key와 OpenAI API Key를 입력해주세요.")
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)

# =========================
# 📚 Kakao Book Search API
# =========================
def search_kakao_books(keyword, size=5):
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
        return response.json().get("documents", [])
    except requests.RequestException:
        return []

# =========================
# 🧠 프롬프트 (연령 + 음악 + 영화 반영)
# =========================
def build_prompt(user_input):
    return f"""
너는 한국 독서 추천 서비스의 전문 큐레이터다.
아래 사용자 정보를 종합적으로 분석하여,
특히 '연령대에 따른 독서 성향'을 가장 중요하게 고려하고,
음악과 영화 취향은 감성적 성향을 파악하는 보조 신호로 활용해
이 사용자에게 지금 가장 잘 맞는 책 추천 방향을 설정하라.

[1단계] 독서 성향 요약
- 연령대, 독서 습관, 독서 목적을 중심으로 요약한다
- 음악/영화 취향은 분위기와 몰입 성향 보완용으로 반영한다
- 한 문장, 라벨 형태로 작성한다

[2단계] 추천 중심 설정
- 해당 연령대 독자에게 실제로 많이 선택되는 책 유형을 기준으로 한다
- 장르 + 분위기 + 독서 경험을 종합해
- 지금 이 사람에게 가장 먼저 추천할 방향을 하나만 정한다

[3단계] 도서 검색 키워드 생성
- 실제 한국 온라인 서점에서 자주 쓰이는 표현
- 키워드는 2~4단어 이내
- 추상적인 단어 단독 사용 금지

출력 형식 (반드시 지킬 것):
독서성향: <한 문장>
대표추천: <키워드 1개>
보조추천: <키워드 1>, <키워드 2>

사용자 정보:
{user_input}
"""

# =========================
# ❗ 질문 UI
# =========================
st.divider()
st.subheader("0. 연령대")

age_group = st.radio(
    "본인의 연령대에 가장 가까운 것은?",
    ["10대", "20대 초반", "20대 후반", "30대", "40대", "50대 이상"]
)

st.divider()
st.subheader("1. 독서 경험")

reading_level = st.radio(
    "평소 독서 습관은?",
    [
        "📖 자주 읽는다",
        "🙂 가끔 읽는다",
        "😅 거의 안 읽는다",
        "🆕 최근 관심이 생겼다"
    ]
)

st.divider()
st.subheader("2. 음악 취향 🎶")

music_genres = st.multiselect(
    "좋아하는 음악 장르",
    ["발라드", "힙합/R&B", "인디/밴드", "팝", "클래식", "재즈"]
)

st.divider()
st.subheader("3. 영화 취향 🎬")

movie_genres = st.multiselect(
    "좋아하는 영화 장르",
    ["드라마", "로맨스", "액션", "판타지/SF", "스릴러"]
)

st.divider()
st.subheader("4. 독서 목적")

reading_goal = st.radio(
    "책을 읽고 싶은 이유",
    [
        "힐링 / 위로",
        "몰입감",
        "자기성찰",
        "공부 / 성장",
        "가볍게"
    ]
)

# =========================
# ✅ 추천 실행
# =========================
if st.button("📖 도서 추천 받기"):
    user_profile = {
        "연령대": age_group,
        "독서 습관": reading_level,
        "음악 취향": music_genres,
        "영화 취향": movie_genres,
        "독서 목적": reading_goal
    }

    with st.spinner("취향 분석 중..."):
        response = client.responses.create(
            model="gpt-4o-mini",
            input=build_prompt(user_profile),
            temperature=0.6
        )

        raw_text = response.output_text or ""
        lines = [l.strip() for l in raw_text.splitlines() if l.strip()]

        if len(lines) < 3:
            st.error("추천 결과를 생성하지 못했어요. 다시 시도해주세요 🙏")
            st.stop()

        profile = lines[0].replace("독서성향:", "").strip()
        main_kw = lines[1].replace("대표추천:", "").strip()
        sub_kws = [k.strip() for k in lines[2].replace("보조추천:", "").split(",")]

    # =========================
    # 📌 결과 출력
    # =========================
    st.success("📌 당신의 독서 성향")
    st.info(profile)

    st.subheader("⭐ 지금 가장 추천하는 책")
    main_books = search_kakao_books(main_kw, size=5)

    if not main_books:
        st.caption("관련 도서를 찾지 못했어요 😢")

    for book in main_books:
        cols = st.columns([1, 4])
        with cols[0]:
            if book.get("thumbnail"):
                st.image(book["thumbnail"], width=90)
        with cols[1]:
            st.write(f"**{book['title']}**")
            st.caption(f"저자: {', '.join(book['authors'])} | 출판사: {book['publisher']}")

    st.divider()
    st.subheader("🔍 이런 취향도 함께 고려했어요")

    for kw in sub_kws:
        st.markdown(f"### 🔑 {kw}")
        for book in search_kakao_books(kw, size=3):
            st.write(f"- **{book['title']}** ({', '.join(book['authors'])})")
