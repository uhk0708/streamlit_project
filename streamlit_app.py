# streamlit_app.py

import streamlit as st
import sqlite3, hashlib
import streamlit.components.v1 as components
import pandas as pd
from datetime import date

DB_PATH = "users.db"
SALES_DB_PATH = "sales.db"

# ── 사용자 DB 초기화 ─────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username      TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            nickname TEXT
        )
    """)
    conn.commit()
    conn.close()

# ── 매출 DB 초기화 ─────────────────────────────────────────────
def init_sales_db():
    conn = sqlite3.connect(SALES_DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            날짜 TEXT,
            사이트 TEXT,
            상품 TEXT,
            수량 INTEGER,
            광고비 INTEGER
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS fees (
            사이트 TEXT PRIMARY KEY,
            수수료율 REAL
        )
    """)
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

# ── 앱 초기화 & 세션 초기값 ──────────────────────────────────────
init_db()
init_sales_db()

for key, val in {
    "page": "login",
    "logged_in": False,
    "signup_success": False,
    "username": "",
    "nickname": ""
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

if "product_prices" not in st.session_state:
    st.session_state.product_prices = {}

# ── 로그인 페이지 ───────────────────────────────────────────────
def login_page():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.title("🗝 로그인")
        if st.session_state.signup_success:
            st.success("회원가입이 완료되었습니다. 로그인해주세요.")
            st.session_state.signup_success = False

        user = st.text_input("아이디", key="login_user")
        pw   = st.text_input("비밀번호", type="password", key="login_pw")

        if st.button("로그인"):
            if get_pw_hash(user) == hash_pw(pw):
                st.session_state.logged_in = True
                st.session_state.username  = user
                st.session_state.nickname  = get_nickname(user) or user
                st.session_state.page = "main"
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호가 잘못되었습니다.")

        if st.button("회원가입"):
            st.session_state.page = "register"
            st.rerun()

# ── 회원가입 페이지 ────────────────────────────────────────────
def register_page():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.title("📝 회원가입")
        if st.button("← 로그인으로 돌아가기"):
            st.session_state.page = "login"
            st.rerun()

        new_user = st.text_input("사용하실 아이디", key="reg_user")
        new_pw   = st.text_input("비밀번호", type="password", key="reg_pw")
        new_nick = st.text_input("닉네임", key="reg_nick")

        if st.button("가입하기"):
            if not (new_user and new_pw and new_nick):
                st.error("모든 항목을 입력해주세요.")
            elif create_user(new_user, new_pw, new_nick):
                st.session_state.signup_success = True
                st.session_state.page = "login"
                st.rerun()
            else:
                st.error("이미 존재하는 아이디입니다.")

# ── 관리자 페이지 ───────────────────────────────────────────────
def admin_page():
    st.title("🔧 관리자 페이지")

    tab1, tab2 = st.tabs(["상품 가격 설정", "사이트 수수료 설정"])

    with tab1:
        st.subheader("상품 가격 설정")
        site = st.text_input("사이트명")
        product = st.text_input("상품명")
        price = st.number_input("상품 가격", min_value=0, step=10)
        if st.button("상품 가격 저장"):
            if site and product:
                if site not in st.session_state.product_prices:
                    st.session_state.product_prices[site] = {}
                st.session_state.product_prices[site][product] = price
                st.success("상품 가격이 저장되었습니다.")

    with tab2:
        st.subheader("사이트별 수수료율 설정")
        fee_site = st.text_input("수수료 설정할 사이트")
        fee_value = st.number_input("수수료율 (%)", min_value=0.0, step=0.1, format="%.1f")
        if st.button("수수료율 저장"):
            conn = sqlite3.connect(SALES_DB_PATH)
            conn.execute("REPLACE INTO fees (사이트, 수수료율) VALUES (?, ?)", (fee_site, fee_value))
            conn.commit(); conn.close()
            st.success("수수료율이 저장되었습니다.")

# ── 매출 입력 및 분석 페이지 ─────────────────────────────────────
def main_page():
    st.title(f"📈 매출 자동화 시스템 - {st.session_state.nickname}님")

    today = date.today().isoformat()

    if st.session_state.product_prices:
        st.subheader("판매 내역 입력")
        selected_site = st.selectbox("사이트 선택", list(st.session_state.product_prices.keys()))
        selected_product = st.selectbox("상품 선택", list(st.session_state.product_prices[selected_site].keys()))
        quantity = st.number_input("판매 수량", min_value=0, step=1)
        ad_cost = st.number_input("해당 날짜의 광고비", min_value=0, step=100)

        if st.button("판매 데이터 저장"):
            conn = sqlite3.connect(SALES_DB_PATH)
            conn.execute("INSERT INTO sales (날짜, 사이트, 상품, 수량, 광고비) VALUES (?, ?, ?, ?, ?)",
                         (today, selected_site, selected_product, quantity, ad_cost))
            conn.commit(); conn.close()
            st.success("판매 데이터가 저장되었습니다.")

    st.subheader("매출 및 순이익 분석")
    conn = sqlite3.connect(SALES_DB_PATH)
    df = pd.read_sql_query("SELECT * FROM sales", conn)
    fee_df = pd.read_sql_query("SELECT * FROM fees", conn)
    conn.close()

    if not df.empty:
        df["단가"] = df.apply(lambda row: st.session_state.product_prices.get(row["사이트"], {}).get(row["상품"], 0), axis=1)
        df = pd.merge(df, fee_df, on="사이트", how="left")
        df["수수료율"] = df["수수료율"].fillna(0)
        df["매출"] = df["단가"] * df["수량"]
        df["수수료"] = df["매출"] * df["수수료율"] / 100
        df["순이익"] = df["매출"] - df["수수료"] - df["광고비"]

        daily_summary = df.groupby("날짜").agg({
            "매출": "sum",
            "광고비": "sum",
            "순이익": "sum"
        }).reset_index()

        st.dataframe(daily_summary)
        st.line_chart(daily_summary.set_index("날짜")[["매출", "광고비", "순이익"]])
    else:
        st.info("아직 판매 데이터가 없습니다.")

# ── 화면 전환 ──────────────────────────────────────────────────
if not st.session_state.logged_in:
    if st.session_state.page == "login":
        login_page()
    else:
        register_page()
else:
    menu = st.sidebar.selectbox("메뉴 선택", ["매출 페이지", "관리자 설정"])
    if menu == "관리자 설정":
        admin_page()
    else:
        main_page()
