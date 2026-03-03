import os
import streamlit as st
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

st.set_page_config(
    page_title="NEA Protection Master Launcher",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -------------------- CSS: hide sidebar + top bar + polish UI --------------------
st.markdown(
    """
    <style>
    /* Hide sidebar completely */
    [data-testid="stSidebar"] {display: none !important;}
    [data-testid="collapsedControl"] {display: none !important;}

    /* Hide Streamlit Cloud top header (Share, GitHub, menu, etc.) */
    [data-testid="stHeader"] {display: none !important;}
    header {display: none !important;}

    /* Hide footer */
    footer {display: none !important;}
    #MainMenu {visibility: hidden;}

    /* Page padding (fix logo cut-off) */
    .block-container {
        padding-top: 2.2rem !important;
        padding-bottom: 2.5rem !important;
        max-width: 1100px;
    }

    /* Center wrapper */
    .nea-center {text-align: center;}

    /* Logo frame */
    .nea-logo-box{
        display: inline-flex;
        padding: 10px;
        border-radius: 14px;
        border: 2px solid rgba(220, 38, 38, 0.85);
        background: rgba(255,255,255,0.9);
        box-shadow: 0 10px 24px rgba(0,0,0,0.06);
        margin-top: 6px;
        margin-bottom: 14px;
    }

    /* Title text */
    .nea-title {
        font-size: 44px;
        font-weight: 900;
        margin: 10px 0 6px 0;
        color: #111827;
        letter-spacing: 0.2px;
    }
    .nea-subtitle {
        font-size: 14px;
        color: #6b7280;
        margin-bottom: 28px;
    }

    /* Divider line spacing */
    hr {margin: 18px 0 24px 0 !important;}

    /* TAB buttons (pill style) */
    .tab-wrap{
        display:flex;
        flex-direction:column;
        align-items:center;
        gap:16px;
        margin-top: 6px;
        margin-bottom: 40px;
    }

    /* Make Streamlit buttons look like tabs */
    div.stButton > button {
        width: 560px !important;
        height: 58px !important;
        border-radius: 14px !important;
        font-size: 16px !important;
        font-weight: 800 !important;
        border: 1px solid rgba(255,255,255,0.14) !important;
        box-shadow: 0 12px 26px rgba(0,0,0,0.08) !important;
        transition: transform 0.06s ease-in-out, filter 0.12s ease-in-out;
        text-align: left !important;
        padding-left: 18px !important;
    }
    div.stButton > button:hover {
        filter: brightness(1.04);
        transform: translateY(-1px);
    }
    div.stButton > button:active {transform: translateY(0px);}

    /* Footer */
    .nea-footer{
        margin-top: 70px;
        text-align:center;
        color:#6b7280;
        font-style: italic;
        font-size: 14px;
        line-height: 1.5;
    }

    /* Mobile */
    @media (max-width: 700px){
        div.stButton > button {width: 94vw !important;}
        .nea-title{font-size: 34px;}
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------- Navigation --------------------
def go(page_path: str):
    # Best navigation (newer Streamlit)
    try:
        st.switch_page(page_path)
    except Exception:
        # Fallback if switch_page isn't supported
        st.info("If navigation does not work, update Streamlit or use the multipage menu.")
        return


# -------------------- Header (logo centered & not cut) --------------------
st.markdown('<div class="nea-center">', unsafe_allow_html=True)

logo_path = os.path.join(BASE_DIR, "logo.jpg")
if os.path.exists(logo_path):
    img = Image.open(logo_path)
    st.markdown('<div class="nea-logo-box">', unsafe_allow_html=True)
    st.image(img, width=120)  # smaller width avoids cropping on some browsers
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="nea-title">NEA Protection &amp; Coordination Tools</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="nea-subtitle">Protection and Automation Division, GOD • Nepal Electricity Authority</div>',
    unsafe_allow_html=True,
)

st.markdown("</div>", unsafe_allow_html=True)
st.divider()

# -------------------- 4 "Tab" buttons with icons + blue shades --------------------
# Blue shade palette (different tones)
tab_styles = [
    ("#0B5ED7", "📈  Open Protection Coordination Tool (TCC Plot)", "pages/1_TCC_Tool.py"),
    ("#0A58CA", "⚡  Open OC / EF Grid Coordination Tool", "pages/2_OC_EF_Grid.py"),
    ("#1D4ED8", "📘  Open Protection Theory Guide", "pages/3_Theory.py"),
    ("#1E40AF", "🛠️  Open Working Methodology / Manual", "pages/4_Working.py"),
]

# Center area
pad_l, center, pad_r = st.columns([1, 2, 1])
with center:
    st.markdown('<div class="tab-wrap">', unsafe_allow_html=True)

    # Button 1
    st.markdown(f"<style>div.stButton:nth-of-type(1)>button{{background:{tab_styles[0][0]};color:white;}}</style>", unsafe_allow_html=True)
    if st.button(tab_styles[0][1]):
        go(tab_styles[0][2])

    # Button 2
    st.markdown(f"<style>div.stButton:nth-of-type(2)>button{{background:{tab_styles[1][0]};color:white;}}</style>", unsafe_allow_html=True)
    if st.button(tab_styles[1][1]):
        go(tab_styles[1][2])

    # Button 3
    st.markdown(f"<style>div.stButton:nth-of-type(3)>button{{background:{tab_styles[2][0]};color:white;}}</style>", unsafe_allow_html=True)
    if st.button(tab_styles[2][1]):
        go(tab_styles[2][2])

    # Button 4
    st.markdown(f"<style>div.stButton:nth-of-type(4)>button{{background:{tab_styles[3][0]};color:white;}}</style>", unsafe_allow_html=True)
    if st.button(tab_styles[3][1]):
        go(tab_styles[3][2])

    st.markdown("</div>", unsafe_allow_html=True)

# -------------------- Footer --------------------
st.markdown(
    """
    <div class="nea-footer">
        Protection and Automation Division, GOD<br/>
        Nepal Electricity Authority
    </div>
    """,
    unsafe_allow_html=True,
)
