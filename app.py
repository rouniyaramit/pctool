import os
import streamlit as st

# ----------------- Config -----------------
st.set_page_config(
    page_title="NEA Protection & Coordination Tools",
    layout="wide",
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "logo.png")

# ----------------- CSS (Tkinter Clone Start Screen) -----------------
st.markdown(
    """
<style>
/* Hide sidebar */
[data-testid="stSidebar"] {display:none !important;}

/* Tight padding */
.block-container{
    padding-top: 10px !important;
    padding-left: 14px !important;
    padding-right: 14px !important;
    padding-bottom: 10px !important;
}

/* Centered content like Tkinter master window */
.center-wrap{
    max-width: 900px;
    margin: 0 auto;
    text-align: center;
}

/* Title */
.main-title{
    font-size: 34px;
    font-weight: 900;
    margin-top: 8px;
    margin-bottom: 22px;
    color: #222;
}

/* Button base style */
div.stButton > button{
    height: 62px !important;
    font-size: 18px !important;
    font-weight: 900 !important;
    border-radius: 6px !important;
    border: 0px !important;
}

/* Color wrappers for buttons */
.btn-blue button{background:#0a74c9 !important; color:white !important;}
.btn-blue2 button{background:#0a5fb0 !important; color:white !important;}
.btn-purple button{background:#4a2cc2 !important; color:white !important;}
.btn-purple2 button{background:#35127a !important; color:white !important;}

/* Footer */
.footer{
    margin-top: 44px;
    font-style: italic;
    color: #555;
    font-size: 15px;
}

/* Reduce empty whitespace between widgets */
div[data-testid="stVerticalBlock"]{gap: 0.55rem !important;}
</style>
""",
    unsafe_allow_html=True
)

# ----------------- Navigation helper -----------------
def go(page_path: str):
    """
    Navigate to a multipage file inside /pages.
    Requires Streamlit >= 1.31.0 for st.switch_page.
    """
    try:
        st.switch_page(page_path)
    except Exception:
        st.error(
            "Navigation failed. Please update Streamlit in requirements.txt:\n"
            "streamlit>=1.31.0"
        )

# ----------------- UI -----------------
st.markdown("<div class='center-wrap'>", unsafe_allow_html=True)

# Logo (top center)
if os.path.exists(LOGO_PATH):
    st.image(LOGO_PATH, width=180)
else:
    st.warning("logo.png not found in root folder.")

# Title
st.markdown("<div class='main-title'>NEA Protection &amp; Coordination Tools</div>", unsafe_allow_html=True)

# Buttons
st.markdown("<div class='btn-blue'>", unsafe_allow_html=True)
if st.button("Open Protection Coordination Tool (TCC Plot)", use_container_width=True):
    go("pages/2_GUI_Final5_TCC.py")
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='btn-blue2'>", unsafe_allow_html=True)
if st.button("Open OC / EF Grid Coordination Tool", use_container_width=True):
    go("pages/3_OC_EF_GOD.py")
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='btn-purple'>", unsafe_allow_html=True)
if st.button("Open Protection Theory Guide", use_container_width=True):
    go("pages/4_Theory.py")
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='btn-purple2'>", unsafe_allow_html=True)
if st.button("Open Working Methodology / Manual", use_container_width=True):
    go("pages/5_Working.py")
st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown(
    """
<div class='footer'>
Protection and Automation Division, GOD<br/>
Nepal Electricity Authority
</div>
""",
    unsafe_allow_html=True
)

st.markdown("</div>", unsafe_allow_html=True)
