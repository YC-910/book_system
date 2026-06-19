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
# MAIN TITLE
# =====================
st.markdown('<div class="title">📚 藏书记录</div>', unsafe_allow_html=True)

st.metric("📚 图书总数", total_books)

main_tab, search_tab, add_tab = st.tabs([
    "📚 图书馆",
    "🔍 搜索书本",
    "➕ 添加书本"
])

# =====================
# CATEGORY TABS
# =====================
with main_tab:

    category_tabs = st.tabs(categories)

    for i, cat in enumerate(categories):

        with category_tabs[i]:

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

with search_tab:

    search = st.text_input("🔍 输入书名搜索")

    if search:

        results = []

        for cat in categories:
            books = df[cat].dropna().tolist()

            for book in books:
                if search.lower() in str(book).lower():
                    results.append((book, cat))

        st.subheader(f"找到 {len(results)} 本书")

        if not results:
            st.warning("没有找到相关书籍")
        else:
            for book, cat in results:
                st.markdown(
                    f"""
                    <div class="book-card">
                        📖 {book}<br>
                        <small>{cat}</small>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

with add_tab:

    st.subheader("➕ 添加书本")

    new_book = st.text_input("书名")

    category = st.selectbox(
        "种类",
        categories,
        key="add_category"
    )

    if st.button("确定添加"):

        if new_book.strip():

            headers = sheet.row_values(1)

            col_index = headers.index(category) + 1

            next_row = len(sheet.col_values(col_index)) + 1

            sheet.update_cell(
                next_row,
                col_index,
                new_book
            )

            st.success("添加成功！")

            st.cache_data.clear()

            st.rerun()


