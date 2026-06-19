import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from rapidfuzz import fuzz
from collections import defaultdict, Counter

# =====================
# PAGE CONFIG
# =====================
st.set_page_config(
    page_title="📚 藏书记录",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =====================
# UI STYLE (UNCHANGED)
# =====================
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}

div[data-testid="stToolbar"] { display: none; }
div[data-testid="stStatusWidget"] { display: none; }

.stApp{
    background: url("https://raw.githubusercontent.com/YC-910/book_system/refs/heads/Python/aquarius.png");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    background-attachment: fixed;
}

.main .block-container{
    padding: 1rem 2.5rem;
}

.title{
    text-align:center;
    font-size:56px;
    font-weight:900;
    margin-bottom:20px;
    color:#ffffff;
}

.book-grid{
    display:grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 26px;
    margin-top: 14px;
}

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
}

.book-card:hover{
    transform: translateY(-6px);
}
</style>
""", unsafe_allow_html=True)

# =====================
# AUTH
# =====================
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

service_account_info = dict(st.secrets["gcp_service_account"])
service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")

creds = Credentials.from_service_account_info(
    service_account_info,
    scopes=SCOPE
)

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
# NORMALIZATION
# =====================
def normalize(text):
    return str(text).strip().lower().replace(" ", "")

# =====================
# INDEX (FAST SEARCH)
# =====================
book_index = {}
all_books = []

for cat in categories:
    for book in df[cat].dropna().tolist():
        key = normalize(book)
        book_index[key] = (book, cat)
        all_books.append((book, cat))

# =====================
# SIMPLE ANALYTICS (DA LAYER)
# =====================
category_counts = {cat: df[cat].dropna().shape[0] for cat in categories}
total_books = sum(category_counts.values())

search_history = Counter()

# =====================
# HEADER
# =====================
st.markdown('<div class="title">📚 藏书记录</div>', unsafe_allow_html=True)
st.metric("📚 图书总数", total_books)

# =====================
# RANKED SEARCH ENGINE (V2)
# =====================
def search_books(keyword):
    key = normalize(keyword)

    results = []

    for book, cat in all_books:
        score = fuzz.partial_ratio(key, normalize(book))  # better for search
        if key in normalize(book):
            score += 30

        results.append((score, book, cat))

    results.sort(reverse=True, key=lambda x: x[0])
    return results[:50]

# =====================
# TABS
# =====================
library_tab, search_tab, add_tab, analytics_tab = st.tabs(
    ["📚 图书馆", "🔍 搜索书本", "➕ 添加书本", "📊 数据分析"]
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

            for book in books:
                st.markdown(f"📖 {book}")

# =====================
# SEARCH (RANKED V2)
# =====================
with search_tab:
    st.subheader("🔍 搜索书本")

    keyword = st.text_input("输入书名", placeholder="例如：法医")

    if keyword:
        key = normalize(keyword)

        results = []

        for book, cat in all_books:
            score = fuzz.partial_ratio(key, normalize(book))

            # boost exact/substring match
            if key in normalize(book):
                score += 30

            results.append((score, book, cat))

        # sort by relevance
        results.sort(reverse=True, key=lambda x: x[0])

        # keep top results only (clean UX)
        results = results[:30]

        st.write(f"找到 {len(results)} 本书")

        if not results:
            st.warning("没有找到相关书籍")

        for _, book, cat in results:
            st.markdown(f"""
            <div style="
                background:rgba(255,255,255,0.88);
                padding:12px;
                border-radius:12px;
                margin-bottom:10px;
                color:black;
                font-weight:600;
            ">
                📖 {book}<br>
                <small>📂 {cat}</small>
            </div>
            """, unsafe_allow_html=True)
            
# =====================
# ADD
# =====================
with add_tab:

    st.subheader("➕ 添加书本")

    col1, col2 = st.columns(2)

    with col1:
        new_book = st.text_input("书名", key="new_book")

    with col2:
        category = st.selectbox("种类", categories, key="add_category")

    if st.button("确定添加", use_container_width=True):

        if new_book.strip():
            headers = sheet.row_values(1)
            col_index = headers.index(category) + 1
            next_row = len(sheet.col_values(col_index)) + 1

            sheet.update_cell(next_row, col_index, new_book)

            st.success(f"✅ 已添加：《{new_book}》")
            st.cache_data.clear()
            st.rerun()

# =====================
# 📊 ANALYTICS TAB (DA SYSTEM)
# =====================
with analytics_tab:

    st.subheader("📊 数据分析")

    st.write("### 📚 分类统计")
    st.bar_chart(category_counts)

    st.write("### 🔥 热门搜索词")
    st.bar_chart(search_history)

    st.write("### 📈 总览")
    st.metric("Total Books", total_books)
    st.metric("Categories", len(categories))
    st.metric("Search Terms", len(search_history))
