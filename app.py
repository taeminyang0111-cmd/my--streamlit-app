import streamlit as st
import requests

st.set_page_config(page_title="취향 기반 도서 추천", page_icon="📚")

# ------------------------
# API 설정
# ------------------------
GOOGLE_API_KEY = st.secrets["GOOGLE_BOOKS_API_KEY"]
KAKAO_API_KEY = st.secrets["KAKAO_REST_API_KEY"]

# ------------------------
# API 함수
# ------------------------
def search_google_books(query, max_results=5):
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {
        "q": query,
        "maxResults": max_results,
        "key": GOOGLE_API_KEY
    }
    res = requests.get(url, params=params).json()
    return res.get("items", [])

def search_kakao_books(query, size=5):
    url = "https://dapi.kakao.com/v3/search/book"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {"query": query, "size": size}
    res = requests.get(url, headers=headers, params=params).json()
    return res.get("documents", [])

# ------------------------
# UI
# ------------------------
st.title("📚 취향 기반 도서 추천")

st.subheader("1. 기본 취향 입력")

genre = st.multiselect(
    "선호 도서 장르",
    ["소설", "에세이", "인문", "자기계발", "SF", "판타지", "추리", "철학"]
)

music_mood = st.selectbox(
    "선호하는 분위기",
    ["감성적인", "잔잔한", "어두운", "밝은", "몰입감 있는"]
)

favorite_movie = st.text_input(
    "좋아하는 영화 (선택)"
)

st.divider()

# ------------------------
# 추천 버튼
# ------------------------
if st.button("📖 도서 추천 받기"):
    st.subheader("📌 추천 도서")

    # 검색 키워드 구성
    query_keywords = genre.copy()
    if favorite_movie:
        query_keywords.append(favorite_movie)

    query = " ".join(query_keywords)

    st.caption(f"🔎 검색 키워드: {query}")

    # Google Books
    google_books = search_google_books(query)

    # Kakao Books
    kakao_books = search_kakao_books(query)

    # ------------------------
    # 결과 출력
    # ------------------------
    st.markdown("### 📚 Google Books 추천")
    for book in google_books:
        info = book["volumeInfo"]
        st.markdown(f"**{info.get('title')}**")
        st.caption(", ".join(info.get("authors", [])))
        st.write(info.get("description", "설명 없음")[:150] + "...")
        if "imageLinks" in info:
            st.image(info["imageLinks"].get("thumbnail"))
        st.divider()

    st.markdown("### 📕 Kakao Books 추천")
    for book in kakao_books:
        st.markdown(f"**{book['title']}**")
        st.caption(", ".join(book["authors"]))
        st.write(book["contents"][:150] + "...")
        if book["thumbnail"]:
            st.image(book["thumbnail"])
        st.divider()
