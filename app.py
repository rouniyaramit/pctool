import streamlit as st

st.set_page_config(page_title="NEA Protection Suite", layout="wide")

# -------- Tkinter Clone Global CSS --------
st.markdown("""
<style>
/* Hide Streamlit sidebar completely */
[data-testid="stSidebar"] {display: none !important;}
/* Reduce big paddings */
.block-container {padding-top: 6px !important; padding-bottom: 8px !important; padding-left: 14px !important; padding-right: 14px !important;}
/* Make buttons feel like Tkinter */
div.stButton > button {
    height: 36px !important;
    padding: 0px 14px !important;
    font-weight: 800 !important;
    border-radius: 6px !important;
}
/* Compact inputs like Tkinter */
label {font-size: 13px !important; font-weight: 600 !important;}
input, textarea {font-size: 14px !important;}
/* Remove extra whitespace between widgets */
[data-testid="stVerticalBlock"] {gap: 0.45rem !important;}
</style>
""", unsafe_allow_html=True)

# -------- Tkinter-like top menu bar --------
menu = st.columns([1.2, 1.1, 1.1, 0.9, 0.9, 3.8], gap="small")

with menu[0]:
    if st.button("MASTER", use_container_width=True):
        st.switch_page("pages/1_MASTER_LAUNCHER.py")
with menu[1]:
    if st.button("TCC TOOL", use_container_width=True):
        st.switch_page("pages/2_GUI_Final5_TCC.py")
with menu[2]:
    if st.button("OC/EF TOOL", use_container_width=True):
        st.switch_page("pages/3_OC_EF_GOD.py")
with menu[3]:
    if st.button("THEORY", use_container_width=True):
        st.switch_page("pages/4_Theory.py")
with menu[4]:
    if st.button("WORKING", use_container_width=True):
        st.switch_page("pages/5_Working.py")

st.markdown("<hr style='margin:6px 0 10px 0;'>", unsafe_allow_html=True)

st.title("NEA Protection Suite (Tkinter Clone UI)")
st.caption("Use the top menu buttons (like Tkinter menu bar).")
