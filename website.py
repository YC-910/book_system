import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# =====================================
# PAGE CONFIG
# =====================================
st.set_page_config(
    page_title="📚 书橱记录系统",
    layout="wide"
)

# =====================================
# GOOGLE SHEETS AUTH
# =====================================
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

service_account_info = dict(st.secrets["gcp_service_account"])

creds = Credentials.from_service_account_info(
    service_account_info,
    scopes=scope
)

client = gspread.authorize(creds)

SHEET_ID = "1c8t964bqcoMl1BlSTrijp2QLBXXAH-58AlEZbCBtT0Q"

spreadsheet = client.open_by_key(SHEET_ID)
sheet = spreadsheet.worksheet("纸质书")

# =====================================
# LOAD DATA (SAFE)
# =====================================
@st.cache_data(ttl=60)
def load_data():
    data = sheet.get_all_values()

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)
    df.columns = df.iloc[0]
    df = df[1:]

    # clean empty spaces
    df = df.replace(r"^\s*$", pd.NA, regex=True)

    return df

df = load_data()

categories = df.columns.tolist()

# =====================================
# CLEAN CATEGORY COUNT (FIXED)
# =====================================
category_counts = {
    col: df[col].dropna().shape[0]
    for col in categories
}

total_books = sum(category_counts.values())

# =====================================
# STYLE (LIBRARY UI UPGRADE)
# =====================================
st.markdown("""
<style>

.main .block-container{
    padding: 1rem 2rem;
}

.title{
    text-align:center;
    font-size:52px;
    font-weight:900;
    margin-bottom:20px;
    color:#111;
}

/* BOOK CARD (MORE LIBRARY STYLE) */
.book-card{
    background: linear-gradient(145deg, #ffffff, #f3f4f6);
    border-radius:18px;
    padding:18px;
    min-height:140px;

    display:flex;
    align-items:center;
    justify-content:center;

    text-align:center;

    font-size:18px;
    font-weight:800;
    color:#000;

    box-shadow:0px 6px 18px rgba(0,0,0,0.12);

    border:1px solid #e5e7eb;

    transition:all 0.25s ease;
}

.book-card:hover{
    transform:translateY(-6px) scale(1.02);
    box-shadow:0px 10px 25px rgba(0,0,0,0.18);
}

/* SIDEBAR */
section[data-testid="stSidebar"]{
    background:#0f172a;
    color:white;
}

</style>
""", unsafe_allow_html=True)

# =====================================
# SIDEBAR
# =====================================
st.sidebar.title("📚 Library Menu")

search = st.sidebar.text_input("🔍 搜索书名")

st.sidebar.markdown("---")

st.sidebar.metric("📚 Total Books", total_books)

st.sidebar.markdown("---")

st.sidebar.subheader("➕ 添加新书")

new_book = st.sidebar.text_input("书名")

category = st.sidebar.selectbox("分类", categories)

if st.sidebar.button("添加书籍"):
    if new_book.strip():

        headers = sheet.row_values(1)
        col_index = headers.index(category) + 1

        col_values = sheet.col_values(col_index)
        next_row = len(col_values) + 1

        sheet.update_cell(next_row, col_index, new_book)

        st.sidebar.success("添加成功！")
        st.cache_data.clear()
        st.rerun()

# =====================================
# TITLE
# =====================================
st.markdown('<div class="title">📚 书橱记录系统</div>', unsafe_allow_html=True)

# =====================================
# TABS
# =====================================
tabs = st.tabs(categories)

for i, cat in enumerate(categories):

    with tabs[i]:

        books = df[cat].dropna().tolist()

        # SEARCH FIX (CHINESE SAFE)
        if search:
            books = [
                b for b in books
                if search.strip().lower() in str(b).lower()
            ]

        total = len(books)

        st.subheader(f"📂 {cat}")
        st.markdown(f"### 📚 Total: {total} books")

        if total == 0:
            st.info("没有找到书籍")
            continue

        # SMART GRID (ADAPTIVE)
        cols = st.columns(6)

        for idx, book in enumerate(books):
            with cols[idx % 6]:
                st.markdown(f"""
                <div class="book-card">
                    📖<br><br>{book}
                </div>
                """, unsafe_allow_html=True)
