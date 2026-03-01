import os
import streamlit as st

st.set_page_config(page_title="NEA Protection & Coordination Tools", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Prefer logo.jpg, fallback to logo.png
LOGO_JPG = os.path.join(BASE_DIR, "logo.jpg")
LOGO_PNG = os.path.join(BASE_DIR, "logo.png")
LOGO_PATH = LOGO_JPG if os.path.exists(LOGO_JPG) else LOGO_PNG

# -------------------- HARDENED CSS (kills the top bar) --------------------
st.markdown("""
<style>
/* ===== Hide all Streamlit chrome (multiple versions) ===== */
#MainMenu {display:none !important;}
footer {display:none !important;}

/* Header + toolbars + decorations */
header, header[data-testid="stHeader"] {display:none !important;}
[data-testid="stToolbar"] {display:none !important;}
[data-testid="stDecoration"] {display:none !important;}
[data-testid="stAppToolbar"] {display:none !important;}
[data-testid="stTopNav"] {display:none !important;}
[data-testid="stStatusWidget"] {display:none !important;}
[data-testid="stSidebar"] {display:none !important;}

/* Sometimes the bar is created by these wrappers */
div[data-testid="stVerticalBlockBorderWrapper"] {border:0 !important; padding:0 !important; margin:0 !important;}
div[data-testid="stVerticalBlock"] {gap: 0.0rem !important;}

/* Remove padding that can look like a bar */
.block-container {padding:0 !important; margin:0 !important;}
[data-testid="stAppViewContainer"] > .main {padding:0 !important; margin:0 !important;}
[data-testid="stAppViewContainer"] {padding:0 !important; margin:0 !important;}

/* Kill any top “spacer” elements */
div.st-emotion-cache-1kyxreq, 
div.st-emotion-cache-1avcm0n,
div.st-emotion-cache-18ni7ap,
div.st-emotion-cache-z5fcl4 {
    display:none !important;
}

/* Full-screen gray background + no scroll */
html, body, [data-testid="stAppViewContainer"] {
    background: #dcdcdc !important;
    overflow: hidden !important;
}

/* ===== EXE window panel ===== */
.window {
    width: 980px;
    max-width: 95%;
    margin: 18px auto;
    background: #efefef;
    border: 1px solid #b5b5b5;
    border-radius: 10px;
    padding: 20px 22px 20px 22px;
    box-shadow: 0 12px 26px rgba(0,0,0,0.25);
}

/* Title */
.title {
    text-align:center;
    font-size: 34px;
    font-weight: 900;
    margin-top: 10px;
    margin-bottom: 18px;
    color:#1f1f1f;
}

/* Buttons */
.tkbtn {
    display:block;
    width: 660px;
    max-width: 94%;
    margin: 14px auto;
    padding: 18px;
    font-size: 18px;
    font-weight: 900;
    color:white !important;
    text-decoration:none !important;
    text-align:center;
    border-radius:6px;
    border:1px solid rgba(0,0,0,0.2);
    box-shadow:0 3px 0 rgba(0,0,0,0.2);
    transition: filter 0.12s ease, transform 0.05s ease;
}
.tkbtn:hover {filter:brightness(1.08);}
.tkbtn:active {transform: translateY(1px);}

/* Colors */
.blue1{background:#0b74c7;}
.blue2{background:#0a63b5;}
.purp1{background:#4a35c8;}
.purp2{background:#36157d;}

/* Footer */
.footer{
    text-align:center;
    margin-top:28px;
    font-style:italic;
    color:#4b4b4b;
    font-size:14px;
    line-height:1.5;
}
</style>
""", unsafe_allow_html=True)

# -------------------- Navigation via query param --------------------
page = st.query_params.get("page", None)

if page:
    mapping = {
        "tcc": "pages/2_GUI_Final5_TCC.py",
        "ocef": "pages/3_OC_EF_GOD.py",
        "theory": "pages/4_Theory.py",
        "working": "pages/5_Working.py",
    }
    target = mapping.get(page)
    if target:
        st.switch_page(target)

# -------------------- UI --------------------
st.markdown("<div class='window'>", unsafe_allow_html=True)

# Center logo
if os.path.exists(LOGO_PATH):
    c1, c2, c3 = st.columns([3, 1, 3])
    with c2:
        st.image(LOGO_PATH, width=150)

# Title
st.markdown("<div class='title'>NEA Protection &amp; Coordination Tools</div>", unsafe_allow_html=True)

# Buttons
st.markdown("""
<a class='tkbtn blue1' href='?page=tcc'>Open Protection Coordination Tool (TCC Plot)</a>
<a class='tkbtn blue2' href='?page=ocef'>Open OC / EF Grid Coordination Tool</a>
<a class='tkbtn purp1' href='?page=theory'>Open Protection Theory Guide</a>
<a class='tkbtn purp2' href='?page=working'>Open Working Methodology / Manual</a>
""", unsafe_allow_html=True)

# Footer
st.markdown("""
<div class='footer'>
Protection and Automation Division, GOD<br/>
Nepal Electricity Authority
</div>
""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
