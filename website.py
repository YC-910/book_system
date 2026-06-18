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

/* ===== PAGE ===== */
.stApp{
    background: linear-gradient(135deg,#0f172a,#1e293b,#334155);
}

.main .block-container{
    padding:1rem 2.5rem;
}

/* ===== TITLE ===== */
.title{
    text-align:center;
    font-size:64px;
    font-weight:900;
    margin-bottom:20px;

    background: linear-gradient(
        90deg,
        #60a5fa,
        #a78bfa,
        #f472b6
    );

    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;

    animation: glow 3s infinite alternate;
}

@keyframes glow{
    from{
        filter:drop-shadow(0 0 5px rgba(255,255,255,.2));
    }
    to{
        filter:drop-shadow(0 0 15px rgba(255,255,255,.5));
    }
}

/* ===== TABS ===== */
.stTabs [data-baseweb="tab-list"]{
    gap:10px;
}

.stTabs [data-baseweb="tab"]{
    background:rgba(255,255,255,.08);
    border-radius:12px;
    padding:10px 18px;
    color:white;
    transition:.3s;
}

.stTabs [aria-selected="true"]{
    background:#60a5fa !important;
    color:white !important;
}

/* ===== GRID ===== */
.book-grid{
    display:grid;
    grid-template-columns:repeat(6,1fr);
    gap:24px;
    margin-top:20px;
}

/* ===== BOOK CARD ===== */
.book-card{
    background:rgba(255,255,255,0.12);
    backdrop-filter:blur(15px);

    border-radius:22px;
    padding:20px;
    height:170px;

    display:flex;
    align-items:center;
    justify-content:center;

    text-align:center;

    font-size:18px;
    font-weight:700;

    color:white;

    border:1px solid rgba(255,255,255,.15);

    transition:.3s;
}

.book-card:hover{
    transform:translateY(-8px) scale(1.03);

    background:rgba(96,165,250,.35);

    box-shadow:
    0 10px 25px rgba(0,0,0,.35),
    0 0 25px rgba(96,165,250,.4);
}

/* ===== SIDEBAR ===== */
section[data-testid="stSidebar"]{
    background:linear-gradient(
        180deg,
        #020617,
        #0f172a,
        #1e293b
    );
}

/* Sidebar title */
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3{
    color:white;
}

/* ===== SEARCH RESULT CARD ===== */
.search-card{
    display:flex;
    justify-content:space-between;

    padding:8px 12px;
    margin-bottom:8px;

    border-radius:12px;

    background:rgba(255,255,255,.08);

    color:white;

    transition:.25s;
}

.search-card:hover{
    background:#2563eb;
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
