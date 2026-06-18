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
# UI STYLE (POLISHED SPACE LIBRARY)
# =====================
st.markdown("""
<style>

/* =========================
   🌌 AQUARIUS STAR BACKGROUND
========================= */
.stApp{
    background:
    radial-gradient(circle at 15% 20%, rgba(173,216,255,0.10), transparent 35%),
    radial-gradient(circle at 80% 30%, rgba(140,180,255,0.08), transparent 40%),
    radial-gradient(circle at 50% 80%, rgba(180,160,255,0.06), transparent 45%),
    linear-gradient(180deg, #050814, #0b1026, #0a0f1f);

    color:white;
}

/* soft constellation stars */
.stApp::before{
    content:"";
    position:fixed;
    inset:0;

    background-image:
        radial-gradient(1.2px 1.2px at 10% 20%, rgba(255,255,255,0.5), transparent),
        radial-gradient(1px 1px at 25% 70%, rgba(200,220,255,0.35), transparent),
        radial-gradient(1px 1px at 60% 40%, rgba(255,255,255,0.3), transparent),
        radial-gradient(1px 1px at 80% 80%, rgba(180,200,255,0.25), transparent),
        radial-gradient(1px 1px at 40% 10%, rgba(255,255,255,0.2), transparent);

    background-size: 500px 500px;
    opacity: 0.25;
    pointer-events: none;
}

/* =========================
   ✨ TITLE (AQUARIUS GLOW)
========================= */
.title{
    text-align:center;
    font-size:60px;
    font-weight:800;

    color:#dbeafe;

    margin:10px 0 25px 0;

    text-shadow:
        0 0 10px rgba(120,180,255,0.25),
        0 0 25px rgba(180,160,255,0.15);
}

/* =========================
   📊 METRICS
========================= */
div[data-testid="stMetric"]{
    background:rgba(255,255,255,0.06);
    padding:12px;
    border-radius:12px;
    border:1px solid rgba(255,255,255,0.12);
    backdrop-filter: blur(8px);
}

/* =========================
   📑 TABS
========================= */
.stTabs [data-baseweb="tab"]{
    background:rgba(255,255,255,0.05);
    border-radius:10px;
    color:#cfe3ff;
    border:1px solid rgba(255,255,255,0.08);
}

.stTabs [aria-selected="true"]{
    background:rgba(120,160,255,0.25) !important;
    color:white !important;
}

/* =========================
   📚 GRID
========================= */
.book-grid{
    display:grid;
    grid-template-columns:repeat(6,1fr);
    gap:24px;
    margin-top:20px;
}

/* =========================
   📖 BOOK CARD (soft cosmic glass)
========================= */
.book-card{
    background:rgba(255,255,255,0.06);
    backdrop-filter:blur(12px);

    border:1px solid rgba(255,255,255,0.12);

    border-radius:16px;
    height:160px;

    display:flex;
    align-items:center;
    justify-content:center;

    text-align:center;

    font-size:18px;
    font-weight:600;

    color:#eaf2ff;

    transition:0.25s ease;
}

.book-card:hover{
    transform:translateY(-6px) scale(1.02);
    background:rgba(120,160,255,0.16);
    box-shadow:0 12px 30px rgba(0,0,0,0.35);
}

/* =========================
   📚 SIDEBAR (deep space)
========================= */
section[data-testid="stSidebar"]{
    background:linear-gradient(180deg,#050814,#0a1024,#0d1430);
}

section[data-testid="stSidebar"] *{
    color:#e6f0ff;
}

/* =========================
   🔎 SEARCH RESULT CARD
========================= */
.search-card{
    display:flex;
    justify-content:space-between;

    padding:8px 10px;
    margin-bottom:6px;

    border-radius:10px;

    background:rgba(255,255,255,0.05);

    border:1px solid rgba(255,255,255,0.08);

    color:#dbe7ff;

    transition:0.2s;
}

.search-card:hover{
    background:rgba(120,160,255,0.18);
    transform:translateX(4px);
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
# DASHBOARD (TOP)
# =====================
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("📚 图书总数", total_books)

with col2:
    st.metric("📂 分类数量", len(categories))

# divider between search + stats (as you requested)
st.markdown("---")

# =====================
# TITLE
# =====================
st.markdown('<div class="title">📚 宇宙图书系统</div>', unsafe_allow_html=True)

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
