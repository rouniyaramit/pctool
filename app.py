import os
import streamlit as st

st.set_page_config(page_title="NEA Protection & Coordination Tools", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "logo.png")

# -------------------- CSS (Tkinter gray background) --------------------
st.markdown("""
<style>
/* Hide sidebar */
[data-testid="stSidebar"] {display:none !important;}

/* Full-page gray background like Tkinter */
html, body, [data-testid="stAppViewContainer"] {
    background: #e6e6e6 !important;
}

/* Remove extra padding */
.block-container {
    padding-top: 0px !important;
    padding-left: 0px !important;
    padding-right: 0px !important;
    padding-bottom: 0px !important;
}

/* Center "window panel" (like a Tkinter window placed on gray bg) */
.window {
    width: 980px;
    max-width: 92%;
    margin: 22px auto;
    background: #f2f2f2;
    border: 1px solid #c8c8c8;
    border-radius: 10px;
    padding: 18px 18px 22px 18px;
    box-shadow: 0px 3px 12px rgba(0,0,0,0.10);
}

/* Logo centered */
.logo img {
    display:block;
    margin-left:auto;
    margin-right:auto;
}

/* Title centered */
.title {
    text-align:center;
    font-size: 34px;
    font-weight: 900;
    margin-top: 10px;
    margin-bottom: 22px;
    color: #222;
}

/* Buttons: same feel as Tkinter big buttons */
.tkbtn {
    display: block;
    width: 620px;
    max-width: 92%;
    margin: 16px auto;
    padding: 18px 14px;
    font-size: 18px;
    font-weight: 900;
    color: white !important;
    text-decoration: none !important;
    border-radius: 6px;
    text-align: center;
}

/* Colors (match your Tkinter) */
.blue1 { background: #0a74c9; }
.blue2 { background: #0a5fb0; }
.purp1 { background: #4a2cc2; }
.purp2 { background: #35127a; }

/* Footer bottom center like Tkinter */
.footer {
    text-align: center;
    margin-top: 42px;
    font-style: italic;
    color: #555;
    font-size: 15px;
    line-height: 1.4;
}
</style>
""", unsafe_allow_html=True)

# -------------------- Navigation using query param --------------------
params = st.query_params
page = params.get("page", None)

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
    else:
        st.query_params.clear()
        st.rerun()

# -------------------- UI --------------------
st.markdown("<div class='window'>", unsafe_allow_html=True)

# Center logo
if os.path.exists(LOGO_PATH):
    st.markdown("<div class='logo'>", unsafe_allow_html=True)
    st.image(LOGO_PATH, width=170)
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.warning("logo.png not found in root folder.")

# Title
st.markdown("<div class='title'>NEA Protection &amp; Coordination Tools</div>", unsafe_allow_html=True)

# HTML buttons (stable styling on Streamlit Cloud)
st.markdown("""
<a class="tkbtn blue1" href="?page=tcc">Open Protection Coordination Tool (TCC Plot)</a>
<a class="tkbtn blue2" href="?page=ocef">Open OC / EF Grid Coordination Tool</a>
<a class="tkbtn purp1" href="?page=theory">Open Protection Theory Guide</a>
<a class="tkbtn purp2" href="?page=working">Open Working Methodology / Manual</a>
""", unsafe_allow_html=True)

# Footer
st.markdown("""
<div class="footer">
Protection and Automation Division, GOD<br/>
Nepal Electricity Authority
</div>
""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
