import os
import streamlit as st

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_PATH = os.path.join(BASE_DIR, "logo.png")

st.set_page_config(page_title="MASTER LAUNCHER", layout="wide")

st.markdown("""
<style>
[data-testid="stSidebar"] {display:none !important;}
.block-container {padding-top: 6px !important; padding-left: 14px !important; padding-right: 14px !important;}
.tk_frame {
    background: #efefef;
    border: 1px solid #cfcfcf;
    border-radius: 10px;
    padding: 14px;
}
.tk_title {
    text-align:center;
    font-size: 28px;
    font-weight: 900;
}
.tk_sub {
    text-align:center;
    font-size: 14px;
    color: #333;
    margin-top: 3px;
}
.bigbtn button {
    height: 52px !important;
    font-size: 16px !important;
    font-weight: 900 !important;
}
.footer {
    text-align:center;
    font-style: italic;
    color:#444;
    margin-top: 12px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='tk_frame'>", unsafe_allow_html=True)

c1, c2, c3 = st.columns([2, 1, 2])
with c2:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=140)

st.markdown("<div class='tk_title'>NEA Protection & Coordination Tools</div>", unsafe_allow_html=True)
st.markdown("<div class='tk_sub'>Protection and Automation Division, GOD • Nepal Electricity Authority</div>", unsafe_allow_html=True)
st.write("")

def goto(page):
    st.switch_page(page)

st.markdown("<div class='bigbtn'>", unsafe_allow_html=True)
if st.button("Open Protection Coordination Tool (TCC Plot)", use_container_width=True):
    goto("pages/2_GUI_Final5_TCC.py")
if st.button("Open OC / EF Grid Coordination Tool", use_container_width=True):
    goto("pages/3_OC_EF_GOD.py")
if st.button("Open Protection Theory Guide", use_container_width=True):
    goto("pages/4_Theory.py")
if st.button("Open Working Methodology / Manual", use_container_width=True):
    goto("pages/5_Working.py")
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='footer'>Protection and Automation Division, GOD</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)
