import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="📚 书橱记录系统",
    layout="wide"
)

# =========================
# GOOGLE SHEETS AUTH
# =========================
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]



creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(creds)

SHEET_ID = "1c8t964bqcoMl1BlSTrijp2QLBXXAH-58AlEZbCBtT0Q"

spreadsheet = client.open_by_key(SHEET_ID)
sheet = spreadsheet.worksheet("纸质书")

# =========================
# LOAD DATA
# =========================
def load_data():
    data = sheet.get_all_values()

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)
    df.columns = df.iloc[0]
    df = df[1:]

    return df

df = load_data()

# =========================
# CLEAN COUNT
# =========================
def count_books(col):
    return df[col].replace(["", " "], pd.NA).dropna().shape[0]

category_counts = {col: count_books(col) for col in df.columns}

# =========================
# STYLE
# =========================
st.markdown("""
<style>

.main .block-container {
    padding-top: 1rem;
    padding-left: 2rem;
    padding-right: 2rem;
}

.title {
    font-size: 42px;
    font-weight: bold;
    margin-bottom: 10px;
}

.book-card {
    background: white;
    padding: 18px;
    border-radius: 14px;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.15);
    text-align: center;
    font-weight: 600;
    transition: 0.2s;
    height: 120px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #000000;
    font-size: 16px;
}

.book-card:hover {
    transform: scale(1.03);
    background: #f8f9fa;
}

section[data-testid="stSidebar"] {
    background-color: #0f172a;
    color: white;
}

</style>
""", unsafe_allow_html=True)

# =========================
# SIDEBAR (SEARCH + ADD BOOK)
# =========================
st.sidebar.title("📚 Library Menu")

search = st.sidebar.text_input("🔍 Search book")

st.sidebar.markdown("---")
st.sidebar.subheader("➕ 添加新书")

new_book = st.sidebar.text_input("书名")

category = st.sidebar.selectbox("分类", df.columns.tolist())

if st.sidebar.button("添加书籍"):

    headers = sheet.row_values(1)

    if category in headers:
        col_index = headers.index(category) + 1

        col_values = sheet.col_values(col_index)
        next_row = len(col_values) + 1

        sheet.update_cell(next_row, col_index, new_book)

        st.sidebar.success("添加成功！")
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.write("📊 Total Books:", sum(category_counts.values()))

# =========================
# TITLE
# =========================
st.markdown('<div class="title">📚 书橱记录系统</div>', unsafe_allow_html=True)

# =========================
# TABS
# =========================
categories = df.columns.tolist()
tabs = st.tabs(categories)

for i, cat in enumerate(categories):

    with tabs[i]:

        books = df[cat].replace(["", " "], pd.NA).dropna().tolist()

        # =========================
        # SEARCH FILTER (FIXED)
        # =========================
        if search:
            books = [b for b in books if search.lower() in str(b).lower()]

        total = len(books)

        st.subheader(f"📂 {cat}")
        st.markdown(f"📚 **Total: {total} books**")

        cols = st.columns(5)

        for idx, book in enumerate(books):

            with cols[idx % 5]:
                st.markdown(f"""
                <div class="book-card">
                    📖 {book}
                </div>
                """, unsafe_allow_html=True)
