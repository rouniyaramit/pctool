import os
import streamlit as st
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

st.set_page_config(
    page_title="NEA Protection Master Launcher",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -------------------- CSS: hide sidebar + polish UI --------------------
st.markdown(
    """
    <style>
    /* Hide Streamlit sidebar completely */
    [data-testid="stSidebar"] {display: none !important;}
    [data-testid="collapsedControl"] {display: none !important;}

    /* Reduce top padding */
    .block-container {padding-top: 1.2rem; padding-bottom: 2.0rem; max-width: 1100px;}

    /* Hide Streamlit default menu/footer (optional) */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Center everything inside the main container */
    .nea-center {text-align: center;}

    /* Title */
    .nea-title {
        font-size: 44px;
        font-weight: 800;
        margin-top: 10px;
        margin-bottom: 8px;
        letter-spacing: 0.2px;
        color: #1f2937;
    }
    .nea-subtitle {
        font-size: 15px;
        color: #6b7280;
        margin-bottom: 24px;
    }

    /* Button styles */
    .nea-btn-wrap {
        display: flex;
        flex-direction: column;
        gap: 18px;
        align-items: center;
        margin-top: 12px;
        margin-bottom: 30px;
    }

    /* Make streamlit buttons fixed width & big */
    div.stButton > button {
        width: 560px !important;
        height: 56px !important;
        border-radius: 10px !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        border: 0 !important;
        box-shadow: 0 8px 18px rgba(0,0,0,0.08) !important;
        transition: transform 0.05s ease-in-out;
    }
    div.stButton > button:active {
        transform: scale(0.99);
    }

    /* Footer */
    .nea-footer {
        margin-top: 70px;
        text-align: center;
        color: #6b7280;
        font-style: italic;
        font-size: 14px;
        line-height: 1.5;
    }

    /* Mobile responsive */
    @media (max-width: 700px) {
        div.stButton > button {width: 95vw !important;}
        .nea-title {font-size: 34px;}
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------- Header (centered logo + title) --------------------
st.markdown('<div class="nea-center">', unsafe_allow_html=True)

logo_path = os.path.join(BASE_DIR, "logo.jpg")
if os.path.exists(logo_path):
    st.image(Image.open(logo_path), width=140)

st.markdown('<div class="nea-title">NEA Protection &amp; Coordination Tools</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="nea-subtitle">Protection and Automation Division, GOD • Nepal Electricity Authority</div>',
    unsafe_allow_html=True,
)

st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# -------------------- Navigation helpers --------------------
def go(page_path: str):
    """
    Works on Streamlit Cloud:
    - Newer Streamlit: st.switch_page
    - Fallback: show page_link
    """
    try:
        st.switch_page(page_path)
    except Exception:
        # If switch_page isn't available, user can use page links below
        pass

# -------------------- Buttons (Tkinter-like) --------------------
# Use columns to center buttons nicely
left_pad, center_col, right_pad = st.columns([1, 2, 1])

with center_col:
    # Button 1 (Blue)
    st.markdown(
        "<style>div.stButton:nth-of-type(1) > button{background:#0b5ed7;color:white;}</style>",
        unsafe_allow_html=True,
    )
    if st.button("Open Protection Coordination Tool (TCC Plot)"):
        go("pages/1_TCC_Tool.py")

    # Button 2 (Blue - slightly different)
    st.markdown(
        "<style>div.stButton:nth-of-type(2) > button{background:#0a58ca;color:white;}</style>",
        unsafe_allow_html=True,
    )
    if st.button("Open OC / EF Grid Coordination Tool"):
        go("pages/2_OC_EF_Grid.py")

    # Button 3 (Purple)
    st.markdown(
        "<style>div.stButton:nth-of-type(3) > button{background:#4c1d95;color:white;}</style>",
        unsafe_allow_html=True,
    )
    if st.button("Open Protection Theory Guide"):
        go("pages/3_Theory.py")

    # Button 4 (Deep Purple)
    st.markdown(
        "<style>div.stButton:nth-of-type(4) > button{background:#3b0764;color:white;}</style>",
        unsafe_allow_html=True,
    )
    if st.button("Open Working Methodology / Manual"):
        go("pages/4_Working.py")

# -------------------- If switch_page isn't available, show links --------------------
# (Still no sidebar; user can click links here)
try:
    # If switch_page exists, this section is not needed, but harmless.
    pass
except Exception:
    pass

st.markdown(
    """
    <div class="nea-footer">
        Protection and Automation Division, GOD<br/>
        Nepal Electricity Authority
    </div>
    """,
    unsafe_allow_html=True,
)
