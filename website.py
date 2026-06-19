import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from PIL import Image
import easyocr
from PIL import Image
import numpy as np
    
# =====================
# PAGE CONFIG
# =====================
st.set_page_config(
    page_title="📚 藏书记录",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =====================
# CSS (same as yours)
# =====================
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}

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
</style>
""", unsafe_allow_html=True)

# =====================
# GOOGLE SHEET
# =====================
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

service_account_info = dict(st.secrets["gcp_service_account"])
service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")

creds = Credentials.from_service_account_info(
    service_account_info,
    scopes=scope
)

client = gspread.authorize(creds)

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

total_books = sum(df[c].dropna().shape[0] for c in categories)

# =====================
# AI OCR FUNCTION
# =====================

def extract_text(image):
    img = np.array(image)
    result = reader.readtext(img, detail=0)
    return " ".join(result)

def find_book(text):
    text = text.lower()

    for cat in categories:
        for book in df[cat].dropna().tolist():

            book_clean = str(book).lower()

            # flexible matching
            if any(word in book_clean for word in text.split() if len(word) > 3):
                return book, cat

    return None, None

# =====================
# UI HEADER
# =====================
st.markdown('<div class="title">📚 藏书记录</div>', unsafe_allow_html=True)
st.metric("📚 图书总数", total_books)

# =====================
# TABS (NOW 4 TABS)
# =====================
library_tab, search_tab, add_tab, scan_tab = st.tabs(
    ["📚 图书馆", "🔍 搜索书本", "➕ 添加书本", "📸 扫描书本"]
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

            html = '<div class="book-grid">'
            for book in books:
                html += f'<div class="book-card">📖 {book}</div>'
            html += "</div>"

            st.markdown(html, unsafe_allow_html=True)

# =====================
# SEARCH
# =====================
with search_tab:
    keyword = st.text_input("输入书名")

    if keyword:
        results = []

        for cat in categories:
            for book in df[cat].dropna().tolist():
                if keyword.lower() in str(book).lower():
                    results.append((book, cat))

        st.write(f"找到 {len(results)} 本书")

        for book, cat in results:
            st.write(f"📖 {book} ({cat})")

# =====================
# ADD
# =====================
with add_tab:
    new_book = st.text_input("书名")
    category = st.selectbox("种类", categories)

    if st.button("添加"):
        headers = sheet.row_values(1)
        col_index = headers.index(category) + 1
        next_row = len(sheet.col_values(col_index)) + 1

        sheet.update_cell(next_row, col_index, new_book)

        st.success("添加成功")
        st.cache_data.clear()
        st.rerun()

# =====================
# 📸 SCANNER TAB (NEW)
# =====================
with scan_tab:

    st.subheader("📸 扫描书本")

    uploaded = st.file_uploader("上传书本照片", type=["png", "jpg", "jpeg"])

    if uploaded:

        image = Image.open(uploaded)
        st.image(image, caption="扫描图片", use_container_width=True)

        text = extract_text(image)
        st.write("🧠 识别结果:", text)

        book, cat = find_book(text)

        if book:
            st.success(f"✅ 你已经有这本书：{book}")
            st.info(f"📂 分类: {cat}")
        else:
            st.error("❌ 你没有这本书")
