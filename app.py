import streamlit as st
import requests
from openai import OpenAI

st.set_page_config(page_title="나와 어울리는 영화는?", page_icon="🎬")

# =========================
# 사이드바 설정
# =========================
st.sidebar.title("⚙️ API & 추천 설정")

tmdb_api_key = st.sidebar.text_input("TMDB API Key", type="password")
openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")

min_rating = st.sidebar.slider("최소 평점", 0.0, 10.0, 6.5, 0.5)

year_range = st.sidebar.slider(
    "개봉 연도 범위",
    min_value=1980,
    max_value=2025,
    value=(2010, 2025),
)

movie_count = st.sidebar.selectbox(
    "추천 영화 개수",
    [3, 5, 7],
    index=1,
)

client = OpenAI(api_key=openai_api_key) if openai_api_key else None

# =========================
# 제목 & 소개
# =========================
st.title("🎬 나와 어울리는 영화는?")
st.write(
    "간단한 심리테스트로 **당신의 영화 취향을 분석**하고,\n"
    "AI가 친구처럼 이유를 설명해주는 영화 추천 서비스 🍿"
)
st.divider()

# =========================
# 장르 및 질문
# =========================
genres = {
    "로맨스/드라마": {"id": [18, 10749], "score": 0},
    "액션/어드벤처": {"id": [28], "score": 0},
    "SF/판타지": {"id": [878, 14], "score": 0},
    "코미디": {"id": [35], "score": 0},
}

questions = [
    (
        "Q1. 시험 끝난 금요일 밤, 가장 끌리는 건?",
        [
            ("조용히 감정선 깊은 영화 보기", "로맨스/드라마"),
            ("스트레스 풀리는 액션 영화", "액션/어드벤처"),
            ("현실 탈출용 세계관 영화", "SF/판타지"),
            ("아무 생각 없이 웃긴 영화", "코미디"),
        ],
    ),
    (
        "Q2. 영화에서 가장 중요한 요소는?",
        [
            ("감정과 관계", "로맨스/드라마"),
            ("속도감과 긴장감", "액션/어드벤처"),
            ("설정과 상상력", "SF/판타지"),
            ("분위기와 웃음", "코미디"),
        ],
    ),
    (
        "Q3. 끌리는 주인공 스타일은?",
        [
            ("현실적이고 섬세한 인물", "로맨스/드라마"),
            ("몸이 먼저 나가는 행동파", "액션/어드벤처"),
            ("특별한 능력을 가진 존재", "SF/판타지"),
            ("허술한데 정 가는 캐릭터", "코미디"),
        ],
    ),
    (
        "Q4. 영화가 끝났을 때 가장 좋은 느낌은?",
        [
            ("여운이 오래 남는다", "로맨스/드라마"),
            ("와… 다시 보고 싶다", "액션/어드벤처"),
            ("설정 찾아보다가 밤 샌다", "SF/판타지"),
            ("기분이 한결 가벼워진다", "코미디"),
        ],
    ),
    (
        "Q5. 추천 문구 중 제일 끌리는 건?",
        [
            ("현실 공감 제대로", "로맨스/드라마"),
            ("액션 진짜 시원함", "액션/어드벤처"),
            ("상상력 미쳤다", "SF/판타지"),
            ("생각 없이 보기 딱 좋음", "코미디"),
        ],
    ),
]

answers = []
for q, opts in questions:
    choice = st.radio(q, [o[0] for o in opts], index=None)
    answers.append((choice, opts))

st.divider()

# =========================
# LLM 추천 이유 생성 (친구 말투)
# =========================
def generate_reason(movie, user_genre):
    prompt = f"""
너는 영화 좋아하는 대학생 친구야.
말투는 너무 설명하지 말고, 자연스럽게 추천해줘.

사용자 성향: {user_genre}
영화 제목: {movie['title']}
평점: {movie['vote_average']}
줄거리: {movie['overview']}

왜 이 영화가 이 사람한테 잘 맞을지
친구가 말해주듯이 2~3문장으로 설명해줘.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "너는 친한 친구처럼 영화 추천해주는 AI야."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.8,
    )

    return response.choices[0].message.content.strip()

# =========================
# 결과 버튼
# =========================
if st.button("🎥 결과 보기"):
    if not tmdb_api_key or not openai_api_key:
        st.error("TMDB API Key와 OpenAI API Key를 모두 입력해주세요.")
    elif any(a[0] is None for a in answers):
        st.warning("모든 질문에 답해주세요!")
    else:
        # 점수 계산
        for answer, opts in answers:
            for text, genre in opts:
                if answer == text:
                    genres[genre]["score"] += 1

        best_genre = max(genres, key=lambda g: genres[g]["score"])
        genre_ids = ",".join(map(str, genres[best_genre]["id"]))

        st.subheader(f"🎯 너의 영화 취향은 **{best_genre}**")
        st.write("이 성향 기준으로, 지금 딱 보기 좋은 영화 골라봤어 👀")

        # =========================
        # TMDB Discover API
        # =========================
        url = (
            f"https://api.themoviedb.org/3/discover/movie"
            f"?api_key={tmdb_api_key}"
            f"&with_genres={genre_ids}"
            f"&vote_average.gte={min_rating}"
            f"&primary_release_date.gte={year_range[0]}-01-01"
            f"&primary_release_date.lte={year_range[1]}-12-31"
            f"&sort_by=popularity.desc"
            f"&language=ko-KR"
        )

        movies = requests.get(url).json().get("results", [])[:movie_count]

        # =========================
        # 영화 출력
        # =========================
        for m in movies:
            st.divider()
            col1, col2 = st.columns([1, 2])

            with col1:
                if m.get("poster_path"):
                    st.image(
                        "https://image.tmdb.org/t/p/w500" + m["poster_path"],
                        use_container_width=True,
                    )

            with col2:
                st.markdown(f"### 🎬 {m['title']}")
                st.write(f"⭐ 평점: {m['vote_average']}")
                st.write(m["overview"] or "줄거리 정보 없음")

                with st.spinner("친구가 추천 이유 생각 중..."):
                    reason = generate_reason(m, best_genre)

                st.success(f"💬 추천 이유\n\n{reason}")
            
