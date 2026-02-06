import streamlit as st

st.set_page_config(
    page_title="취향 기반 도서 추천",
    page_icon="📚",
    layout="centered"
)

st.title("📚 취향 기반 도서 추천")
st.write("몇 가지 질문에 답하면 당신에게 맞는 책을 추천해드려요!")

st.divider()

# 1️⃣ 독서 경험 분기
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

# 2️⃣ 독서 경험자 / 입문자 분기
st.subheader("2. 독서 취향")

if reading_level.startswith("📖") or reading_level.startswith("🙂"):
    # 경험자
    recent_book = st.text_input(
        "최근에 인상 깊게 읽은 책이 있다면 적어주세요 (선택)"
    )

    favorite_genres = st.multiselect(
        "선호하는 도서 분야를 골라주세요",
        [
            "소설(한국)", "소설(해외)", "에세이", "인문·철학",
            "경제·자기계발", "과학·기술", "사회·시사",
            "역사", "판타지/SF", "추리/스릴러"
        ]
    )

    reading_point = st.multiselect(
        "책을 읽을 때 중요하게 생각하는 요소 (최대 2개)",
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
    # 입문자
    worry = st.radio(
        "책을 읽을 때 가장 걱정되는 점은?",
        [
            "너무 어려울까 봐",
            "재미없을까 봐",
            "분량이 부담될까 봐",
            "끝까지 못 읽을까 봐",
            "어떤 책을 골라야 할지 모르겠음"
        ]
    )

    preferred_contents = st.multiselect(
        "평소 더 자주 즐기는 콘텐츠는?",
        ["영화", "드라마", "웹툰", "유튜브", "음악", "팟캐스트"]
    )

st.divider()

# 3️⃣ 음악 취향
st.subheader("3. 음악 취향 🎶")

music_genres = st.multiselect(
    "좋아하는 음악 장르",
    [
        "발라드", "힙합/R&B", "인디/밴드", "팝",
        "클래식", "재즈", "OST", "EDM/일렉트로닉"
    ]
)

music_mood = st.multiselect(
    "선호하는 음악 분위기",
    [
        "감성적", "잔잔한", "에너지 넘치는",
        "우울하지만 위로되는", "어둡고 깊은",
        "밝고 희망적인"
    ],
    max_selections=2
)

st.divider()

# 4️⃣ 영화 취향
st.subheader("4. 영화 취향 🎬")

movie_genres = st.multiselect(
    "좋아하는 영화 장르",
    [
        "드라마", "로맨스", "액션",
        "판타지/SF", "범죄/스릴러",
        "다큐멘터리", "성장 영화", "예술 영화"
    ]
)

favorite_movie = st.text_input(
    "기억에 남는 영화 한 편이 있다면 적어주세요 (선택)"
)

st.divider()

# 5️⃣ 독서 목적
st.subheader("5. 독서 목적")

reading_goal = st.radio(
    "지금 책을 읽고 싶은 가장 큰 이유는?",
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

# 제출 버튼
if st.button("📖 도서 추천 받기"):
    st.success("설문이 완료되었습니다! ✨")
    st.write("아래 정보를 바탕으로 책을 추천할 수 있어요:")

    st.json({
        "독서 수준": reading_level,
        "음악 장르": music_genres,
        "음악 분위기": music_mood,
        "영화 장르": movie_genres,
        "기억에 남는 영화": favorite_movie,
        "독서 목적": reading_goal
    })
import streamlit as st
import requests

st.set_page_config(page_title="Google Books 도서 추천", page_icon="📚")

# ------------------------
# Google Books API Key
# ------------------------
GOOGLE_API_KEY = st.secrets.get("GOOGLE_BOOKS_API_KEY")

if not GOOGLE_API_KEY:
    st.error("Google Books API Key가 설정되지 않았습니다.")
    st.stop()

# ------------------------
# Google Books API 함수
# ------------------------
def search_google_books(query, max_results=10):
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {
        "q": query,
        "maxResults": max_results,
        "key": GOOGLE_API_KEY,
        "printType": "books",
        "langRestrict": "ko"
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        return []

    data = response.json()
    return data.get("items", [])

# ------------------------
# UI
# ------------------------
st.title("📚 Google Books 기반 도서 추천")
st.write("키워드를 입력하면 Google Books API를 통해 책을 검색합니다.")

query = st.text_input(
    "검색어를 입력하세요 (장르, 영화 제목, 분위기 등)",
    placeholder="예: 감성 소설, 인터스텔라, 성장 이야기"
)

if st.button("🔍 도서 검색") and query:
    books = search_google_books(query)

    if not books:
        st.warning("검색 결과가 없습니다.")
    else:
        st.subheader("📖 검색 결과")

        for book in books:
            info = book.get("volumeInfo", {})

            title = info.get("title", "제목 없음")
            authors = ", ".join(info.get("authors", ["저자 정보 없음"]))
            description = info.get("description", "설명이 없습니다.")
            thumbnail = info.get("imageLinks", {}).get("thumbnail")

            st.markdown(f"### {title}")
            st.caption(authors)
            st.write(description[:200] + "...")

            if thumbnail:
                st.image(thumbnail, width=120)

            st.divider()
