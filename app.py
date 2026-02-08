import streamlit as st
import requests
from openai import OpenAI

# =========================
# 기본 설정
# =========================
st.set_page_config(page_title="취향 기반 도서 추천", page_icon="📚")
st.title("📚 취향 기반 도서 추천")
st.write("독서 경험과 취향, 연령대와 감성까지 고려해 지금 당신에게 맞는 책을 추천해드려요.")

# =========================
# API KEY
# =========================
st.sidebar.header("🔑 API 설정")
KAKAO_API_KEY = st.sidebar.text_input("Kakao REST API Key", type="password")
OPENAI_API_KEY = st.sidebar.text_input("OpenAI API Key", type="password")

if not KAKAO_API_KEY or not OPENAI_API_KEY:
    st.info("🔑 사이드바에서 API Key를 입력해주세요.")
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)

# =========================
# ❌ 문제집 / 수험서 필터
# =========================
BANNED_KEYWORDS = [
    "문제", "기출", "토익", "토플", "수능", "자격증",
    "시험", "연습", "워크북", "Workbook", "교과서",
    "EBS", "개정", "한국사능력검정", "한능검"
]

def is_study_book(book):
    title = book.get("title", "")
    return any(bad in title for bad in BANNED_KEYWORDS)

# =========================
# Fallback 키워드 (분야별 안전망)
# =========================
FALLBACK_KEYWORDS = {
    "과학·기술": "교양 과학 입문",
    "역사": "이야기로 읽는 역사",
    "경제·경영": "경제 교양서",
    "사회·시사": "사회 이야기 책",
    "인문·철학": "쉽게 읽는 인문학"
}

# =========================
# Kakao Book API
# =========================
def search_kakao_books(keyword, size=6):
    try:
        res = requests.get(
            "https://dapi.kakao.com/v3/search/book",
            headers={"Authorization": f"KakaoAK {KAKAO_API_KEY}"},
            params={"query": keyword, "size": size},
            timeout=10
        )
        res.raise_for_status()
        books = res.json().get("documents", [])
        return [b for b in books if not is_study_book(b)]
    except requests.RequestException:
        return []

# =========================
# Google Books API
# =========================
def get_google_book_info(title):
    try:
        res = requests.get(
            "https://www.googleapis.com/books/v1/volumes",
            params={"q": title, "maxResults": 1},
            timeout=10
        )
        res.raise_for_status()
        items = res.json().get("items", [])
        if not items:
            return {"description": "", "year": ""}
        info = items[0].get("volumeInfo", {})
        return {
            "description": info.get("description", ""),
            "year": info.get("publishedDate", "")[:4]
        }
    except requests.RequestException:
        return {"description": "", "year": ""}

# =========================
# 🧠 프롬프트
# =========================
def build_main_prompt(user_input):
    return f"""
너는 한국 독서 추천 서비스의 전문 큐레이터다.

분석 원칙:
- 독서 경험과 선호 분야를 추천의 중심으로 삼는다.
- 연령대는 난이도, 관심사, 문체 톤을 조정하는 데에만 활용한다.
- 음악/영화 취향은 독서 분위기 태그로 변환해 활용한다.
- 현재 기분은 오늘 읽기 좋은 분위기만 조정한다.

중요 제한:
- 과학·기술·역사 분야에서도 문제집, 수험서, 교재는 제외한다.
- 교양서, 이야기형, 일반 독자용 책만 추천한다.
- 실험적·난해한 책은 추천하지 않는다.
- 독서 입문자는 끝까지 읽을 수 있는 책을 우선한다.

출력 형식:
독서성향: <한 문장>
대표추천: <검색 키워드 1개>

사용자 정보:
{user_input}
"""

def build_reason_prompt(profile, title, description):
    return f"""
독서 성향:
{profile}

책 제목:
{title}

책 설명:
{description}

이 사용자에게 이 책을 추천하는 이유를
한 문장으로 설명하라.
"""

def build_taste_reason_prompt(title, music, movie):
    return f"""
책 제목:
{title}

음악 취향:
{music}

영화 취향:
{movie}

이 취향에서 느껴지는 분위기와
이 책의 감정선이 왜 잘 어울리는지
한 문장으로 설명하라.
"""

# =========================
# 질문 UI
# =========================
age_group = st.radio(
    "🎂 연령대",
    ["10대", "20대 초반", "20대 후반", "30대", "40대", "50대 이상"]
)

reading_experience = st.radio(
    "📖 독서 경험",
    ["📚 자주 읽는다", "🙂 가끔 읽는다", "😅 거의 읽지 않는다", "🆕 최근 관심이 생겼다"]
)

book_field = st.radio(
    "📚 선호 분야",
    [
        "소설·문학", "에세이/시집", "자기계발", "인문·철학",
        "사회·시사", "경제·경영", "과학·기술", "역사",
        "판타지/SF", "추리·스릴러", "가볍게 읽는 교양"
    ]
)

current_mood = st.radio(
    "🙂 요즘 기분",
    ["지치고 위로가 필요함", "차분함", "에너지가 넘침", "특별한 기분은 아님"]
)

music = st.multiselect("🎶 음악 취향", ["발라드", "인디/밴드", "힙합/R&B", "팝", "클래식", "재즈"])
movie = st.multiselect("🎬 영화 취향", ["드라마", "로맨스", "판타지/SF", "스릴러", "액션"])

# =========================
# 추천 실행
# =========================
if st.button("📖 도서 추천 받기"):
    user_profile = {
        "연령대": age_group,
        "독서 경험": reading_experience,
        "선호 분야": book_field,
        "현재 기분": current_mood,
        "음악 취향": music,
        "영화 취향": movie
    }

    with st.spinner("추천 분석 중..."):
        res = client.responses.create(
            model="gpt-4o-mini",
            input=build_main_prompt(user_profile),
            temperature=0.6
        )

        lines = [l for l in res.output_text.splitlines() if l.strip()]
        profile = lines[0].replace("독서성향:", "").strip()
        keyword = lines[1].replace("대표추천:", "").strip()

    st.success("📌 당신의 독서 성향")
    st.info(profile)

    # 1차 검색
    books = search_kakao_books(keyword)

    # 🔁 fallback 검색
    if not books and book_field in FALLBACK_KEYWORDS:
        st.info("조금 더 일반적인 기준으로 다시 추천했어요 📚")
        books = search_kakao_books(FALLBACK_KEYWORDS[book_field])

    if not books:
        st.warning("현재 조건에 맞는 도서를 찾지 못했어요 😢")
        st.stop()

    for book in books[:3]:
        google = get_google_book_info(book["title"])
        year = book.get("datetime", "")[:4] or google["year"]

        reason = client.responses.create(
            model="gpt-4o-mini",
            input=build_reason_prompt(profile, book["title"], google["description"]),
            temperature=0.7
        ).output_text.strip()

        taste_reason = client.responses.create(
            model="gpt-4o-mini",
            input=build_taste_reason_prompt(book["title"], music, movie),
            temperature=0.7
        ).output_text.strip()

        cols = st.columns([1, 4])
        with cols[0]:
            if book.get("thumbnail"):
                st.image(book["thumbnail"], width=90)
        with cols[1]:
            st.markdown(f"**{book['title']}** ({year})")
            st.caption(reason)
            st.markdown(f"🎧🎬 *{taste_reason}*")

        st.divider()
