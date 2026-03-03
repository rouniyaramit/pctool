import os
import streamlit as st
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

st.set_page_config(
    page_title="NEA Protection Master Launcher",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -------------------- GLOBAL CSS --------------------
st.markdown("""
<style>

/* Force light grey background */
html, body, [data-testid="stApp"] {
    background: #eef2f7 !important;
}

/* Remove sidebar */
[data-testid="stSidebar"] {display:none !important;}
[data-testid="collapsedControl"] {display:none !important;}

/* Remove menu/footer */
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}

/* Main container spacing */
.block-container{
    padding-top: 3.2rem !important;
    padding-bottom: 2.5rem !important;
    max-width: 900px;      /* THIS controls straight alignment */
    margin: auto;
}

/* Master wrapper */
.center-wrapper{
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
    text-align:center;
}

/* Logo frame */
.logo-frame{
    display:inline-flex;
    padding:10px;
    border-radius:16px;
    border:2px solid rgba(220,38,38,0.85);
    background:white;
    box-shadow:0 14px 30px rgba(0,0,0,0.10);
    margin-bottom:18px;
}

/* Title */
.main-title{
    font-size:46px;
    font-weight:900;
    color:#111827;
    margin:8px 0 25px 0;
    letter-spacing:0.2px;
}

/* Buttons */
div.stButton > button{
    width:100% !important;   /* EXACT SAME WIDTH as container */
    height:64px !important;
    border-radius:18px !important;
    font-size:16px !important;
    font-weight:900 !important;
    border:none !important;
    box-shadow:0 14px 28px rgba(0,0,0,0.12) !important;
    transition: all 0.15s ease;
    text-align:center !important;
    color:white !important;
}
div.stButton > button:hover{
    transform: translateY(-2px);
    filter: brightness(1.07);
}

/* Responsive */
@media (max-width: 720px){
    .main-title{font-size:32px;}
}

</style>
""", unsafe_allow_html=True)

# -------------------- HEADER --------------------
st.markdown('<div class="center-wrapper">', unsafe_allow_html=True)

logo_path = os.path.join(BASE_DIR, "logo.jpg")
if os.path.exists(logo_path):
    img = Image.open(logo_path)   # NO color modification
    st.markdown('<div class="logo-frame">', unsafe_allow_html=True)
    st.image(img, width=130)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="main-title">NEA Protection & Coordination Tools</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# -------------------- NAVIGATION FUNCTION --------------------
def go(page):
    try:
        st.switch_page(page)
    except:
        pass

# -------------------- BUTTONS (perfect straight alignment) --------------------

# Blue Shade 1
st.markdown("""
<style>
div.stButton:nth-of-type(1) > button{
background: linear-gradient(135deg,#0B5ED7,#2563EB,#1D4ED8) !important;
}
</style>
""", unsafe_allow_html=True)
if st.button("📈  Protection Coordination Tool (TCC Plot)"):
    go("pages/1_TCC_Tool.py")

# Blue Shade 2
st.markdown("""
<style>
div.stButton:nth-of-type(2) > button{
background: linear-gradient(135deg,#0A58CA,#1D4ED8,#1E40AF) !important;
}
</style>
""", unsafe_allow_html=True)
if st.button("⚡  OC / EF Grid Coordination Tool"):
    go("pages/2_OC_EF_Grid.py")

# Blue Shade 3
st.markdown("""
<style>
div.stButton:nth-of-type(3) > button{
background: linear-gradient(135deg,#1D4ED8,#1E40AF,#1E3A8A) !important;
}
</style>
""", unsafe_allow_html=True)
if st.button("📘  Protection Theory Guide"):
    go("pages/3_Theory.py")

# Blue Shade 4
st.markdown("""
<style>
div.stButton:nth-of-type(4) > button{
background: linear-gradient(135deg,#1E40AF,#1E3A8A,#172554) !important;
}
</style>
""", unsafe_allow_html=True)
if st.button("🛠️  Working Methodology / Manual"):
    go("pages/4_Working.py")
