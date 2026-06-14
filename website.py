import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# =====================
# PAGE CONFIG
# =====================
st.set_page_config(
    page_title="📚 Reading App",
    layout="wide"
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
# UI STYLE (MODERN READING APP)
# =====================
st.markdown("""
<style>

/* BACKGROUND */
.main {
    background: #f5f7fb;
}

/* TITLE */
.title {
    text-align:center;
    font-size:48px;
    font-weight:900;
    margin-bottom:15px;
    color:#111827;
}

/* CATEGORY CARDS (DASHBOARD STYLE) */
.category-card {
    background: linear-gradient(135deg, #ffffff, #f3f4f6);
    border-radius: 18px;
    padding: 18px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.08);
    text-align: center;
    font-weight: 800;
    margin-bottom: 15px;
}

/* BOOK GRID */
.book-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 22px;
    margin-top: 10px;
}

/* BOOK CARD (READING STYLE) */
.book-card {
    background: white;
    border-radius: 14px;
    padding: 16px;
    height: 120px;

    display: flex;
    align-items: center;
    justify-content: center;

    text-align: center;

    font-size: 18px;
    font-weight: 700;
    color: #111827;

    box-shadow: 0 6px 16px rgba(0,0,0,0.08);

    transition: all 0.25s ease;
    border: 1px solid #eef2f7;
}

.book-card:hover {
    transform: translateY(-6px) scale(1.02);
    box-shadow: 0 10px 25px rgba(0,0,0,0.12);
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background: #111827;
    color: white;
}

</style>
""", unsafe_allow_html=True)

# =====================
# SIDEBAR (CLEAN APP STYLE)
# =====================
st.sidebar.title("📚 Library")

search = st.sidebar.text_input("🔍 Search book")

st.sidebar.metric("📖 Total Books", total_books)

st.sidebar.markdown("---")

st.sidebar.subheader("➕ Add Book")

new_book = st.sidebar.text_input("Book name")
category = st.sidebar.selectbox("Category", categories)

if st.sidebar.button("Add"):
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
st.markdown('<div class="title">📚 Reading Dashboard</div>', unsafe_allow_html=True)

# =====================
# CATEGORY DASHBOARD (HOME UI)
# =====================
st.markdown("## 📂 Categories")

cols = st.columns(len(categories))

for i, cat in enumerate(categories):
    count = count_books(cat)

    with cols[i]:
        st.markdown(f"""
        <div class="category-card">
            📚 {cat}<br>
            <span style="font-size:20px;">{count} books</span>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# =====================
# TABS
# =====================
tabs = st.tabs(categories)

for i, cat in enumerate(categories):

    with tabs[i]:

        books = df[cat].dropna().tolist()

        if search:
            books = [b for b in books if search.lower() in str(b).lower()]

        st.markdown(f"### 📖 {cat} Books")

        if not books:
            st.info("No books found")
            continue

        html = '<div class="book-grid">'

        for book in books:
            html += f'<div class="book-card">📖 {book}</div>'

        html += "</div>"

        st.markdown(html, unsafe_allow_html=True)
