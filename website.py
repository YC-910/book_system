import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# =====================
# PAGE CONFIG
# =====================
st.set_page_config(page_title="📚 藏书记录", layout="wide", initial_sidebar_state="expanded")

# =====================
# GOOGLE AUTH
# =====================
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

service_account_info = dict(st.secrets["gcp_service_account"])
service_account_info["private_key"] = service_account_info["private_key"].replace(
    "\\n", "\n"
)

creds = Credentials.from_service_account_info(service_account_info, scopes=scope)

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
# BOOK COUNT
# =====================
def count_books(col):
    return df[col].dropna().shape[0]

total_books = sum(count_books(c) for c in categories)

# =====================
# STYLES
# =====================
st.markdown(
    """
<style>

/* ===== BACKGROUND ===== */
.stApp{
    background: url("https://raw.githubusercontent.com/YC-910/book_system/refs/heads/Python/aquarius.png");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    background-attachment: fixed;
}

/* ===== LAYOUT ===== */
.main .block-container{
    padding: 1rem 2.5rem;
}

/* ===== TITLE ===== */
.title{
    text-align:center;
    font-size:56px;
    font-weight:900;
    margin-bottom:20px;
    color:#ffffff;
}

/* ===== GRID ===== */
.book-grid{
    display:grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 26px;
    margin-top: 14px;
}

/* ===== BOOK CARD ===== */
.book-card{
    background: rgba(255, 255, 255, 0.88);
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

    box-shadow:0px 10px 30px rgba(0,0,0,0.15);
    border: 1px solid rgba(255,255,255,0.6);
    transition:0.3s ease;
}

.book-card:hover{
    transform: translateY(-6px);
    box-shadow: 0 15px 35px rgba(120,180,255,0.25);
    border: 1px solid rgba(120,180,255,0.5);
}

/* ===== RESPONSIVE ===== */
@media (max-width: 1200px){
    .book-grid{ grid-template-columns: repeat(4, 1fr); }
}

@media (max-width: 800px){
    .book-grid{ grid-template-columns: repeat(2, 1fr); }
}

</style>
""",
    unsafe_allow_html=True,
)

# =====================
# SIDEBAR UI
# =====================
st.sidebar.title("📚 侧边栏")

search = st.sidebar.text_input("🔍 寻找书本")

# =====================
# SEARCH FUNCTION
# =====================
def search_books(query):
    results = []
    for cat in categories:
        books = df[cat].dropna().tolist()
        for book in books:
            if query.lower() in str(book).lower():
                results.append((book, cat))
    return results

if search:
    st.sidebar.markdown("### 🔎 搜索结果")

    results = search_books(search)

    if not results:
        st.sidebar.info("No matching books")
    else:
        for book, cat in results:
            st.sidebar.markdown(
                f"""
            <div style="
                display:flex;
                justify-content:space-between;
                padding:6px 10px;
                margin:4px 0;
                border-radius:8px;
                background:#1f2937;
                color:white;
                font-size:13px;
            ">
                <div>📖 {book}</div>
                <div style="color:#9ca3af;">{cat}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

st.sidebar.markdown("---")
st.sidebar.metric("📚 总数", total_books)
st.sidebar.markdown("---")

# =====================
# ADD BOOK
# =====================
st.sidebar.subheader("➕ 添加书本")

new_book = st.sidebar.text_input("书名")
category = st.sidebar.selectbox("种类", categories)

if st.sidebar.button("确定添加") and new_book.strip():

    headers = sheet.row_values(1)
    col_index = headers.index(category) + 1
    next_row = len(sheet.col_values(col_index)) + 1

    sheet.update_cell(next_row, col_index, new_book)

    st.cache_data.clear()
    st.rerun()

# =====================
# MAIN TITLE
# =====================
st.markdown('<div class="title">📚 藏书记录</div>', unsafe_allow_html=True)

# =====================
# CATEGORY TABS
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

        html = '<div class="book-grid">'

        for book in books:
            html += f'<div class="book-card">📖 {book}</div>'

        html += "</div>"

        st.markdown(html, unsafe_allow_html=True)
