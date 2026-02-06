import streamlit as st
import requests

st.set_page_config(page_title="도서 추천 AI", layout="wide")
st.title("📚 취향 기반 도서 추천")

# =========================
# ❗❗ 질문 UI (절대 수정 X)
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
            "문장이 예쁜 책", "몰입감 있는 스토리",
            "생각할 거리를 주는 책", "가볍게 읽히는 책",
            "현실적인 이야기", "강한 메시지와 여운"
        ],
        max_selections=2
    )
else:
    worry = st.radio(
        "책을 읽을 때 가장 걱정되는 점은?",
        [
            "너무 어려울까 봐", "재미없을까 봐",
            "분량이 부담될까 봐", "끝까지 못 읽을까 봐",
            "어떤 책을 골라야 할지 모르겠음"
        ]
    )

    preferred_contents = st.multiselect(
        "평소 더 자주 즐기는 콘텐츠는?",
        ["영화", "드라마", "웹툰", "유튜브", "음악", "팟캐스트"]
    )

st.divider()
st.subheader("3. 음악 취향 🎶")

music_genres = st.multiselect(
    "좋아하는 음악 장르",
    ["발라드", "힙합/R&B", "인디/밴드", "팝", "클래식", "재즈", "OST", "EDM/일렉트로닉"]
)

music_mood = st.multiselect(
    "선호하는 음악 분위기",
    ["감성적", "잔잔한", "에너지 넘치는", "우울하지만 위로되는", "어둡고 깊은", "밝고 희망적인"],
    max_selections=2
)

st.divider()
st.subheader("4. 영화 취향 🎬")

movie_genres = st.multiselect(
    "좋아하는 영화 장르",
    ["드라마", "로맨스", "액션", "판타지/SF", "범죄/스릴러", "다큐멘터리", "성장 영화", "예술 영화"]
)

favorite_movie = st.text_input(
    "기억에 남는 영화 한 편이 있다면 적어주세요 (선택)"
)

st.divider()
st.subheader("5. 독서 목적")

reading_goal = st.radio(
    "지금 책을 읽고 싶은 가장 큰 이유는?",
    [
        "힐링 / 위로", "생각의 폭을 넓히고 싶어서",
        "재미있게 몰입하고 싶어서", "나 자신을 돌아보고 싶어서",
        "공부 / 성장 목적", "그냥 가볍게 읽고 싶어서"
    ]
)

# =========================
# 📌 추천 로직 (업그레이드)
# =========================

def build_search_query():
    keywords = []

    if favorite_genres:
        keywords.append(favorite_genres[0])

    if reading_goal:
        keywords.append(reading_goal)

    if music_mood:
        keywords.append(music_mood[0])

    if movie_genres:
        keywords.append(movie_genres[0])

    return " ".join(keywords)

def kakao_book_search(query):
    url = "https://dapi.kakao.com/v3/search/book"
    headers = {
        "Authorization": f"KakaoAK {st.secrets['KAKAO_API_KEY']}"
    }
    params = {
        "query": query,
        "size": 5,
        "sort": "accuracy"
    }
    res = requests.get(url, headers=headers, params=params)
    return res.json().get("documents", [])

def generate_reason(book):
    return (
        f"이 책은 **{reading_goal}** 목적에 잘 맞고, "
        f"당신이 선택한 **{', '.join(movie_genres[:1])} 분위기**와 "
        f"**{', '.join(music_mood[:1])} 감성**을 좋아한다는 점에서 추천했어요."
    )

# =========================
# 📖 추천 결과 출력
# =========================

if st.button("📖 도서 추천 받기"):
    st.subheader("✨ 당신을 위한 추천 도서")

    query = build_search_query()
    books = kakao_book_search(query)

    if not books:
        st.warning("추천 결과를 찾지 못했어요 😢")
    else:
        for book in books:
            with st.container():
                col1, col2 = st.columns([1, 4])

                with col1:
                    if book["thumbnail"]:
                        st.image(book["thumbnail"], width=120)

                with col2:
                    st.markdown(f"### 📘 {book['title']}")
                    st.markdown(f"**저자**: {', '.join(book['authors'])}")
                    st.markdown(f"**출판사**: {book['publisher']}")
                    st.markdown(generate_reason(book))

                    c1, c2 = st.columns(2)
                    with c1:
                        st.button("👍 마음에 들어요", key=book["isbn"] + "like")
                    with c2:
                        st.button("👎 별로예요", key=book["isbn"] + "dislike")

                st.divider()
