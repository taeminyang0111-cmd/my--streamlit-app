import streamlit as st
import requests

st.set_page_config(
    page_title="취향 기반 도서 추천",
    page_icon="📚",
    layout="centered"
)

# =========================
# 🔑 사이드바: API Key 입력
# =========================
st.sidebar.header("🔑 Google Books API")
GOOGLE_API_KEY = st.sidebar.text_input(
    "Google Books API Key를 입력하세요",
    type="password",
    placeholder="AIza..."
)

st.sidebar.caption(
    "※ Google Books API는 키 없이도 동작하지만\n"
    "할당량/안정성을 위해 키 사용을 권장해요."
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

    # 👉 API Key가 있으면 params에 추가
    if GOOGLE_API_KEY:
        params["key"] = GOOGLE_API_KEY

    response = requests.get(url, params=params, timeout=10)

    if response.status_code != 200:
        return []

    return response.json().get("items", [])

# =========================
# 메인 UI
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
    favorite_genres = st.multiselect(
        "선호하는 도서 분야",
        [
            "소설", "에세이", "인문·철학",
            "경제·자기계발", "과학", "판타지/SF", "추리"
        ]
    )
else:
    preferred_contents = st.multiselect(
        "평소 더 자주 즐기는 콘텐츠",
        ["영화", "드라마", "웹툰", "유튜브", "음악"]
    )

st.divider()

# 3️⃣ 영화/음악
movie = st.text_input("기억에 남는 영화 (선택)")
music = st.text_input("좋아하는 음악/아티스트 (선택)")

st.divider()

# 4️⃣ 독서 목적
reading_goal = st.radio(
    "독서 목적",
    [
        "힐링", "몰입", "성장", "생각 확장", "가볍게"
    ]
)

# =========================
# 추천 버튼
# =========================
if st.button("📖 도서 추천 받기"):
    keywords = " ".join(
        favorite_genres if reading_level.startswith(("📖", "🙂")) else []
    ) + f" {movie} {music} {reading_goal}"

    if not keywords.strip():
        st.warning("추천을 위해 최소한의 정보를 입력해주세요!")
    else:
        with st.spinner("책을 찾고 있어요..."):
            books = search_google_books(keywords)

        if not books:
            st.error("추천할 책을 찾지 못했어요 😢")
        else:
            st.subheader("✨ 추천 도서")

            for book in books:
                info = book.get("volumeInfo", {})
                title = info.get("title", "제목 없음")
                authors = ", ".join(info.get("authors", ["저자 정보 없음"]))
                desc = info.get("description", "설명 없음")
                thumb = info.get("imageLinks", {}).get("thumbnail")

                st.markdown("---")
                cols = st.columns([1, 3])

                with cols[0]:
                    if thumb:
                        st.image(thumb, use_container_width=True)

                with cols[1]:
                    st.markdown(f"**📘 {title}**")
                    st.caption(f"✍️ {authors}")
                    st.write(desc[:200] + "...")
