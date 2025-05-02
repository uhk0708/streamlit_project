# streamlit_app.py

import streamlit as st
import sqlite3, hashlib
import streamlit.components.v1 as components

DB_PATH = "users.db"

# ── DB 초기화 ───────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # users 테이블 (이미 있으면 건너뜀)
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username      TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL
        )
    """)
    # 닉네임 컬럼이 없으면 추가
    try:
        c.execute("ALTER TABLE users ADD COLUMN nickname TEXT")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

# ── 해시 및 CRUD 함수 ────────────────────────────────────────────
def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def get_pw_hash(username: str):
    row = sqlite3.connect(DB_PATH).execute(
        "SELECT password_hash FROM users WHERE username=?", (username,)
    ).fetchone()
    return row[0] if row else None

def get_nickname(username: str):
    row = sqlite3.connect(DB_PATH).execute(
        "SELECT nickname FROM users WHERE username=?", (username,)
    ).fetchone()
    return row[0] if row else None

def create_user(username: str, password: str, nickname: str) -> bool:
    if get_pw_hash(username):
        return False
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO users (username, password_hash, nickname) VALUES (?, ?, ?)",
        (username, hash_pw(password), nickname)
    )
    conn.commit(); conn.close()
    return True

# ── 더미 챗봇 응답 (개발 중) ────────────────────────────────────
def get_bot_response(msg: str) -> str:
    return f"에코: {msg} (챗봇 로직은 곧 연결됩니다)"

# ── 앱 초기화 & 세션 초기값 ──────────────────────────────────────
init_db()
for key, val in {
    "page": "login",          # login / register / chat
    "logged_in": False,
    "signup_success": False,
    "username": "",
    "nickname": ""
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ── 로그인 페이지 ───────────────────────────────────────────────
def login_page():
    # 가운데 정렬
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.title("🗝 로그인")
        if st.session_state.signup_success:
            st.success("회원가입이 완료되었습니다. 로그인해주세요.")
            st.session_state.signup_success = False

        user = st.text_input("아이디", key="login_user")
        pw   = st.text_input("비밀번호", type="password", key="login_pw")

        # 로그인 시도
        if st.button("로그인"):
            if get_pw_hash(user) == hash_pw(pw):
                st.session_state.logged_in = True
                st.session_state.username  = user
                st.session_state.nickname  = get_nickname(user) or user
                st.session_state.page = "chat"
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호가 잘못되었습니다.")

        # 회원가입 페이지로 이동
        if st.button("회원가입"):
            st.session_state.page = "register"
            st.rerun()

# ── 회원가입 페이지 ────────────────────────────────────────────
def register_page():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.title("📝 회원가입")
        # 로그인 화면으로 돌아가기 버튼
        if st.button("← 로그인으로 돌아가기"):
            st.session_state.page = "login"
            # 필요한 경우 입력 필드 초기화
            st.session_state.reg_user = ""
            st.session_state.reg_pw   = ""
            st.session_state.reg_nick = ""
            st.rerun()
        new_user = st.text_input("사용하실 아이디", key="reg_user")
        new_pw   = st.text_input("비밀번호", type="password", key="reg_pw")
        new_nick = st.text_input("닉네임", key="reg_nick")

        if st.button("가입하기"):
            if not (new_user and new_pw and new_nick):
                st.error("모든 항목을 입력해주세요.")
            elif create_user(new_user, new_pw, new_nick):
                # 성공 시 로그인 화면으로, 성공 메시지 표시
                st.session_state.signup_success = True
                st.session_state.page = "login"
                st.rerun()
            else:
                st.error("이미 존재하는 아이디입니다.")

# ── 챗봇 화면 ─────────────────────────────────────────────────
def chat_page():
    # st.title(f"🗨 상담 챗봇 (안녕하세요, {st.session_state.nickname}님!)")
    # if st.button("🔙 로그아웃"):
    #     for k in ("logged_in","username","nickname"):
    #         st.session_state[k] = False if k=="logged_in" else ""
    #     st.session_state.page = "login"
    #     st.rerun()

    # msg = st.text_input("메시지를 입력하세요:", key="chat_msg")
    # if st.button("전송", key="chat_send") and msg:
    #     with st.spinner("응답 생성 중..."):
    #         resp = get_bot_response(msg)
    #     st.text_area("챗봇 응답:", value=resp, height=200)
    st.title("내 Streamlit 앱에 Dify.ai 챗봇 임베드하기")

    # iframe 코드 전체를 문자열로 넣고, 높이(height)만 지정해 줍니다.
    iframe_code = """
    <iframe
        src="https://udify.app/chatbot/HuH7Wl5AO5GuwQlY"
        style="width: 100%; height: 100%; min-height: 700px;"
        frameborder="0"
        allow="microphone">
    </iframe>
    """

    # components.html로 렌더링
    components.html(iframe_code, height=700)

# ── 화면 전환 ──────────────────────────────────────────────────
if not st.session_state.logged_in:
    if st.session_state.page == "login":
        login_page()
    else:
        register_page()
else:
    chat_page()
