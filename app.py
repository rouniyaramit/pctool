import streamlit as st
import pandas as pd
import math
from streamlit_option_menu import option_menu

# --- PDF Library Setup ---
try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

# --- Page Setup ---
st.set_page_config(page_title="NEA Grid Protection Coordination Tool", layout="wide")

# --- 1. SESSION STATE INITIALIZATION ---
# 'reset_ctr' is the secret to the single-click fix.
if 'reset_ctr' not in st.session_state:
    st.session_state.reset_ctr = 0

if 'sys_vars' not in st.session_state:
    st.session_state.sys_vars = {
        "mva": 16.6, "hv": 33.0, "lv": 11.0, "z": 10.0, "cti": 150.0, "q4": 900.0, "q5": 300.0
    }
if 'feeder_data' not in st.session_state:
    st.session_state.feeder_data = [{"l": 200.0, "c": 400.0}, {"l": 250.0, "c": 400.0}, {"l": 300.0, "c": 400.0}]
if 'oc_report' not in st.session_state:
    st.session_state.oc_report = ""
if 'ef_report' not in st.session_state:
    st.session_state.ef_report = ""

# --- 2. NAVIGATION & RESET LOGIC ---
selected_menu = option_menu(
    menu_title=None, 
    options=["Home", "Preload Default Data", "Save Tabulated CSV", "Save PDF", "Reset"],
    icons=["house", "cloud-download", "file-earmark-spreadsheet", "file-pdf", "arrow-counterclockwise"],
    menu_icon="cast", 
    default_index=0,
    orientation="horizontal",
)

# SINGLE-CLICK LOGIC:
# We increment 'reset_ctr' which changes the 'key' of every widget below.
# This forces Streamlit to render "New" empty boxes instead of keeping old typed values.
if selected_menu == "Preload Default Data":
    st.session_state.sys_vars = {"mva": 16.6, "hv": 33.0, "lv": 11.0, "z": 10.0, "cti": 150.0, "q4": 900.0, "q5": 300.0}
    st.session_state.feeder_data = [{"l": 200.0, "c": 400.0}, {"l": 250.0, "c": 400.0}, {"l": 300.0, "c": 400.0}]
    st.session_state.reset_ctr += 1 
    st.rerun()

if selected_menu == "Reset":
    st.session_state.sys_vars = {k: 0.0 for k in st.session_state.sys_vars}
    st.session_state.feeder_data = []
    st.session_state.oc_report = ""
    st.session_state.ef_report = ""
    st.session_state.reset_ctr += 1
    st.rerun()

# --- 3. MAIN UI ---
st.title("Nepal Electricity Authority (NEA) Grid Protection Coordination Tool")

# --- Transformer & System Data ---
st.subheader("Transformer & System Data (Inputs)")
c1, c2, c3, c4 = st.columns(4)

# Note the key="{key}_{reset_ctr}". When reset_ctr changes, the key changes, forcing a UI update.
with c1:
    mva = st.number_input("MVA", value=float(st.session_state.sys_vars["mva"]), key=f"mva_{st.session_state.reset_ctr}")
    hv = st.number_input("HV (kV)", value=float(st.session_state.sys_vars["hv"]), key=f"hv_{st.session_state.reset_ctr}")
with c2:
    lv = st.number_input("LV (kV)", value=float(st.session_state.sys_vars["lv"]), key=f"lv_{st.session_state.reset_ctr}")
    z = st.number_input("Z%", value=float(st.session_state.sys_vars["z"]), key=f"z_{st.session_state.reset_ctr}")
with c3:
    cti = st.number_input("CTI (ms)", value=float(st.session_state.sys_vars["cti"]), key=f"cti_{st.session_state.reset_ctr}")
    q4_ct = st.number_input("Q4 CT Ratio", value=float(st.session_state.sys_vars["q4"]), key=f"q4_{st.session_state.reset_ctr}")
with c4:
    q5_ct = st.number_input("Q5 CT Ratio", value=float(st.session_state.sys_vars["q5"]), key=f"q5_{st.session_state.reset_ctr}")

# --- Feeder Configuration ---
st.subheader("Feeder Configuration")
num_feeders = st.number_input("No. of Feeders:", min_value=0, step=1, 
                              value=len(st.session_state.feeder_data), 
                              key=f"num_f_{st.session_state.reset_ctr}")

# Sync feeder list size
if len(st.session_state.feeder_data) != num_feeders:
    st.session_state.feeder_data = [{"l": 0.0, "c": 0.0} for _ in range(int(num_feeders))]

current_feeders = []
total_load = 0.0

for i in range(int(num_feeders)):
    f1, f2 = st.columns(2)
    with f1:
        l_val = st.number_input(f"Q{i+1} Load (A):", value=float(st.session_state.feeder_data[i]["l"]), key=f"l{i}_{st.session_state.reset_ctr}")
    with f2:
        c_val = st.number_input(f"Q{i+1} CT Ratio:", value=float(st.session_state.feeder_data[i]["c"]), key=f"c{i}_{st.session_state.reset_ctr}")
    
    total_load += l_val
    current_feeders.append({"l": l_val, "c": c_val})

st.markdown(f"**Total Connected Load: {round(total_load, 2)} A**")

# --- 4. CALCULATIONS ---
if st.button("RUN CALCULATION", type="primary"):
    if hv == 0 or lv == 0 or z == 0 or mva == 0:
        st.error("Inputs cannot be zero for calculation.")
    else:
        try:
            cti_s = cti / 1000
            flc_lv = round((mva * 1000) / (math.sqrt(3) * lv), 2)
            flc_hv = round((mva * 1000) / (math.sqrt(3) * hv), 2)
            isc_lv = round(flc_lv / (z / 100), 2)
            if_lv = round(isc_lv * 0.9, 2)
            if_hv = round(if_lv / (hv / lv), 2)

            f_oc, f_ef = "", ""
            max_t_oc, max_t_ef = 0.0, 0.0

            # Feeder Calcs
            for i, f in enumerate(current_feeders):
                l_v, ct_v = f['l'], f['c']
                if ct_v == 0: continue
                p_oc = round(1.1 * l_v, 2)
                t_oc = round(0.025 * (0.14 / (math.pow(max(1.05, if_lv/p_oc), 0.02) - 1)), 3)
                max_t_oc = max(max_t_oc, t_oc)
                f_oc += f"FEEDER Q{i+1}: Load={l_v}A, CT={ct_v} | S1 (IDMT): Pickup={p_oc}A, TMS=0.025, Time={t_oc}s\n"
                
                p_ef = round(0.15 * l_v, 2)
                t_ef = round(0.025 * (0.14 / (math.pow(max(1.05, if_lv/p_ef), 0.02) - 1)), 3)
                max_t_ef = max(max_t_ef, t_ef)
                f_ef += f"FEEDER Q{i+1}: Load={l_v}A, CT={ct_v} | S1 (IDMT): Pickup={p_ef}A, TMS=0.025, Time={t_ef}s\n"

            # Results
            header = f"FLC LV: {flc_lv}A | Short Circuit: {isc_lv}A\n" + "="*50 + "\n"
            st.session_state.oc_report = header + f_oc
            st.session_state.ef_report = header + f_ef
            st.rerun() # Refresh to show tabs
        except Exception as e:
            st.error(f"Error: {e}")

# --- 5. OUTPUT DISPLAY ---
if st.session_state.oc_report:
    tab1, tab2 = st.tabs([" Overcurrent ", " Earth Fault "])
    with tab1: st.code(st.session_state.oc_report)
    with tab2: st.code(st.session_state.ef_report)

# --- 6. EXPORTS ---
if selected_menu == "Save PDF" and st.session_state.oc_report:
    st.info("Generating PDF...") # Placeholder for FPDF logic
