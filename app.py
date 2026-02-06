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
st.write("몇 가지 질문에 답하면, 지금 당신에게 가장 잘 맞는 책을 추천해드려요.")

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
    except requests.RequestException as e:
        st.error(f"Kakao API 오류: {e}")
        return []

# =========================
# 🧠 프롬프트 (리디자인)
# =========================
def build_prompt(user_input):
    return f"""
너는 한국 독서 추천 서비스의 전문 큐레이터다.
아래 사용자 정보를 종합적으로 분석하여
"이 사용자에게 지금 가장 잘 맞는 독서 방향"을 먼저 정의한 뒤,
그 방향에 맞는 도서 검색 키워드를 만들어라.

작업 단계는 반드시 아래 순서를 따른다.

[1단계] 독서 성향 요약
- 사용자 정보를 종합해 한 문장으로 요약한다
- 독서 난이도 / 분위기 / 목적이 모두 드러나야 한다
- 설명체가 아닌 '라벨' 형태로 작성한다

[2단계] 추천 중심 설정
- 이 사용자에게 가장 적합한 추천 방향을 하나만 정한다
- 장르 + 분위기 + 독서 경험을 모두 반영한다

[3단계] 도서 검색 키워드 생성
- 실제 한국 온라인 서점에서 많이 쓰이는 표현
- 키워드는 2~4단어 이내
- 추상적인 단어 단독 사용 금지

출력 규칙:
- 줄바꿈 외 추가 설명 금지
- 아래 형식을 정확히 유지할 것

출력 형식:
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

favorite_genres = []
worry = None

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
# ✅ 추천 버튼
# =========================
if st.button("📖 도서 추천 받기"):
    user_profile = {
        "독서 습관": reading_level,
        "선호 장르": favorite_genres or None,
        "독서 고민": worry,
        "음악 취향": music_genres,
        "영화 취향": movie_genres,
        "독서 목적": reading_goal
    }

    with st.spinner("취향 분석 중..."):
        prompt = build_prompt(user_profile)

        response = client.responses.create(
            model="gpt-4o-mini",
            input=prompt,
            temperature=0.6
        )

        raw_text = response.output_text or ""
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

        if len(lines) < 3:
            st.error("추천 결과를 생성하지 못했어요. 다시 시도해주세요 🙏")
            st.stop()

        profile = lines[0].replace("독서성향:", "").strip()
        main_keyword = lines[1].replace("대표추천:", "").strip()
        sub_keywords = [
            k.strip()
            for k in lines[2].replace("보조추천:", "").split(",")
        ]

    # =========================
    # 📌 결과 출력
    # =========================
    st.success("📌 당신의 독서 성향")
    st.info(profile)

    st.subheader("⭐ 지금 가장 추천하는 책")
    main_books = search_kakao_books(main_keyword, size=5)

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

    for kw in sub_keywords:
        st.markdown(f"### 🔑 {kw}")
        books = search_kakao_books(kw, size=3)

        if not books:
            st.caption("관련 도서를 찾지 못했어요 😢")
            continue

        for book in books:
            st.write(f"- **{book['title']}** ({', '.join(book['authors'])})")
