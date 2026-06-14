import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# =====================
# PAGE CONFIG
# =====================
st.set_page_config(
    page_title="📚 图书系统",
    layout="wide"
)

# =====================
# GOOGLE AUTH
# =====================
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

service_account_info = dict(st.secrets["gcp_service_account"])
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
# UI STYLE (READING APP PRO MODE)
# =====================
st.markdown("""
<style>

/* ===== REMOVE STREAMLIT UI ===== */
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}

div[data-testid="stToolbar"] {display: none !important;}
div[data-testid="stDecoration"] {display: none !important;}

/* ===== PAGE LAYOUT ===== */
.main .block-container{
    padding: 1rem 2.5rem;
    background: #f6f7fb;
}

/* ===== TITLE ===== */
.title{
    text-align:center;
    font-size:56px;
    font-weight:900;
    margin-bottom:20px;
    color:#FFFFFF;
    letter-spacing:1px;
}

/* ===== GRID ===== */
.book-grid{
    display:grid;
    grid-template-columns: repeat(6, 1fr);
    column-gap: 26px;
    row-gap: 28px;
    margin-top: 14px;
}

/* ===== BOOK CARD (READING APP STYLE) ===== */
.book-card{
    background: linear-gradient(145deg, #ffffff, #f3f4f6);
    border-radius:18px;
    padding:20px;
    height:150px;

    display:flex;
    align-items:center;
    justify-content:center;

    text-align:center;

    font-size:20px;
    font-weight:800;
    color:#111827;

    box-shadow:0px 8px 22px rgba(0,0,0,0.10);
    border: 1px solid #e5e7eb;

    transition: all 0.25s ease;
}

.book-card:hover{
    transform: translateY(-6px) scale(1.02);
    box-shadow:0px 14px 28px rgba(0,0,0,0.18);
}

/* ===== RESPONSIVE ===== */
@media (max-width: 1200px){
    .book-grid{
        grid-template-columns: repeat(4, 1fr);
    }
}

@media (max-width: 800px){
    .book-grid{
        grid-template-columns: repeat(2, 1fr);
    }
}

/* ===== SIDEBAR ===== */
section[data-testid="stSidebar"]{
    background: #0f172a;
    color: white;
}

</style>
""", unsafe_allow_html=True)

# =====================
# SIDEBAR
# =====================
st.sidebar.title("📚 侧边栏")

search = st.sidebar.text_input("🔍 寻找书本")

st.sidebar.metric("📚 总图书", total_books)

st.sidebar.markdown("---")

st.sidebar.subheader("➕ 添加书本")

new_book = st.sidebar.text_input("书名")
category = st.sidebar.selectbox("种类", categories)

if st.sidebar.button("确定添加"):
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
st.markdown('<div class="title">📚 图书系统</div>', unsafe_allow_html=True)

# =====================
# TABS
# =====================
tabs = st.tabs(categories)

for i, cat in enumerate(categories):

    with tabs[i]:

        books = df[cat].dropna().tolist()

        # SEARCH FILTER
        if search:
            books = [b for b in books if search.lower() in str(b).lower()]

        st.subheader(f"📂 {cat}")
        st.markdown(f"### 📚 共: {len(books)} 本")

        if not books:
            st.info("No books found")
            continue

        # =====================
        # GRID RENDER
        # =====================
        html = '<div class="book-grid">'

        for book in books:
            html += f'<div class="book-card">📖 {book}</div>'

        html += "</div>"

        st.markdown(html, unsafe_allow_html=True)
