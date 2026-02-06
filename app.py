import streamlit as st
import requests

st.set_page_config(page_title="AI 도서 추천", page_icon="📚", layout="centered")

st.title("📚 취향 기반 도서 추천")
st.write("몇 가지 질문에 답하면, 당신에게 어울리는 책을 추천해줄게요!")

# -----------------------------
# 1. 질문 UI 구성
# -----------------------------

reader_type = st.radio(
    "독서 경험에 가장 가까운 것은?",
    (
        "독서를 좋아하고 자주 읽는다",
        "독서를 해보고 싶지만 어떤 책부터 읽을지 모르겠다",
    ),
)

interest_fields = st.multiselect(
    "관심 있는 분야를 골라주세요 (복수 선택 가능)",
    [
        "소설",
        "에세이",
        "자기계발",
        "인문학",
        "철학",
        "경제/경영",
        "과학",
        "역사",
        "판타지",
        "추리/미스터리",
    ],
)

favorite_music = st.text_input("좋아하는 음악 장르나 아티스트가 있다면 적어주세요")
favorite_movie = st.text_input("인상 깊게 본 영화나 드라마가 있다면 적어주세요")

mood = st.selectbox(
    "요즘 읽고 싶은 책의 분위기는?",
    (
        "가볍고 편하게",
        "감정적으로 몰입되는",
        "생각할 거리를 주는",
        "동기부여가 되는",
    ),
)

# -----------------------------
# 2. 검색 키워드 생성
# -----------------------------

def build_query():
    keywords = []

    if interest_fields:
        keywords.extend(interest_fields)

    if favorite_movie:
        keywords.append(favorite_movie)

    if favorite_music:
        keywords.append(favorite_music)

    if mood == "가볍고 편하게":
        keywords.append("easy reading")
    elif mood == "감정적으로 몰입되는":
        keywords.append("emotional novel")
    elif mood == "생각할 거리를 주는":
        keywords.append("philosophy")
    elif mood == "동기부여가 되는":
        keywords.append("self improvement")

    if reader_type == "독서를 해보고 싶지만 어떤 책부터 읽을지 모르겠다":
        keywords.append("beginner")

    return " ".join(keywords)

# -----------------------------
# 3. Google Books API 호출
# -----------------------------

def fetch_books(query):
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {
        "q": query,
        "maxResults": 5,
        "printType": "books",
        "langRestrict": "ko",
    }

    response = requests.get(url, params=params, timeout=10)
    if response.status_code != 200:
        return []

    data = response.json()
    return data.get("items", [])

# -----------------------------
# 4. 추천 실행
# -----------------------------

if st.button("📖 책 추천받기"):
    query = build_query()

    if not query.strip():
        st.warning("최소 한 가지 이상은 입력해줘야 추천할 수 있어요!")
    else:
        with st.spinner("책을 찾고 있어요..."):
            books = fetch_books(query)

        if not books:
            st.error("추천할 만한 책을 찾지 못했어요 😢")
        else:
            st.subheader("✨ 당신을 위한 추천 도서")

            for book in books:
                info = book.get("volumeInfo", {})

                title = info.get("title", "제목 없음")
                authors = ", ".join(info.get("authors", ["저자 정보 없음"]))
                description = info.get("description", "설명이 없습니다")
                thumbnail = info.get("imageLinks", {}).get("thumbnail")

                st.markdown("---")
                col1, col2 = st.columns([1, 3])

                with col1:
                    if thumbnail:
                        st.image(thumbnail, use_container_width=True)

                with col2:
                    st.markdown(f"**📘 {title}**")
                    st.markdown(f"✍️ {authors}")
                    st.caption(description[:200] + "...")
