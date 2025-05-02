# streamlit_app.py

import streamlit as st
import sqlite3, hashlib

DB_PATH = "users.db"

# ── DB 초기화 ───────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # users 테이블에 nickname 컬럼 추가
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username     TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            nickname      TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# ── 해시, CRUD 함수 ─────────────────────────────────────────────
def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def get_pw_hash(username: str) -> str | None:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def get_nickname(username: str) -> str | None:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT nickname FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def create_user(username: str, password: str, nickname: str) -> bool:
    """등록 성공하면 True, 이미 있으면 False 반환"""
    if get_pw_hash(username):
        return False
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO users (username, password_hash, nickname) VALUES (?, ?, ?)",
        (username, hash_pw(password), nickname)
    )
    conn.commit()
    conn.close()
    return True

# ── 더미 챗봇 함수 ───────────────────────────────────────────────
def get_bot_response(prompt: str) -> str:
    # 개발 중이니 echo 처리
    return f"입력하신 내용: '{prompt}' (챗봇 기능은 개발 중입니다.)"

# ── 앱 시작 ─────────────────────────────────────────────────────
init_db()

# 세션 초기값 설정
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username  = ""
    st.session_state.nickname  = ""

# ── 로그인 화면 ─────────────────────────────────────────────────
def login_screen():
    st.title("🗝 로그인")
    u = st.text_input("아이디", key="login_user")
    p = st.text_input("비밀번호", type="password", key="login_pw")
    if st.button("로그인"):
        if get_pw_hash(u) == hash_pw(p):
            st.session_state.logged_in = True
            st.session_state.username  = u
            # 로그인할 때 DB에서 nickname 불러와 세션에 저장
            st.session_state.nickname  = get_nickname(u) or u
            st.success(f"{st.session_state.nickname}님, 환영합니다!")
            st.rerun()
        else:
            st.error("아이디 또는 비밀번호가 잘못되었습니다.")

# ── 회원가입 화면 ────────────────────────────────────────────────
def register_screen():
    st.title("📝 회원가입")
    nu   = st.text_input("사용하실 아이디", key="reg_user")
    npw  = st.text_input("비밀번호", type="password", key="reg_pw")
    nnic = st.text_input("닉네임", key="reg_nick")
    if st.button("가입하기"):
        if not nu or not npw or not nnic:
            st.error("아이디, 비밀번호, 닉네임을 모두 입력해주세요.")
        elif create_user(nu, npw, nnic):
            st.success("회원가입이 완료되었습니다. 로그인해주세요.")
        else:
            st.error("이미 존재하는 아이디입니다.")

# ── 챗봇 화면 ────────────────────────────────────────────────
def chat_screen():
    st.title(f"🗨 상담 챗봇 (안녕하세요, {st.session_state.nickname}님!)")
    # 로그아웃 버튼
    if st.button("🔙 로그아웃"):
        st.session_state.logged_in = False
        st.session_state.username  = ""
        st.session_state.nickname  = ""
        st.rerun()

    msg = st.text_input("메시지를 입력하세요:", key="chat_msg")
    if st.button("전송", key="chat_send") and msg:
        with st.spinner("응답 생성 중..."):
            answer = get_bot_response(msg)
        st.text_area("챗봇 응답:", value=answer, height=200)

# ── 메인 ────────────────────────────────────────────────────────
if not st.session_state.logged_in:
    menu = st.sidebar.selectbox("메뉴", ["로그인", "회원가입"])
    if menu == "로그인":
        login_screen()
    else:
        register_screen()
else:
    chat_screen()
