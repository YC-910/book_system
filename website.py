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

# FIX SECRET FORMAT
service_account_info = dict(st.secrets["gcp_service_account"])
service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")

creds = Credentials.from_service_account_info(
    service_account_info,
    scopes=scope
)

client = gspread.authorize(creds)

# =====================================
# SHEET CONFIG
# =====================================
SHEET_ID = "YOUR_SHEET_ID"
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

    # clean empty
    df = df.replace(r"^\s*$", pd.NA, regex=True)

    return df

df = load_data()
categories = df.columns.tolist()

# =====================================
# COUNT FIX
# =====================================
def count_books(col):
    return df[col].dropna().shape[0]

category_counts = {col: count_books(col) for col in categories}
total_books = sum(category_counts.values())

# =====================================
# STYLE (LIBRARY UI)
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
}

.book-card{
    background: linear-gradient(145deg, #fff, #f3f4f6);
    border-radius:18px;
    padding:18px;
    min-height:140px;

    display:flex;
    align-items:center;
    justify-content:center;

    text-align:center;

    font-size:20px;
    font-weight:800;
    color:black;

    box-shadow:0px 6px 18px rgba(0,0,0,0.12);

    transition:0.2s;
}

.book-card:hover{
    transform:translateY(-6px);
}

section[data-testid="stSidebar"]{
    background:#0f172a;
}

</style>
""", unsafe_allow_html=True)

# =====================================
# SIDEBAR
# =====================================
st.sidebar.title("📚 Library")

search = st.sidebar.text_input("🔍 Search book")

st.sidebar.metric("📚 Total Books", total_books)

st.sidebar.markdown("---")
st.sidebar.subheader("➕ Add Book")

new_book = st.sidebar.text_input("Book name")
category = st.sidebar.selectbox("Category", categories)

if st.sidebar.button("Add"):
    if new_book.strip():
        headers = sheet.row_values(1)
        col_index = headers.index(category) + 1

        col_values = sheet.col_values(col_index)
        next_row = len(col_values) + 1

        sheet.update_cell(next_row, col_index, new_book)

        st.success("Added successfully!")
        st.cache_data.clear()
        st.rerun()

# =====================================
# TITLE
# =====================================
st.markdown('<div class="title">📚 Library System</div>', unsafe_allow_html=True)

# =====================================
# TABS
# =====================================
tabs = st.tabs(categories)

def normalize(x):
    return str(x).replace(" ", "").lower()

for i, cat in enumerate(categories):

    with tabs[i]:

        books = df[cat].dropna().tolist()

        # SEARCH FIX (Chinese + English)
        if search:
            books = [b for b in books if normalize(search) in normalize(b)]

        st.subheader(f"📂 {cat}")
        st.markdown(f"### 📚 Total: {len(books)} books")

        if not books:
            st.info("No books found")
            continue

        cols = st.columns(6)

        for idx, book in enumerate(books):
            with cols[idx % 6]:
                st.markdown(f"""
                <div class="book-card">
                    📖 {book}
                </div>
                """, unsafe_allow_html=True)
