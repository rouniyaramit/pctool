import streamlit as st
from tcc_tool import run_tcc_tool
from oc_ef_tool import run_oc_ef_tool

st.set_page_config(page_title="NEA Protection Tools", layout="wide")

col1, col2 = st.columns([4,1])

with col1:
    st.title("NEA Protection & Coordination Tools")
    st.markdown("### Protection and Automation Division, GOD")

with col2:
    try:
        st.image("logo.jpg", width=180)
    except:
        pass

st.markdown("---")

tool = st.sidebar.radio(
    "Select Tool",
    ["Master Dashboard",
     "Protection Coordination Tool (TCC)",
     "OC / EF Grid Coordination Tool"]
)

if tool == "Master Dashboard":
    st.subheader("Welcome to NEA Protection Web Suite")
    st.info("Select a tool from the sidebar to begin.")
    st.image("sld.png", width=400)

elif tool == "Protection Coordination Tool (TCC)":
    run_tcc_tool()

elif tool == "OC / EF Grid Coordination Tool":
    run_oc_ef_tool()
