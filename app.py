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

# =========================
# 🔑 사이드바: API Key 입력
# =========================
st.sidebar.header("🔑 API 설정")

GOOGLE_API_KEY = st.sidebar.text_input(
    "Google Books API Key (선택)",
    type="password",
    placeholder="AIza..."
)

OPENAI_API_KEY = st.sidebar.text_input(
    "OpenAI API Key (LLM 추천 이유 생성)",
    type="password",
    placeholder="sk-..."
)

st.sidebar.caption(
    "• Google Books API는 키 없이도 동작합니다.\n"
    "• OpenAI API Key는 추천 이유 생성에 사용됩니다."
)

# =========================
# Google Books API 함수
# =========================
def search_google_books(query, max_results=5):
    url = "https://www.googleapis.com/books/v1/volumes"

    params = {
        "q": query,
        "maxResults": max_results,
        "printType": "books",
        "langRestrict": "ko",
    }

    if GOOGLE_API_KEY:
        params["key"] = GOOGLE_API_KEY

    response = requests.get(url, params=params, timeout=10)
    if response.status_code != 200:
        return []

    return response.json().get("items", [])

# =========================
# LLM 추천 이유 생성 함수
# =========================
def generate_recommend_reason(user_profile, book_info):
    if not OPENAI_API_KEY:
        return "🔒 OpenAI API Key가 없어 추천 이유를 생성하지 못했어요."

    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"""
너는 독서 큐레이터야.
아래 사용자 정보와 책 정보를 보고,
왜 이 책이 이 사용자에게 어울리는지
친구에게 말해주듯 2~3문장으로 설명해줘.

[사용자 정보]
{user_profile}

[책 정보]
제목: {book_info['title']}
저자: {book_info['authors']}
설명: {book_info['description']}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    return response.choices[0].message.content

# =========================
# 메인 UI (질문부 – 원본 유지)
# =========================
st.title("📚 취향 기반 도서 추천")
st.write("몇 가지 질문에 답하면 당신에게 맞는 책을 추천해드려요!")

st.divider()

# 1️⃣ 독서 경험
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

# 2️⃣ 독서 취향
st.subheader("2. 독서 취향")

if reading_level.startswith("📖") or reading_level.startswith("🙂"):
    recent_book = st.text_input("최근에 인상 깊게 읽은 책 (선택)")

    favorite_genres = st.multiselect(
        "선호 도서 분야",
        [
            "소설(한국)", "소설(해외)", "에세이", "인문·철학",
            "경제·자기계발", "과학·기술", "사회·시사",
            "역사", "판타지/SF", "추리/스릴러"
        ]
    )

    reading_point = st.multiselect(
        "중요하게 생각하는 요소 (최대 2개)",
        [
            "문장이 예쁜 책",
            "몰입감 있는 스토리",
            "생각할 거리를 주는 책",
            "가볍게 읽히는 책",
            "현실적인 이야기",
            "강한 메시지와 여운"
        ],
        max_selections=2
    )
else:
    worry = st.radio(
        "책을 읽을 때 가장 걱정되는 점",
        [
            "너무 어려울까 봐",
            "재미없을까 봐",
            "분량이 부담될까 봐",
            "끝까지 못 읽을까 봐",
            "어떤 책을 골라야 할지 모르겠음"
        ]
    )

    preferred_contents = st.multiselect(
        "평소 더 자주 즐기는 콘텐츠",
        ["영화", "드라마", "웹툰", "유튜브", "음악", "팟캐스트"]
    )

st.divider()

# 3️⃣ 음악 취향
st.subheader("3. 음악 취향 🎶")
music_genres = st.multiselect(
    "좋아하는 음악 장르",
    ["발라드", "힙합/R&B", "인디/밴드", "팝", "클래식", "재즈", "OST", "EDM"]
)

music_mood = st.multiselect(
    "선호 음악 분위기",
    ["감성적", "잔잔한", "에너지 넘치는", "우울하지만 위로되는", "어둡고 깊은", "밝고 희망적인"],
    max_selections=2
)

st.divider()

# 4️⃣ 영화 취향
st.subheader("4. 영화 취향 🎬")
movie_genres = st.multiselect(
    "좋아하는 영화 장르",
    ["드라마", "로맨스", "액션", "판타지/SF", "범죄/스릴러", "다큐", "성장 영화", "예술 영화"]
)

favorite_movie = st.text_input("기억에 남는 영화 (선택)")

st.divider()

# 5️⃣ 독서 목적
st.subheader("5. 독서 목적")
reading_goal = st.radio(
    "지금 책을 읽고 싶은 이유",
    [
        "힐링 / 위로",
        "생각의 폭을 넓히고 싶어서",
        "재미있게 몰입하고 싶어서",
        "나 자신을 돌아보고 싶어서",
        "공부 / 성장 목적",
        "그냥 가볍게 읽고 싶어서"
    ]
)

st.divider()

# =========================
# 추천 실행
# =========================
if st.button("📖 도서 추천 받기"):
    user_profile = f"""
독서 수준: {reading_level}
독서 목적: {reading_goal}
음악 장르: {', '.join(music_genres)}
음악 분위기: {', '.join(music_mood)}
영화 장르: {', '.join(movie_genres)}
기억에 남는 영화: {favorite_movie}
"""

    query = f"{reading_goal} {favorite_movie} {' '.join(movie_genres)}"

    with st.spinner("책을 찾고 있어요..."):
        books = search_google_books(query)

    if not books:
        st.warning("추천할 책을 찾지 못했어요 😢")
    else:
        st.subheader("✨ 당신을 위한 도서 추천")

        for book in books[:3]:
            info = book.get("volumeInfo", {})
            title = info.get("title", "제목 없음")
            authors = ", ".join(info.get("authors", ["저자 정보 없음"]))
            description = info.get("description", "설명 없음")
            thumbnail = info.get("imageLinks", {}).get("thumbnail")

            reason = generate_recommend_reason(
                user_profile,
                {
                    "title": title,
                    "authors": authors,
                    "description": description
                }
            )

            st.markdown("---")
            cols = st.columns([1, 3])

            with cols[0]:
                if thumbnail:
                    st.image(thumbnail, use_container_width=True)

            with cols[1]:
                st.markdown(f"### 📘 {title}")
                st.caption(f"✍️ {authors}")
                st.write(reason)
