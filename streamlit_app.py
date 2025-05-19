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
    c.execute("""
        CREATE TABLE IF NOT EXISTS products (
            사이트 TEXT,
            상품 TEXT,
            가격 INTEGER,
            PRIMARY KEY (사이트, 상품)
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

    tab1, tab2, tab3 = st.tabs(["상품 가격 설정", "사이트 수수료 설정", "광고비 설정"])

    with tab1:
        st.subheader("상품 가격 설정")
        site = st.text_input("사이트명")
        product = st.text_input("상품명")
        price = st.number_input("상품 가격", min_value=0, step=10)
        if st.button("상품 가격 저장"):
            if site and product:
                conn = sqlite3.connect(SALES_DB_PATH)
                conn.execute("REPLACE INTO products (사이트, 상품, 가격) VALUES (?, ?, ?)", (site, product, price))
                conn.commit(); conn.close()
                st.success("상품 가격이 저장되었습니다.")

        st.divider()
        st.subheader("상품 목록 관리")
        conn = sqlite3.connect(SALES_DB_PATH)
        product_df = pd.read_sql_query("SELECT * FROM products", conn)
        conn.close()

        for idx, row in product_df.iterrows():
            with st.container():
                cols = st.columns([5, 3, 1, 1])
                with cols[0]:
                    st.markdown(f"**{row['사이트']} / {row['상품']}** - {row['가격']}원")
                with cols[1]:
                    new_price = st.number_input(
                        label=f"",
                        value=row['가격'],
                        key=f"edit_{row['사이트']}_{row['상품']}",
                        label_visibility="collapsed",
                        step=100
                    )
                with cols[2]:
                    if st.button("수정", key=f"update_{row['사이트']}_{row['상품']}"):
                        conn = sqlite3.connect(SALES_DB_PATH)
                        conn.execute("UPDATE products SET 가격=? WHERE 사이트=? AND 상품=?", (new_price, row['사이트'], row['상품']))
                        conn.commit(); conn.close()
                        st.success("수정 완료"); st.rerun()
                with cols[3]:
                    if st.button("삭제", key=f"delete_{row['사이트']}_{row['상품']}"):
                        conn = sqlite3.connect(SALES_DB_PATH)
                        conn.execute("DELETE FROM products WHERE 사이트=? AND 상품=?", (row['사이트'], row['상품']))
                        conn.commit(); conn.close()
                        st.success("삭제 완료"); st.rerun()

    with tab2:
        st.subheader("사이트별 수수료율 설정")
        fee_site = st.text_input("수수료 설정할 사이트")
        fee_value = st.number_input("수수료율 (%)", min_value=0.0, step=0.00001, format="%.5f")
        if st.button("수수료율 저장"):
            conn = sqlite3.connect(SALES_DB_PATH)
            conn.execute("REPLACE INTO fees (사이트, 수수료율) VALUES (?, ?)", (fee_site, fee_value))
            conn.commit(); conn.close()
            st.success("수수료율이 저장되었습니다.")

        st.divider()
        st.subheader("수수료 목록 및 관리")
        conn = sqlite3.connect(SALES_DB_PATH)
        fee_df = pd.read_sql_query("SELECT * FROM fees", conn)
        conn.close()
        for idx, row in fee_df.iterrows():
            col1, col2, col3 = st.columns([4, 2, 2])
            with col1:
                st.markdown(f"**{row['사이트']}** - {row['수수료율']}%")
            with col2:
                updated_fee = st.number_input(f"수정할 수수료율 ({row['사이트']})", value=row['수수료율'], key=f"fee_{row['사이트']}")
                if st.button("수정", key=f"fee_update_{row['사이트']}"):
                    conn = sqlite3.connect(SALES_DB_PATH)
                    conn.execute("UPDATE fees SET 수수료율 = ? WHERE 사이트 = ?", (updated_fee, row['사이트']))
                    conn.commit(); conn.close()
                    st.success("수정 완료"); st.rerun()
            with col3:
                if st.button("삭제", key=f"fee_delete_{row['사이트']}"):
                    conn = sqlite3.connect(SALES_DB_PATH)
                    conn.execute("DELETE FROM fees WHERE 사이트 = ?", (row['사이트'],))
                    conn.commit(); conn.close()
                    st.success("삭제 완료"); st.rerun()
    with tab3:
        st.subheader("📆 날짜별 사이트 광고비 관리")
        from datetime import datetime
        conn = sqlite3.connect(SALES_DB_PATH)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS adcost (
                날짜 TEXT,
                사이트 TEXT,
                광고비 INTEGER,
                PRIMARY KEY (날짜, 사이트)
            )
        """)
        conn.commit()
    
        ad_date = st.date_input("광고비 적용 날짜", value=date.today())
        ad_site = st.text_input("사이트명", key="ad_site")
        ad_value = st.number_input("광고비 (원)", min_value=0, step=100)
    
        if st.button("광고비 저장"):
            conn.execute(
                "REPLACE INTO adcost (날짜, 사이트, 광고비) VALUES (?, ?, ?)",
                (ad_date.isoformat(), ad_site, ad_value)
            )
            conn.commit()
            st.success("광고비 저장 완료")
    
        st.divider()
        ad_df = pd.read_sql_query("SELECT * FROM adcost ORDER BY 날짜 DESC, 사이트", conn)
        conn.close()
    
        for idx, row in ad_df.iterrows():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            with col1:
                st.markdown(f"📅 {row['날짜']} | 🛒 {row['사이트']} | 💰 {row['광고비']}원")
            with col2:
                updated_val = st.number_input(
                    "수정 광고비", value=row['광고비'], key=f"edit_ad_{idx}", step=100
                )
            with col3:
                if st.button("수정", key=f"update_ad_{idx}"):
                    conn = sqlite3.connect(SALES_DB_PATH)
                    conn.execute(
                        "UPDATE adcost SET 광고비 = ? WHERE 날짜 = ? AND 사이트 = ?",
                        (updated_val, row['날짜'], row['사이트'])
                    )
                    conn.commit(); conn.close()
                    st.success("수정 완료"); st.rerun()
            with col4:
                if st.button("삭제", key=f"delete_ad_{idx}"):
                    conn = sqlite3.connect(SALES_DB_PATH)
                    conn.execute(
                        "DELETE FROM adcost WHERE 날짜 = ? AND 사이트 = ?",
                        (row['날짜'], row['사이트'])
                    )
                    conn.commit(); conn.close()
                    st.success("삭제 완료"); st.rerun()
    


# ── 매출 입력 및 분석 페이지 ─────────────────────────────────────
def main_page():
    st.title(f"📈 매출 자동화 시스템 - {st.session_state.nickname}님")

    today = date.today().isoformat()

    conn = sqlite3.connect(SALES_DB_PATH)
    product_df = pd.read_sql_query("SELECT * FROM products", conn)
    conn.close()

    if not product_df.empty:
        st.subheader("판매 내역 입력")
        selected_site = st.selectbox("사이트 선택", product_df["사이트"].unique())
        filtered_products = product_df[product_df["사이트"] == selected_site]
        selected_product = st.selectbox("상품 선택", filtered_products["상품"].tolist())
        quantity = st.number_input("판매 수량", min_value=0, step=1)

        if st.button("판매 데이터 저장"):
            conn = sqlite3.connect(SALES_DB_PATH)
            conn.execute("INSERT INTO sales (날짜, 사이트, 상품, 수량, 광고비) VALUES (?, ?, ?, ?, 0)",
                         (today, selected_site, selected_product, quantity))
            conn.commit(); conn.close()
            st.success("판매 데이터가 저장되었습니다.")

    st.subheader("판매 데이터 목록 및 수정")
    conn = sqlite3.connect(SALES_DB_PATH)
    sales_df = pd.read_sql_query("SELECT rowid, * FROM sales ORDER BY 날짜 DESC", conn)
    conn.close()

    if not sales_df.empty:
        site_filter = st.selectbox("사이트 필터", ["전체"] + sorted(sales_df["사이트"].unique().tolist()))
        filtered_df = sales_df if site_filter == "전체" else sales_df[sales_df["사이트"] == site_filter]

        for idx, row in filtered_df.iterrows():
            with st.container():
                cols = st.columns([3, 3, 2, 2, 1])
                with cols[0]:
                    st.markdown(f"📅 **{row['날짜']}** | 🛒 **{row['사이트']} / {row['상품']}**")
                with cols[1]:
                    qty = st.number_input("수량", value=row['수량'], key=f"qty_{row['rowid']}", step=1)
                with cols[2]:
                    if st.button("수정", key=f"edit_{row['rowid']}"):
                        conn = sqlite3.connect(SALES_DB_PATH)
                        conn.execute("UPDATE sales SET 수량=? WHERE rowid=?", (qty, row['rowid']))
                        conn.commit(); conn.close()
                        st.success("수정 완료"); st.rerun()
                with cols[3]:
                    if st.button("삭제", key=f"del_{row['rowid']}"):
                        conn = sqlite3.connect(SALES_DB_PATH)
                        conn.execute("DELETE FROM sales WHERE rowid=?", (row['rowid'],))
                        conn.commit(); conn.close()
                        st.success("삭제 완료"); st.rerun()

    st.subheader("매출 및 순이익 분석")
    conn = sqlite3.connect(SALES_DB_PATH)
    df = pd.read_sql_query("SELECT * FROM sales", conn)
    fee_df = pd.read_sql_query("SELECT * FROM fees", conn)
    prod_df = pd.read_sql_query("SELECT * FROM products", conn)
    ad_df = pd.read_sql_query("SELECT * FROM adcost", conn)
    conn.close()

    if not df.empty:
        df = df.merge(prod_df, on=["사이트", "상품"], how="left")
        df = df.merge(fee_df, on="사이트", how="left")
        df = df.merge(ad_df, on=["날짜", "사이트"], how="left")

        df["수수료율"] = df["수수료율"].fillna(0)
        df["광고비"] = df["광고비"].fillna(0)
        df["매출"] = df["가격"] * df["수량"]
        df["수수료"] = df["매출"] * df["수수료율"] / 100

        # 광고비가 동일 날짜-사이트에 중복 계산되지 않도록 제거
        df_grouped = df.drop_duplicates(subset=["날짜", "사이트"])[["날짜", "사이트", "광고비"]]
        ad_summary = df_grouped.groupby("날짜")["광고비"].sum().reset_index()

        df["광고비"] = 0  # 다시 초기화 후 날짜별 광고비 수동 할당
        for idx, row in ad_summary.iterrows():
            df.loc[df["날짜"] == row["날짜"], "광고비"] = row["광고비"]

        df_grouped = df.groupby("날짜").agg({
            "매출": "sum",
            "광고비": "max",
            "수수료": "sum"
        }).reset_index()

        df_grouped["순이익"] = df_grouped["매출"] - df_grouped["수수료"] - df_grouped["광고비"]

        st.dataframe(df_grouped)
        st.line_chart(df_grouped.set_index("날짜")[['매출', '광고비', '순이익']])
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
