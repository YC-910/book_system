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
    background:
    radial-gradient(circle at top left,#00ffff22,transparent 25%),
    radial-gradient(circle at bottom right,#8b5cf622,transparent 25%),
    linear-gradient(135deg,#020617,#050816,#0f172a);

    color:white;
}

.main .block-container{
    padding:1rem 2.5rem;
}

/* ===== TITLE ===== */
.title{
    text-align:center;
    font-size:72px;
    font-weight:900;

    color:#00ffff;

    text-shadow:
    0 0 10px #00ffff,
    0 0 20px #00ffff,
    0 0 40px #00ffff;

    letter-spacing:4px;

    animation:pulseGlow 2s infinite alternate;
}

@keyframes pulseGlow{
    from{
        text-shadow:
        0 0 10px #00ffff,
        0 0 20px #00ffff;
    }
    to{
        text-shadow:
        0 0 20px #00ffff,
        0 0 40px #00ffff,
        0 0 80px #00ffff;
    }
}

/* ===== TABS ===== */
.stTabs [data-baseweb="tab-list"]{
    gap:10px;
}

.stTabs [data-baseweb="tab"]{
    background:#0f172a;
    border:1px solid #00ffff55;

    border-radius:12px;

    color:#00ffff;

    transition:.3s;
}

.stTabs [data-baseweb="tab"]:hover{
    box-shadow:
    0 0 15px #00ffff88;
}

.stTabs [aria-selected="true"]{
    background:#00ffff22 !important;

    color:#00ffff !important;

    box-shadow:
    0 0 20px #00ffff;
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
    background:
    linear-gradient(
        145deg,
        rgba(0,255,255,.08),
        rgba(255,255,255,.03)
    );

    border:1px solid #00ffff55;

    backdrop-filter:blur(12px);

    border-radius:20px;

    height:170px;

    color:#00ffff;

    font-size:18px;
    font-weight:700;

    display:flex;
    align-items:center;
    justify-content:center;

    text-align:center;

    transition:.35s;
}

.book-card:hover{

    transform:
    translateY(-10px)
    scale(1.05);

    box-shadow:
    0 0 15px #00ffff,
    0 0 30px #00ffff,
    0 0 60px #00ffff55;

    border-color:#00ffff;
}

/* ===== SIDEBAR ===== */
section[data-testid="stSidebar"]{
    background:
    linear-gradient(
        180deg,
        #000814,
        #001d3d,
        #003566
    );

    border-right:
    2px solid #00ffff44;
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

    padding:10px 12px;

    margin-bottom:8px;

    border-radius:10px;

    border:1px solid #00ffff33;

    background:#00ffff11;

    color:#00ffff;

    transition:.3s;
}

.search-card:hover{

    transform:translateX(6px);

    background:#00ffff22;

    box-shadow:
    0 0 15px #00ffff88;
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
