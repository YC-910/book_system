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
# SEARCH ENGINE
# =====================

def search_engine_v2(keyword):
    key = normalize(keyword)

    results = {}

    # =====================
    # FAST CANDIDATE GATHERING
    # =====================
    candidates = set()

    for ch in key:
        candidates.update(inverted_index.get(ch, set()))

    # fallback if too strict
    if not candidates:
        for cat in categories:
            for book in df[cat].dropna().tolist():
                candidates.add((book, cat))

    # =====================
    # SCORING ENGINE
    # =====================
    for book, cat in candidates:

        norm_book = normalize(book)
        score = 0

        # EXACT MATCH
        if key == norm_book:
            score = 1000

        # PREFIX MATCH
        elif norm_book.startswith(key):
            score += 800

        # SUBSTRING MATCH
        elif key in norm_book:
            score += 500

        # FUZZY MATCH (main intelligence layer)
        score += fuzz.ratio(key, norm_book)

        # CHARACTER OVERLAP BOOST
        overlap = sum(1 for ch in key if ch in norm_book)
        score += overlap * 8

        # store best score only
        if book not in results or score > results[book][0]:
            results[book] = (score, book, cat)

    # =====================
    # SORT RESULTS
    # =====================
    ranked = sorted(results.values(), key=lambda x: x[0], reverse=True)

    return ranked

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
    transition:0.3s ease;
}

.book-card:hover{
    transform: translateY(-6px);
    box-shadow: 0 15px 35px rgba(120,180,255,0.25);
    border: 1px solid rgba(120,180,255,0.5);
}

@media (max-width: 1200px){
    .book-grid{ grid-template-columns: repeat(4, 1fr); }
}

@media (max-width: 800px){
    .book-grid{ grid-template-columns: repeat(2, 1fr); }
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
# INDEX BUILD
# =====================
book_index = {}
inverted_index = defaultdict(set)

for cat in categories:
    for book in df[cat].dropna().tolist():
        key = normalize(book)

        book_index[key] = (book, cat)

        for ch in key:
            inverted_index[ch].add((book, cat))

# =====================
# COUNT
# =====================
total_books = sum(df[c].dropna().shape[0] for c in categories)

st.markdown('<div class="title">📚 藏书记录</div>', unsafe_allow_html=True)
st.metric("📚 图书总数", total_books)

# =====================
# DUPLICATE CHECK
# =====================
def find_duplicate(book_name, threshold=85):
    results = search_engine_v2(book_name)

    if not results:
        return None, None, 0

    best_score, book, cat = results[0]

    if best_score >= 900:  # near-exact duplicate
        return book, cat, best_score / 10

    if best_score >= threshold:
        return book, cat, best_score

    return None, None, 0

# =====================
# TABS
# =====================
library_tab, search_tab, add_tab = st.tabs(
    ["📚 图书馆", "🔍 搜索书本", "➕ 添加书本"]
)

# =====================
# LIBRARY TAB
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
# SEARCH TAB
# =====================
with search_tab:
    st.subheader("🔍 搜索书本")

    keyword = st.text_input("输入书名", placeholder="例如：法医")

    if keyword:

        results = search_engine_v2(keyword)

        st.write(f"找到 {len(results)} 本书")

        if not results:
            st.warning("没有找到相关书籍")

        for score, book, cat in results[:20]:
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
                <small>📂 {cat}</small><br>
                <small>🔥 score: {score:.1f}</small>
            </div>
            """, unsafe_allow_html=True)
            
# =====================
# ADD TAB
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
