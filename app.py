import os
import streamlit as st

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="NEA Protection & Coordination Tools",
    layout="wide",
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "logo.jpg")

# -------------------- FULL DESKTOP CSS --------------------
st.markdown("""
<style>

/* ===== REMOVE ALL STREAMLIT UI ===== */
header {visibility: hidden !important;}
footer {visibility: hidden !important;}
#MainMenu {visibility: hidden !important;}
[data-testid="stToolbar"] {display:none !important;}
[data-testid="stDecoration"] {display:none !important;}
[data-testid="stSidebar"] {display:none !important;}
[data-testid="stStatusWidget"] {display:none !important;}

/* REMOVE TOP WHITE BAR */
[data-testid="stAppViewContainer"] > .main {
    padding-top: 0rem !important;
}

/* FULL SCREEN BACKGROUND */
html, body, [data-testid="stAppViewContainer"] {
    background: #dcdcdc !important;
    overflow: hidden !important;
}

/* REMOVE DEFAULT PADDING */
.block-container {
    padding: 0 !important;
}

/* ===== EXE WINDOW LOOK ===== */
.window {
    width: 980px;
    max-width: 95%;
    margin: 20px auto;
    background: #efefef;
    border: 1px solid #b5b5b5;
    border-radius: 10px;
    padding: 20px;
    box-shadow: 0 12px 26px rgba(0,0,0,0.25);
}

/* TITLE */
.title {
    text-align:center;
    font-size: 34px;
    font-weight: 900;
    margin-top: 10px;
    margin-bottom: 18px;
    color:#1f1f1f;
}

/* BUTTONS */
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
    transition:0.15s;
}
.tkbtn:hover {filter:brightness(1.08);}
.tkbtn:active {transform:translateY(1px);}

/* COLORS */
.blue1{background:#0b74c7;}
.blue2{background:#0a63b5;}
.purp1{background:#4a35c8;}
.purp2{background:#36157d;}

/* FOOTER */
.footer{
    text-align:center;
    margin-top:28px;
    font-style:italic;
    color:#4b4b4b;
    font-size:14px;
}

</style>
""", unsafe_allow_html=True)

# -------------------- PAGE NAVIGATION --------------------
params = st.query_params
page = params.get("page", None)

if page:
    mapping = {
        "tcc": "pages/2_GUI_Final5_TCC.py",
        "ocef": "pages/3_OC_EF_GOD.py",
        "theory": "pages/4_Theory.py",
        "working": "pages/5_Working.py",
    }
    if page in mapping:
        st.switch_page(mapping[page])

# -------------------- MAIN EXE WINDOW --------------------
st.markdown("<div class='window'>", unsafe_allow_html=True)

# CENTER LOGO (Tkinter style)
if os.path.exists(LOGO_PATH):
    col1, col2, col3 = st.columns([3,1,3])
    with col2:
        st.image(LOGO_PATH, width=150)

# TITLE
st.markdown(
    "<div class='title'>NEA Protection &amp; Coordination Tools</div>",
    unsafe_allow_html=True
)

# BUTTONS
st.markdown("""
<a class='tkbtn blue1' href='?page=tcc'>Open Protection Coordination Tool (TCC Plot)</a>
<a class='tkbtn blue2' href='?page=ocef'>Open OC / EF Grid Coordination Tool</a>
<a class='tkbtn purp1' href='?page=theory'>Open Protection Theory Guide</a>
<a class='tkbtn purp2' href='?page=working'>Open Working Methodology / Manual</a>
""", unsafe_allow_html=True)

# FOOTER
st.markdown("""
<div class='footer'>
Protection and Automation Division, GOD<br>
Nepal Electricity Authority
</div>
""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
