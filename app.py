import os
import streamlit as st
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

st.set_page_config(
    page_title="NEA Protection Master Launcher",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -------------------- CSS: hide sidebar, menu/footer; keep layout clean --------------------
st.markdown(
    """
    <style>
    /* Sidebar off */
    [data-testid="stSidebar"] {display:none !important;}
    [data-testid="collapsedControl"] {display:none !important;}

    /* Remove Streamlit toolbars/menu/footer (config.toml removes topbar red circle best) */
    [data-testid="stToolbar"] {display:none !important;}
    #MainMenu {visibility:hidden;}
    footer {visibility:hidden;}

    /* Layout spacing (prevents logo cut) */
    .block-container{
        padding-top: 3.0rem !important;
        padding-bottom: 2.4rem !important;
        max-width: 1150px;
    }

    /* Center wrapper */
    .nea-center{
        display:flex;
        flex-direction:column;
        align-items:center;
        justify-content:center;
        text-align:center;
    }

    /* Logo frame (does NOT change logo colors) */
    .nea-logo-frame{
        display:inline-flex;
        padding: 10px;
        border-radius: 16px;
        border: 2px solid rgba(220, 38, 38, 0.85);
        background: #ffffff;
        box-shadow: 0 14px 30px rgba(0,0,0,0.10);
        margin-bottom: 14px;
    }

    /* Title */
    .nea-title{
        font-size: 46px;
        font-weight: 900;
        margin: 6px 0 8px 0;
        color: #111827;
        letter-spacing: 0.2px;
    }

    /* Tabs container */
    .tabs-grid{
        display:flex;
        flex-direction:column;
        gap:18px;
        align-items:center;
        margin-top: 16px;
        margin-bottom: 30px;
    }

    /* Tab buttons */
    div.stButton > button{
        width: 610px !important;
        height: 62px !important;
        border-radius: 16px !important;
        font-size: 16px !important;
        font-weight: 900 !important;
        border: 1px solid rgba(255,255,255,0.20) !important;
        box-shadow: 0 14px 28px rgba(0,0,0,0.10) !important;
        transition: transform 0.08s ease, filter 0.14s ease, box-shadow 0.14s ease;
        text-align: left !important;
        padding-left: 18px !important;
        letter-spacing: 0.1px;
        color: #ffffff !important;
    }
    div.stButton > button:hover{
        transform: translateY(-2px);
        filter: brightness(1.06);
        box-shadow: 0 16px 34px rgba(0,0,0,0.14) !important;
    }
    div.stButton > button:active{transform: translateY(0px);}

    /* Responsive */
    @media (max-width: 720px){
        div.stButton > button {width: 94vw !important;}
        .nea-title{font-size: 34px;}
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------- Navigation --------------------
def go(page_path: str):
    try:
        st.switch_page(page_path)
    except Exception:
        st.info("Navigation not available in this Streamlit version. Upgrade Streamlit or use multipage menu.")

# -------------------- Header: logo centered ABOVE title --------------------
st.markdown('<div class="nea-center">', unsafe_allow_html=True)

logo_path = os.path.join(BASE_DIR, "logo.jpg")
if os.path.exists(logo_path):
    img = Image.open(logo_path)  # NO color modifications
    st.markdown('<div class="nea-logo-frame">', unsafe_allow_html=True)
    st.image(img, width=125)
    st.markdown("</div>", unsafe_allow_html=True)

# Subtitle removed (as requested)
st.markdown('<div class="nea-title">NEA Protection &amp; Coordination Tools</div>', unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# -------------------- 4 blue-shade tabs with icons --------------------
pad_l, center, pad_r = st.columns([1, 2, 1])
with center:
    st.markdown('<div class="tabs-grid">', unsafe_allow_html=True)

    # 1
    st.markdown("""
    <style>
    div.stButton:nth-of-type(1) > button{
        background: linear-gradient(135deg, #0B5ED7 0%, #2563EB 55%, #1D4ED8 100%) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    if st.button("📈  Protection Coordination Tool (TCC Plot)"):
        go("pages/1_TCC_Tool.py")

    # 2
    st.markdown("""
    <style>
    div.stButton:nth-of-type(2) > button{
        background: linear-gradient(135deg, #0A58CA 0%, #1D4ED8 55%, #1E40AF 100%) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    if st.button("⚡  OC / EF Grid Coordination Tool"):
        go("pages/2_OC_EF_Grid.py")

    # 3
    st.markdown("""
    <style>
    div.stButton:nth-of-type(3) > button{
        background: linear-gradient(135deg, #1D4ED8 0%, #1E40AF 60%, #1E3A8A 100%) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    if st.button("📘  Protection Theory Guide"):
        go("pages/3_Theory.py")

    # 4
    st.markdown("""
    <style>
    div.stButton:nth-of-type(4) > button{
        background: linear-gradient(135deg, #1E40AF 0%, #1E3A8A 60%, #172554 100%) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    if st.button("🛠️  Working Methodology / Manual"):
        go("pages/4_Working.py")

    st.markdown("</div>", unsafe_allow_html=True)
