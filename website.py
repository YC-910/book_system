import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# =====================
# PAGE CONFIG
# =====================
st.set_page_config(
    page_title="📚 Library System",
    layout="wide"
)

# =====================
# GOOGLE AUTH (STREAMLIT SECRETS)
# =====================
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

service_account_info = dict(st.secrets["gcp_service_account"])

# FIX KEY FORMAT (IMPORTANT)
service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")

creds = Credentials.from_service_account_info(
    service_account_info,
    scopes=scope
)

client = gspread.authorize(creds)

# =====================
# SHEET
# =====================
SHEET_ID = "1c8t964bqcoMl1BlSTrijp2QLBXXAH-58AlEZbCBtT0Q"
sheet = client.open_by_key(SHEET_ID).worksheet("纸质书")

# =====================
# LOAD DATA
# =====================
@st.cache_data(ttl=60)
def load_data():
    data = sheet.get_all_values()

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)
    df.columns = df.iloc[0]
    df = df[1:]

    df = df.replace(r"^\s*$", pd.NA, regex=True)
    return df

df = load_data()
categories = df.columns.tolist()

# =====================
# COUNT
# =====================
def count_books(col):
    return df[col].dropna().shape[0]

total_books = sum(count_books(c) for c in categories)

# =====================
# UI STYLE
# =====================
st.markdown("""
<style>

.main .block-container{
    padding: 1rem 2rem;
}

.title{
    text-align:center;
    font-size:54px;
    font-weight:900;
}

.book-card{
    background:white;
    border-radius:16px;
    padding:18px;
    min-height:130px;

    display:flex;
    align-items:center;
    justify-content:center;

    font-size:20px;
    font-weight:800;
    color:black;

    box-shadow:0px 6px 18px rgba(0,0,0,0.12);
    transition:0.2s;
}

.book-card:hover{
    transform:translateY(-5px);
}

section[data-testid="stSidebar"]{
    background:#0f172a;
}

.book-row-gap {
    height: 22px;
}

</style>
""", unsafe_allow_html=True)

# =====================
# SIDEBAR
# =====================
st.sidebar.title("📚 侧边栏")

search = st.sidebar.text_input("🔍 书本查询")

st.sidebar.metric("📚 总数：", total_books)

st.sidebar.markdown("---")

st.sidebar.subheader("➕ 添加书本")

new_book = st.sidebar.text_input("书本名字")
category = st.sidebar.selectbox("Category", categories)

if st.sidebar.button("Add"):
    if new_book.strip():

        headers = sheet.row_values(1)
        col_index = headers.index(category) + 1

        next_row = len(sheet.col_values(col_index)) + 1
        sheet.update_cell(next_row, col_index, new_book)

        st.cache_data.clear()
        st.rerun()

# =====================
# TITLE
# =====================
st.markdown('<div class="title">📚 Library System</div>', unsafe_allow_html=True)

# =====================
# TABS
# =====================
tabs = st.tabs(categories)

for i, cat in enumerate(categories):

    with tabs[i]:

        books = df[cat].dropna().tolist()

        if search:
            books = [b for b in books if search.lower() in str(b).lower()]

        st.subheader(f"📂 {cat}")
        st.markdown(f"### 📚 共: {len(books)} 本")

        if not books:
            st.info("No books found")
            continue

        # =========================
        # GRID STYLE (IMPORTANT FIX)
        # =========================
        st.markdown("""
        <style>
        .book-grid {
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 18px;   /* 🔥 THIS IS THE REAL GAP */
            margin-top: 10px;
        }

        @media (max-width: 1200px) {
            .book-grid {
                grid-template-columns: repeat(4, 1fr);
            }
        }

        @media (max-width: 800px) {
            .book-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        </style>
        """, unsafe_allow_html=True)

        # =========================
        # RENDER GRID
        # =========================
        grid_html = '<div class="book-grid">'

        for book in books:
            grid_html += f"""
            <div class="book-card">
                📖 {book}
            </div>
            """

        grid_html += "</div>"

        st.markdown(grid_html, unsafe_allow_html=True)
