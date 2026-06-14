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
# GOOGLE SHEETS AUTH (STREAMLIT SECRETS)
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

# =====================================
# GOOGLE SHEET
# =====================================
SHEET_ID = "1c8t964bqcoMl1BlSTrijp2QLBXXAH-58AlEZbCBtT0Q"

spreadsheet = client.open_by_key(SHEET_ID)
sheet = spreadsheet.worksheet("纸质书")

# =====================================
# LOAD DATA
# =====================================
@st.cache_data(ttl=60)
def load_data():

    data = sheet.get_all_values()

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    df.columns = df.iloc[0]
    df = df[1:]

    return df

df = load_data()

# =====================================
# CATEGORY COUNT
# =====================================
def count_books(col):
    return df[col].replace(["", " "], pd.NA).dropna().shape[0]

category_counts = {
    col: count_books(col)
    for col in df.columns
}

total_books = sum(category_counts.values())

# =====================================
# STYLE
# =====================================
st.markdown("""
<style>

.main .block-container{
    padding-top:1rem;
    padding-left:2rem;
    padding-right:2rem;
}

.title{
    text-align:center;
    font-size:48px;
    font-weight:800;
    margin-bottom:25px;
}

.book-card{
    background:white;
    border-radius:16px;
    padding:20px;
    min-height:130px;

    display:flex;
    align-items:center;
    justify-content:center;

    text-align:center;

    font-size:18px;
    font-weight:700;
    color:black;

    box-shadow:0px 4px 12px rgba(0,0,0,0.15);

    transition:0.2s;
}

.book-card:hover{
    transform:translateY(-5px);
}

section[data-testid="stSidebar"]{
    background-color:#0f172a;
}

</style>
""", unsafe_allow_html=True)

# =====================================
# SIDEBAR
# =====================================
st.sidebar.title("📚 Library Menu")

search = st.sidebar.text_input(
    "🔍 搜索书名"
)

st.sidebar.markdown("---")

st.sidebar.metric(
    "📚 Total Books",
    total_books
)

st.sidebar.markdown("---")

st.sidebar.subheader("➕ 添加新书")

new_book = st.sidebar.text_input(
    "书名"
)

category = st.sidebar.selectbox(
    "分类",
    df.columns.tolist()
)

if st.sidebar.button("添加书籍"):

    if new_book.strip():

        headers = sheet.row_values(1)

        col_index = headers.index(category) + 1

        col_values = sheet.col_values(col_index)

        next_row = len(col_values) + 1

        sheet.update_cell(
            next_row,
            col_index,
            new_book
        )

        st.sidebar.success("添加成功！")

        st.cache_data.clear()

        st.rerun()

# =====================================
# TITLE
# =====================================
st.markdown(
    '<div class="title">📚 书橱记录系统</div>',
    unsafe_allow_html=True
)

# =====================================
# CATEGORY TABS
# =====================================
categories = df.columns.tolist()

tabs = st.tabs(categories)

for i, cat in enumerate(categories):

    with tabs[i]:

        books = (
            df[cat]
            .replace(["", " "], pd.NA)
            .dropna()
            .tolist()
        )

        # SEARCH
        if search:
            books = [
                b for b in books
                if search.lower() in str(b).lower()
            ]

        total = len(books)

        st.subheader(f"📂 {cat}")
        st.markdown(
            f"### 📚 Total: {total} books"
        )

        if total == 0:
            st.info("没有找到相关书籍")
            continue

        cols = st.columns(5)

        for idx, book in enumerate(books):

            with cols[idx % 5]:

                st.markdown(
                    f"""
                    <div class="book-card">
                        📖 {book}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
