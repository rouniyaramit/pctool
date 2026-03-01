import os
import streamlit as st

st.set_page_config(page_title="NEA Protection & Coordination Tools", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "logo.png")

# -------------------- CSS: Desktop App Look --------------------
st.markdown("""
<style>
/* Hide sidebar + remove default Streamlit header spacing */
[data-testid="stSidebar"] {display:none !important;}
header[data-testid="stHeader"] {display:none !important;}
/* Reduce top blank area */
.block-container {
    padding: 0rem !important;
}

/* Full background like Tkinter */
html, body, [data-testid="stAppViewContainer"] {
    background: #dcdcdc !important;
}

/* Center panel = Tkinter window feel */
.window {
    width: 980px;
    max-width: 94%;
    margin: 18px auto;
    background: #efefef;
    border: 1px solid #bdbdbd;
    border-radius: 10px;
    padding: 18px 22px 20px 22px;
    box-shadow: 0px 10px 24px rgba(0,0,0,0.18);
}

/* Top bar line (subtle) */
.topbar {
    height: 10px;
    background: linear-gradient(180deg, #f8f8f8, #e6e6e6);
    border-radius: 8px;
    margin-bottom: 10px;
}

/* Logo centered */
.logo-wrap {
    display:flex;
    justify-content:center;
    margin-top: 4px;
}
.logo-wrap img {
    image-rendering: -webkit-optimize-contrast;
    image-rendering: crisp-edges;
}

/* Title centered */
.title {
    text-align:center;
    font-size: 34px;
    font-weight: 900;
    margin-top: 8px;
    margin-bottom: 18px;
    color: #1f1f1f;
    letter-spacing: 0.3px;
}

/* Button styles: strong contrast like Tkinter */
.tkbtn {
    display:block;
    width: 660px;
    max-width: 94%;
    margin: 14px auto;
    padding: 18px 14px;
    font-size: 18px;
    font-weight: 900;
    color: #ffffff !important;
    text-decoration: none !important;
    border-radius: 6px;
    text-align:center;
    border: 1px solid rgba(0,0,0,0.20);
    box-shadow: 0px 3px 0px rgba(0,0,0,0.18);
    transition: transform 0.06s ease, filter 0.15s ease;
}
.tkbtn:hover {
    filter: brightness(1.08);
}
.tkbtn:active {
    transform: translateY(1px);
    box-shadow: 0px 2px 0px rgba(0,0,0,0.18);
}

/* Colors (closer to Tkinter solid colors) */
.blue1 { background:#0b74c7; }
.blue2 { background:#0a63b5; }
.purp1 { background:#4a35c8; }
.purp2 { background:#36157d; }

/* Footer like Tkinter */
.footer {
    text-align:center;
    margin-top: 30px;
    font-style: italic;
    color: #4b4b4b;
    font-size: 14px;
    line-height: 1.5;
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
st.markdown("<div class='topbar'></div>", unsafe_allow_html=True)

# Logo
if os.path.exists(LOGO_PATH):
    st.markdown("<div class='logo-wrap'>", unsafe_allow_html=True)
    st.image(LOGO_PATH, width=150)
    st.markdown("</div>", unsafe_allow_html=True)

# Title
st.markdown("<div class='title'>NEA Protection &amp; Coordination Tools</div>", unsafe_allow_html=True)

# Buttons (HTML, stable)
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
