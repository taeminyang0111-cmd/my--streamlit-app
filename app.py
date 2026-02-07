import streamlit as st
import requests
from openai import OpenAI

# =========================
# 기본 설정
# =========================
st.set_page_config(page_title="취향 기반 도서 추천", page_icon="📚")
st.title("📚 취향 기반 도서 추천")
st.write("독서 경험과 취향, 그리고 지금의 분위기까지 고려해 책을 추천해드려요.")

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
# Kakao Book API
# =========================
def search_kakao_books(keyword, size=3):
    try:
        res = requests.get(
            "https://dapi.kakao.com/v3/search/book",
            headers={"Authorization": f"KakaoAK {KAKAO_API_KEY}"},
            params={"query": keyword, "size": size},
            timeout=10
        )
        res.raise_for_status()
        return res.json().get("documents", [])
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
# 🧠 메인 프롬프트 (음악·영화 → 분위기 태그 강화)
# =========================
def build_main_prompt(user_input):
    return f"""
너는 한국 독서 추천 서비스의 전문 큐레이터다.
아래 사용자 정보를 종합적으로 분석하여
이 사용자에게 지금 가장 잘 맞는 책 추천 방향을 설정하라.

분석 기준:
- 독서 경험 수준과 선호 분야를 추천의 중심으로 삼는다.
- 현재 기분은 추천의 중심을 바꾸지 말고,
  책의 분위기와 접근 난이도를 조정하는 데에만 활용한다.

중요 지침 (음악/영화 취향 활용):
- 음악 취향과 영화 취향을 바탕으로
  이 사용자의 '독서 분위기 태그'를 먼저 내부적으로 정의한다.
  (예: 잔잔함, 감정 밀도, 서정적, 빠른 전개, 긴장감, 몰입감 등)
- 이후 책 추천 시,
  해당 분위기 태그와 잘 어울리는 감정선과 톤을 가진 책을 선택한다.
- 이 분위기 태그는 추천의 중심을 흔들지 않으며,
  추천의 질감과 체감 몰입도를 높이기 위한 용도로만 사용한다.

추가 지시 (안정성 확보):
1. 독서 경험이 적거나 최근에 관심이 생긴 사용자의 경우,
   반드시 끝까지 읽을 수 있을 가능성이 높은 책을 최우선으로 고려한다.
2. 사용자가 선택한 선호 분야에서 벗어나는 추천은 피한다.
3. 실험적이거나 난해하고 부담이 큰 책은 추천하지 않는다.

출력 형식 (반드시 지킬 것):
독서성향: <한 문장>
대표추천: <키워드 1개>
보조추천: <키워드 1>, <키워드 2>

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
음악·영화 취향에서 유추한 분위기와
독서 성향이 자연스럽게 어울린다는 점이
간접적으로 드러나도록
한 문장으로 설명하라.
"""

# =========================
# 질문 UI
# =========================
st.subheader("📖 독서 경험")
reading_experience = st.radio(
    "평소 책을 얼마나 자주 읽나요?",
    [
        "📚 책 읽는 걸 좋아하고 자주 읽는다",
        "🙂 가끔 읽는다",
        "😅 거의 읽지 않는다",
        "🆕 최근에 책에 관심이 생겼다"
    ]
)

st.subheader("📚 선호하는 책의 분야")
book_field = st.radio(
    "가장 관심 있는 분야를 하나 골라주세요",
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

st.subheader("🙂 현재 기분")
current_mood = st.radio(
    "요즘 당신의 상태에 가장 가까운 것은?",
    [
        "지치고 위로가 필요함",
        "차분하고 혼자 생각하고 싶음",
        "에너지가 넘치고 자극이 필요함",
        "특별한 기분은 아님"
    ]
)

st.subheader("🎶 음악 취향")
music = st.multiselect(
    "자주 듣는 음악 장르",
    ["발라드", "인디/밴드", "힙합/R&B", "팝", "클래식", "재즈"]
)

st.subheader("🎬 영화 취향")
movie = st.multiselect(
    "좋아하는 영화 장르",
    ["드라마", "로맨스", "판타지/SF", "스릴러", "액션"]
)

st.subheader("🎯 독서 목적")
goal = st.radio(
    "책을 통해 얻고 싶은 것은?",
    ["힐링 / 위로", "몰입감", "자기성찰", "공부 / 성장", "가볍게"]
)

# =========================
# 추천 실행
# =========================
if st.button("📖 도서 추천 받기"):
    user_profile = {
        "독서 경험": reading_experience,
        "선호 분야": book_field,
        "현재 기분": current_mood,
        "음악 취향": music,
        "영화 취향": movie,
        "독서 목적": goal
    }

    with st.spinner("추천 분석 중..."):
        res = client.responses.create(
            model="gpt-4o-mini",
            input=build_main_prompt(user_profile),
            temperature=0.6
        )

        lines = [l.strip() for l in res.output_text.splitlines() if l.strip()]
        profile = lines[0].replace("독서성향:", "").strip()
        main_kw = lines[1].replace("대표추천:", "").strip()

    st.success("📌 당신의 독서 성향")
    st.info(profile)

    st.subheader("⭐ 지금 가장 추천하는 책")
    books = search_kakao_books(main_kw, 3)

    for book in books:
        google_info = get_google_book_info(book["title"])
        year = book.get("datetime", "")[:4] or google_info["year"]

        reason_res = client.responses.create(
            model="gpt-4o-mini",
            input=build_reason_prompt(profile, book["title"], google_info["description"]),
            temperature=0.7
        )

        reason = reason_res.output_text.strip()

        cols = st.columns([1, 4])
        with cols[0]:
            if book.get("thumbnail"):
                st.image(book["thumbnail"], width=90)
        with cols[1]:
            st.markdown(f"**{book['title']}** ({year})")
            st.caption(reason)

        st.divider()
