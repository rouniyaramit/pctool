# MASTER_PROTECTION_TOOL.py

import streamlit as st
from tcc_tool import run_tcc_tool
from oc_ef_tool import run_oc_ef_tool


st.set_page_config(
    page_title="MASTER PROTECTION TOOL",
    layout="wide"
)

# ---------------- Sidebar Navigation ----------------
st.sidebar.title("Navigation")

app_mode = st.sidebar.radio(
    "Select Tool",
    (
        "Master Protection Dashboard",
        "TCC Coordination Tool",
        "OC / EF Coordination Tool"
    )
)

# ---------------- Master Dashboard ----------------
if app_mode == "Master Protection Dashboard":

    st.title("MASTER PROTECTION COORDINATION TOOL")

    st.markdown("---")

    try:
        st.image("logo.jpg", width=200)
    except:
        st.info("Place logo.jpg in same repository folder.")

    st.markdown("""
    ### Available Modules:

    1. **TCC Coordination Tool**
       - IDMT Curves
       - DT1 / DT2 stages
       - Fault level plotting
       - Coordination margin check
       - Trip time calculation

    2. **OC / EF Coordination Tool**
       - Feeder relay calculations
       - Incomer relay back-calculation
       - CT validation
       - Transformer overload check
       - Full OC and EF setting report

    ---
    Developed for Protection Coordination Engineering.
    """)

# ---------------- TCC Tool ----------------
elif app_mode == "TCC Coordination Tool":
    run_tcc_tool()

# ---------------- OC/EF Tool ----------------
elif app_mode == "OC / EF Coordination Tool":
    run_oc_ef_tool()
