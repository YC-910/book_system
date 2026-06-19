import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# =====================
# PAGE CONFIG
# =====================
st.set_page_config(
    page_title="📚 藏书记录",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =====================
# HIDE UI + BACKGROUND
# =====================
st.markdown("""
<style>
#MainMenu, header, footer {visibility: hidden;}

div[data-testid="stToolbar"],
div[data-testid="stStatusWidget"] {
    display: none;
}

/* Background */
.stApp{
    background: url("https://raw.githubusercontent.com/YC-910/book_system/refs/heads/Python/aquarius.png");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}

/* Layout */
.main .block-container{
    padding: 1rem 2.5rem;
}

/* Title */
.title{
    text-align:center;
    font-size:56px;
    font-weight:900;
    color:white;
    margin-bottom:20px;
}

/* Grid */
.book-grid{
    display:grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 26px;
    margin-top: 14px;
}

/* Card */
.book-card{
    background: rgba(255,255,255,0.88);
    backdrop-filter: blur(10px);
    border-radius:18px;
    padding:20px;
    height:150px;

    display:flex;
    align-items:center;
    justify-content:center;

    font-size:18px;
    font-weight:800;
    color:#111827;

    box-shadow:0 10px 30px rgba(0,0,0,0.15);
    border:1px solid rgba(255,255,255,0.6);
}

.book-card:hover{
    transform: translateY(-6px);
    transition:0.3s;
}

/* Responsive */
@media (max-width: 1200px){
    .book-grid{ grid-template-columns: repeat(4, 1fr); }
}
@media (max-width: 800px){
    .book-grid{ grid-template-columns: repeat(2, 1fr); }
}
</style>
""", unsafe_allow_html=True)

# =====================
# GOOGLE SHEET AUTH
# =====================
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

creds_dict = dict(st.secrets["gcp_service_account"])
creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

sheet = client.open_by_key(
    "1c8t964bqcoMl1BlSTrijp2QLBXXAH-58AlEZbCBtT0Q"
).worksheet("纸质书")

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
# HELPERS
# =====================
def search_books(keyword):
    results = []
    for cat in categories:
        for book in df[cat].dropna():
            if keyword.lower() in str(book).lower():
                results.append((book, cat))
    return results

def add_book(book, category):
    headers = sheet.row_values(1)
    col = headers.index(category) + 1
    row = len(sheet.col_values(col)) + 1
    sheet.update_cell(row, col, book)

# =====================
# HEADER
# =====================
st.markdown('<div class="title">📚 藏书记录</div>', unsafe_allow_html=True)
st.metric("📚 图书总数", sum(df[c].dropna().shape[0] for c in categories))

# =====================
# TABS
# =====================
library_tab, search_tab, add_tab = st.tabs(
    ["📚 图书馆", "🔍 搜索", "➕ 添加"]
)

# =====================
# LIBRARY
# =====================
with library_tab:
    category_tabs = st.tabs(categories)

    for i, cat in enumerate(categories):
        with category_tabs[i]:
            books = df[cat].dropna().tolist()

            st.subheader(cat)
            st.write(f"📚 共: {len(books)} 本")

            if not books:
                st.info("No books found")
                continue

            html = '<div class="book-grid">'
            for book in books:
                html += f'<div class="book-card">📖 {book}</div>'
            html += "</div>"

            st.markdown(html, unsafe_allow_html=True)

# =====================
# SEARCH
# =====================
with search_tab:
    keyword = st.text_input("输入书名")

    if keyword:
        results = search_books(keyword)

        st.write(f"找到 {len(results)} 本书")

        if not results:
            st.warning("没有找到")

        for book, cat in results:
            st.write(f"📖 {book} ({cat})")

# =====================
# ADD
# =====================
with add_tab:
    book = st.text_input("书名")
    category = st.selectbox("种类", categories)

    if st.button("添加"):
        if book.strip():
            add_book(book, category)
            st.success(f"已添加：{book}")
            st.cache_data.clear()
            st.rerun()
        else:
            st.warning("请输入书名")
