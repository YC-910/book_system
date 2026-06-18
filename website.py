import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# =====================
# PAGE CONFIG
# =====================
st.set_page_config(
    page_title="📚 图书系统",
    layout="wide",
    initial_sidebar_state="expanded"   # ✅ keep sidebar stable
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
# UI STYLE (SAFE + CLEAN)
# =====================
st.markdown("""
<style>

/* ===== LIBRARY BACKGROUND ===== */
.stApp{
    background: linear-gradient(
        135deg,
        #f8f5f0,
        #efe8dc,
        #e8dcc6
    );
}

/* ===== PAGE ===== */
.main .block-container{
    padding:1rem 2.5rem;
}

/* ===== TITLE ===== */
.title{
    text-align:center;
    font-size:60px;
    font-weight:900;

    color:#5c4033;

    margin-bottom:20px;

    font-family: Georgia, serif;
}

/* ===== TABS ===== */
.stTabs [data-baseweb="tab"]{
    background:#f3ece1;
    border-radius:10px;

    color:#5c4033;

    transition:.3s;
}

.stTabs [aria-selected="true"]{
    background:#8b6f47 !important;
    color:white !important;
}

/* ===== BOOK GRID ===== */
.book-grid{
    display:grid;
    grid-template-columns:repeat(6,1fr);
    gap:24px;
    margin-top:20px;
}

/* ===== BOOK CARD ===== */
.book-card{

    background:white;

    border-left:8px solid #8b6f47;

    border-radius:12px;

    height:170px;

    display:flex;
    align-items:center;
    justify-content:center;

    text-align:center;

    padding:15px;

    color:#3d2b1f;

    font-size:18px;
    font-weight:700;

    box-shadow:
    0 4px 12px rgba(0,0,0,.08);

    transition:.25s;
}

.book-card:hover{

    transform:translateY(-5px);

    box-shadow:
    0 10px 25px rgba(0,0,0,.15);

    background:#fffdf8;
}

/* ===== SIDEBAR ===== */
section[data-testid="stSidebar"]{
    background:
    linear-gradient(
        180deg,
        #5c4033,
        #6f4e37,
        #8b6f47
    );
}

/* Sidebar Text */
section[data-testid="stSidebar"] *{
    color:white;
}

/* ===== SEARCH RESULT ===== */
.search-card{

    display:flex;
    justify-content:space-between;

    padding:10px;

    margin-bottom:8px;

    border-radius:10px;

    background:#f5eee3;

    color:#3d2b1f;

    border-left:5px solid #8b6f47;

    transition:.25s;
}

.search-card:hover{
    background:#ebe1d1;
    transform:translateX(4px);
}

/* ===== RESPONSIVE ===== */
@media (max-width:1200px){
    .book-grid{
        grid-template-columns:repeat(4,1fr);
    }
}

@media (max-width:800px){
    .book-grid{
        grid-template-columns:repeat(2,1fr);
    }
}

</style><style>

/* ===== LIBRARY BACKGROUND ===== */
.stApp{
    background: linear-gradient(
        135deg,
        #f8f5f0,
        #efe8dc,
        #e8dcc6
    );
}

/* ===== PAGE ===== */
.main .block-container{
    padding:1rem 2.5rem;
}

/* ===== TITLE ===== */
.title{
    text-align:center;
    font-size:60px;
    font-weight:900;

    color:#5c4033;

    margin-bottom:20px;

    font-family: Georgia, serif;
}

/* ===== TABS ===== */
.stTabs [data-baseweb="tab"]{
    background:#f3ece1;
    border-radius:10px;

    color:#5c4033;

    transition:.3s;
}

.stTabs [aria-selected="true"]{
    background:#8b6f47 !important;
    color:white !important;
}

/* ===== BOOK GRID ===== */
.book-grid{
    display:grid;
    grid-template-columns:repeat(6,1fr);
    gap:24px;
    margin-top:20px;
}

/* ===== BOOK CARD ===== */
.book-card{

    background:white;

    border-left:8px solid #8b6f47;

    border-radius:12px;

    height:170px;

    display:flex;
    align-items:center;
    justify-content:center;

    text-align:center;

    padding:15px;

    color:#3d2b1f;

    font-size:18px;
    font-weight:700;

    box-shadow:
    0 4px 12px rgba(0,0,0,.08);

    transition:.25s;
}

.book-card:hover{

    transform:translateY(-5px);

    box-shadow:
    0 10px 25px rgba(0,0,0,.15);

    background:#fffdf8;
}

/* ===== SIDEBAR ===== */
section[data-testid="stSidebar"]{
    background:
    linear-gradient(
        180deg,
        #5c4033,
        #6f4e37,
        #8b6f47
    );
}

/* Sidebar Text */
section[data-testid="stSidebar"] *{
    color:white;
}

/* ===== SEARCH RESULT ===== */
.search-card{

    display:flex;
    justify-content:space-between;

    padding:10px;

    margin-bottom:8px;

    border-radius:10px;

    background:#f5eee3;

    color:#3d2b1f;

    border-left:5px solid #8b6f47;

    transition:.25s;
}

.search-card:hover{
    background:#ebe1d1;
    transform:translateX(4px);
}

/* ===== RESPONSIVE ===== */
@media (max-width:1200px){
    .book-grid{
        grid-template-columns:repeat(4,1fr);
    }
}

@media (max-width:800px){
    .book-grid{
        grid-template-columns:repeat(2,1fr);
    }
}

</style>
""", unsafe_allow_html=True)

# =====================
# SIDEBAR
# =====================
st.sidebar.title("📚 侧边栏")

search = st.sidebar.text_input("🔍 寻找书本")

# =====================
# SEARCH RESULT (ABOVE TOTAL)
# =====================
if search:
    st.sidebar.markdown("### 🔎 搜索结果")

    results = []

    for cat in categories:
        books = df[cat].dropna().tolist()

        for book in books:
            if search.lower() in str(book).lower():
                results.append((book, cat))

    if not results:
        st.sidebar.info("No matching books")
    else:
        for book, cat in results:
            st.sidebar.markdown(f"""
            <div class="search-card">
                <div>📖 {book}</div>
                <div>{cat}</div>
            </div>
            """, unsafe_allow_html=True)
st.sidebar.markdown("---")

st.sidebar.metric("📚 总数", total_books)

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
col1,col2,col3 = st.columns(3)

with col1:
    st.metric("📚 图书总数", total_books)

with col2:
    st.metric("📂 分类数量", len(categories))

with col3:
    st.metric("🤖 系统状态", "ONLINE")

st.markdown(
    '<div class="title">📚 图书系统</div>',
    unsafe_allow_html=True
)

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

        html = '<div class="book-grid">'

        for book in books:
            html += f'<div class="book-card">📖 {book}</div>'

        html += "</div>"

        st.markdown(html, unsafe_allow_html=True)
