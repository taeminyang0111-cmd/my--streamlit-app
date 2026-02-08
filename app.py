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
# ❌ 문제집 / 수험서 + 아동서 + 선정성 1차 방어
# =========================
BANNED_KEYWORDS = [
    # 문제집 / 수험서
    "문제", "기출", "토익", "토플", "수능", "자격증",
    "시험", "연습", "워크북", "Workbook", "교과서",
    "EBS", "개정", "한국사능력검정", "한능검",

    # 아동 / 저연령
    "유아", "아동", "어린이", "초등", "저학년",

    # 선정성 / 과도한 성인 로맨스 (1차 방어)
    "19금", "성인", "야설", "에로", "Erotic",
    "노골적", "자극적", "금단", "욕망", "육체",
    "불륜", "치정", "베드신", "밤의", "은밀한"
]

def is_study_book(book):
    title = book.get("title", "")
    return any(bad in title for bad in BANNED_KEYWORDS)

# ========================
