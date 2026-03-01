import os
import streamlit as st

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_PATH = os.path.join(BASE_DIR, "logo.jpg")

st.set_page_config(page_title="NEA Protection Master Launcher", layout="wide")

# ----- CSS to mimic Tkinter look -----
st.markdown(
    """
    <style>
      .block-container {padding-top: 20px;}
      .nea-title {text-align:center; font-size:32px; font-weight:800; color:#333;}
      .nea-bg {background:#f2f2f2; padding:18px; border-radius:10px;}
      div.stButton > button {
          width: 100%;
          height: 50px;
          font-size: 16px;
          font-weight: 800;
          border-radius: 6px;
          border: 0px;
      }
      .footer {text-align:center; color:#555; font-style:italic; font-size:16px; padding-top:20px;}
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="nea-bg">', unsafe_allow_html=True)

# Logo centered (Tkinter: top center)
if os.path.exists(LOGO_PATH):
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.image(LOGO_PATH, width=150)

st.markdown('<div class="nea-title">NEA Protection & Coordination Tools</div>', unsafe_allow_html=True)
st.write("")

# Buttons with same text + colors as Tkinter
def colored_button(label: str, color: str, key: str):
    st.markdown(
        f"""
        <style>
        div.stButton > button#{key} {{
            background:{color};
            color:white;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
    return st.button(label, key=key)

# Streamlit navigation helper
def switch_page_safe(page_name: str):
    # Works on newer streamlit. If not available, user can click sidebar.
    try:
        st.switch_page(page_name)
    except Exception:
        st.warning("Sidebar navigation is available (your Streamlit version may not support switch_page).")

# Buttons (same labels)
if colored_button("Open Protection Coordination Tool (TCC Plot)", "#007acc", "btn_tcc"):
    switch_page_safe("pages/2_GUI_Final5_TCC.py")

if colored_button("Open OC / EF Grid Coordination Tool", "#0056b3", "btn_grid"):
    switch_page_safe("pages/3_OC_EF_GOD.py")

if colored_button("Open Protection Theory Guide", "#4626b8", "btn_theory"):
    switch_page_safe("pages/4_Theory.py")

if colored_button("Open Working Methodology / Manual", "#3c1175", "btn_work"):
    switch_page_safe("pages/5_Working.py")

st.markdown(
    '<div class="footer">Protection and Automation Division, GOD<br/>Nepal Electricity Authority</div>',
    unsafe_allow_html=True
)

st.markdown("</div>", unsafe_allow_html=True)
