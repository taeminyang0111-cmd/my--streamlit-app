import streamlit as st
import requests
from openai import OpenAI

# =========================
# 기본 설정
# =========================
st.set_page_config(page_title="취향 기반 도서 추천", page_icon="📚")
st.title("📚 취향 기반 도서 추천")
st.write("몇 가지 질문에 답하면 당신에게 맞는 책을 추천해드려요.")

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
# 문제집 필터 / fallback
# =========================
BANNED_KEYWORDS = [
    "문제", "기출", "토익", "토플", "수능", "자격증",
    "시험", "연습", "워크북", "Workbook", "교과서",
    "EBS", "개정", "한국사능력검정", "한능검"
]

FALLBACK_KEYWORDS = {
    "과학·기술": "교양 과학 입문",
    "역사": "이야기로 읽는 역사",
    "경제·경영": "경제 교양서",
    "사회·시사": "사회 이야기 책",
    "인문·철학": "쉽게 읽는 인문학"
}

def is_study_book(book):
    return any(bad in book.get("title", "") for bad in BANNED_KEYWORDS)

def search_kakao_books(keyword, size=3):
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
    except:
        return []

# =========================
# 🧠 메인 프롬프트 (기존 유지 + 2-레벨 추가)
# =========================
def build_keyword_prompt(user_input):
    return f"""
너는 한국 독서 추천 서비스의 전문 큐레이터다.

아래 사용자 정보를 종합적으로 분석하여
이 사용자에게 지금 가장 잘 맞는
'독서용 도서 검색 키워드'를 설계하라.

분석 기준:
- 독서 경험 수준과 선호 분야를 추천의 중심으로 삼는다.
- 연령대는 추천의 중심을 바꾸지 말고,
  해당 연령대에서 공감하기 쉬운 난이도, 관심사, 문체 톤을 조정하는 데에만 활용한다.
- 음악 취향과 영화 취향은
  사용자의 감정선과 선호 분위기를 추정하는 보조 신호로 활용한다.
- 현재 기분은 추천의 중심을 바꾸지 말고,
  오늘 읽기 좋은 분위기와 접근 난이도를 조정하는 데에만 활용한다.

중요 제한 조건:
- 과학·기술·역사·경제 분야에서도
  문제집, 수험서, 교재, 시험 대비용 도서는 제외한다.
- 일반 독자를 위한 교양서, 이야기형, 에세이형 책을 우선한다.
- 실험적이거나 난해하고 부담이 큰 책은 추천하지 않는다.
- 독서 입문자나 최근 관심이 생긴 사용자의 경우,
  반드시 끝까지 읽을 수 있을 가능성이 높은 책을 최우선으로 고려한다.

[출력 키워드 설계 방식 – 중요]
- 키워드는 역할에 따라 나누어 제시한다.

1) 대표추천:
   - 이 사용자의 선호 분야 안에서
     비교적 안정적이고 무난한 중심 키워드 1개

2) 변주추천:
   - 연령대, 현재 기분, 음악/영화 취향을 반영한
     개인화 키워드 2개
   - 두 키워드는 서로 성격이 겹치지 않도록 한다
   - 대표추천과는 다른 결을 갖도록 한다

출력 형식 (반드시 지킬 것):
대표추천: <키워드 1개>
변주추천: <키워드 1>, <키워드 2>

사용자 정보:
{user_input}
"""

# =========================
# ❓ 질문 UI (원래 버전 그대로)
# =========================
age_group = st.radio(
    "🎂 연령대",
    ["10대", "20대 초반", "20대 후반", "30대", "40대", "50대 이상"]
)

reading_experience = st.radio(
    "📖 평소 책을 얼마나 자주 읽나요?",
    [
        "📚 책 읽는 걸 좋아하고 자주 읽는다",
        "🙂 가끔 읽는다",
        "😅 거의 읽지 않는다",
        "🆕 최근에 책에 관심이 생겼다"
    ]
)

book_field = st.radio(
    "📚 선호하는 책의 분야",
    [
        "소설·문학",
        "에세이/시집",
        "자기계발",
        "인문·철학",
        "사회·시사",
        "경제·경영",
        "과학·기술",
        "역사",
        "판타지/SF",
        "추리·스릴러",
        "가볍게 읽는 교양"
    ]
)

current_mood = st.radio(
    "🙂 요즘 기분은 어떤가요?",
    [
        "지치고 위로가 필요함",
        "차분하고 혼자 생각하고 싶음",
        "에너지가 넘치고 자극이 필요함",
        "특별한 기분은 아님"
    ]
)

music = st.multiselect(
    "🎶 좋아하는 음악 장르",
    ["발라드", "인디/밴드", "힙합/R&B", "팝", "클래식", "재즈"]
)

movie = st.multiselect(
    "🎬 좋아하는 영화 장르",
    ["드라마", "로맨스", "판타지/SF", "스릴러", "액션"]
)

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

    with st.spinner("취향 분석 중..."):
        kw_text = client.responses.create(
            model="gpt-4o-mini",
            input=build_keyword_prompt(user_profile),
            temperature=0.7
        ).output_text

        lines = [l for l in kw_text.splitlines() if l.strip()]
        main_kw = lines[0].replace("대표추천:", "").strip()
        var_kws = [k.strip() for k in lines[1].replace("변주추천:", "").split(",")]

    st.subheader("🔍 추천 기준 키워드")
    st.write("대표 키워드:", main_kw)
    st.write("변주 키워드:", var_kws)

    st.divider()
    st.subheader("📚 추천 도서")

    books = []
    books += search_kakao_books(main_kw, 2)[:1]
    for kw in var_kws:
        books += search_kakao_books(kw, 1)

    if not books and book_field in FALLBACK_KEYWORDS:
        st.info("조금 더 일반적인 기준으로 다시 추천했어요 📚")
        books = search_kakao_books(FALLBACK_KEYWORDS[book_field], 3)

    if not books:
        st.warning("조건에 맞는 도서를 찾지 못했어요 😢")
        st.stop()

    for book in books:
        cols = st.columns([1, 4])
        with cols[0]:
            if book.get("thumbnail"):
                st.image(book["thumbnail"], width=90)
        with cols[1]:
            st.markdown(f"**{book['title']}**")
            st.caption(f"저자: {', '.join(book['authors'])} | 출판사: {book['publisher']}")

        st.divider()
