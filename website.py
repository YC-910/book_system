import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from rapidfuzz import fuzz
from collections import defaultdict

# =====================
# PAGE CONFIG
# =====================
st.set_page_config(
    page_title="📚 藏书记录",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =====================
# HIDE UI
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
</style>
""", unsafe_allow_html=True)

# =====================
# GOOGLE SHEET AUTH
# =====================
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

service_account_info = dict(st.secrets["gcp_service_account"])
service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")

creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPE)
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
# PRECOMPUTE FLAT BOOK LIST (BIG SPEED BOOST)
# =====================
all_books = []
for cat in categories:
    for b in df[cat].dropna().tolist():
        all_books.append((b, cat))

# =====================
# NORMALIZATION
# =====================
def normalize(text):
    return str(text).strip().lower().replace(" ", "")

# =====================
# INDEX BUILD (FASTER SEARCH + DUPLICATE CHECK)
# =====================
book_index = {}
inverted_index = defaultdict(set)

for book, cat in all_books:
    key = normalize(book)

    book_index[key] = (book, cat)

    for ch in key:
        inverted_index[ch].add((book, cat))

# =====================
# DUPLICATE CHECK (OPTIMIZED)
# =====================
def find_duplicate(book_name, threshold=85):
    key = normalize(book_name)

    # O(1)
    if key in book_index:
        return (*book_index[key], 100)

    # candidate set
    candidates = set()
    for ch in key:
        candidates |= inverted_index.get(ch, set())

    best, best_score = None, 0

    for book, cat in candidates:
        score = fuzz.ratio(key, normalize(book))
        if score > best_score:
            best, best_score = (book, cat), score

    if best_score >= threshold:
        return (*best, best_score)

    return None, None, 0

# =====================
# SEARCH ENGINE (OPTIMIZED)
# =====================
def search_books(keyword):
    key = normalize(keyword)

    results = set()
    for ch in key:
        results |= inverted_index.get(ch, set())

    if not results:
        results = [(b, c) for b, c in all_books if key in normalize(b)]

    return results

# =====================
# UI HEADER
# =====================
st.markdown('<div class="title">📚 藏书记录</div>', unsafe_allow_html=True)
st.metric("📚 图书总数", len(all_books))

# =====================
# TABS
# =====================
library_tab, search_tab, add_tab = st.tabs(
    ["📚 图书馆", "🔍 搜索书本", "➕ 添加书本"]
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
    st.subheader("🔍 搜索书本")

    keyword = st.text_input("输入书名", placeholder="例如：法医")

    if keyword:
        results = search_books(keyword)

        st.write(f"找到 {len(results)} 本书")

        if not results:
            st.warning("没有找到相关书籍")

        for book, cat in results:
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
# ADD BOOK (2 COLUMNS UI)
# =====================
with add_tab:
    st.subheader("➕ 添加书本")

    col1, col2 = st.columns(2)

    with col1:
        new_book = st.text_input("书名", key="new_book")

    with col2:
        category = st.selectbox("种类", categories, key="add_category")

    if st.button("确定添加", use_container_width=True):

        if not new_book.strip():
            st.warning("请输入书名")

        else:
            found_book, found_cat, score = find_duplicate(new_book)

            if found_book:
                st.error(
                    f"❌ 检测到重复书籍\n\n"
                    f"📖 已存在: {found_book}\n"
                    f"📂 类别: {found_cat}\n"
                    f"📊 相似度: {score:.1f}%"
                )
            else:
                headers = sheet.row_values(1)
                col_index = headers.index(category) + 1
                next_row = len(sheet.col_values(col_index)) + 1

                sheet.update_cell(next_row, col_index, new_book)

                st.success(f"✅ 已添加：《{new_book}》")

                st.cache_data.clear()
                st.rerun()
