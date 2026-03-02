import streamlit as st
from PIL import Image
from pathlib import Path

st.set_page_config(page_title="NEA Master Protection Tool", layout="wide")

logo_path = Path(__file__).parent / "logo.jpg"

c1, c2 = st.columns([1, 4], vertical_alignment="center")
with c1:
    if logo_path.exists():
        st.image(Image.open(logo_path), use_container_width=True)
with c2:
    st.title("NEA Master Protection Tool")
    st.caption("Web version (Master Launcher → Tools as pages)")

st.divider()

st.subheader("Open a tool")

colA, colB = st.columns(2)
with colA:
    if st.button("TCC Plot Tool (Q1–Q5)", use_container_width=True):
        st.switch_page("pages/2_GUI_Final5_TCC.py")
    if st.button("Theory", use_container_width=True):
        st.switch_page("pages/4_Theory.py")

with colB:
    if st.button("OC/EF Grid Tool", use_container_width=True):
        st.switch_page("pages/3_OC_EF_GOD.py")
    if st.button("Working", use_container_width=True):
        st.switch_page("pages/5_Working.py")

st.info("On the web, tools open as pages (instead of Tkinter pop-up windows).")
