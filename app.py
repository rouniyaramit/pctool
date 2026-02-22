import streamlit as st
import pandas as pd
import math
import csv
from io import BytesIO, StringIO

# Try to import FPDF for PDF generation
try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

# --- Page Configuration & Styling ---
st.set_page_config(page_title="NEA Grid Protection Coordination Tool", layout="wide")

# Applying styles similar to the original setup_styles [cite: 2]
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    .footer { position: fixed; bottom: 0; width: 100%; color: #555555; font-style: italic; text-align: center; padding: 10px; }
    .stButton>button { width: 100%; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- State Management (Replacing Tkinter Vars) ---
if 'feeder_data' not in st.session_state:
    st.session_state.feeder_data = [{"load": 0.0, "ct": 0.0} for _ in range(3)]
if 'sys_vars' not in st.session_state:
    st.session_state.sys_vars = {"mva": 0.0, "hv": 0.0, "lv": 0.0, "z": 0.0, "cti": 0.0, "q4": 0.0, "q5": 0.0}

# --- File Menu Logic (Sidebar)  ---
with st.sidebar:
    st.header("📁 File Menu")
    
    # Preload Default Data [cite: 41, 42, 43]
    if st.button("Preload Default Data"):
        st.session_state.sys_vars = {"mva": 16.6, "hv": 33.0, "lv": 11.0, "z": 10.0, "cti": 150.0, "q4": 900.0, "q5": 300.0}
        st.session_state.feeder_data = [
            {"load": 200.0, "ct": 400.0},
            {"load": 250.0, "ct": 400.0},
            {"load": 300.0, "ct": 400.0}
        ]
        st.rerun()

    # Reset [cite: 44, 45]
    if st.button("Reset"):
        st.session_state.sys_vars = {k: 0.0 for k in st.session_state.sys_vars}
        st.session_state.feeder_data = []
        st.rerun()

# --- Main UI Layout ---
st.title("Nepal Electricity Authority (NEA) Grid Protection Coordination Tool") [cite: 1]

# Transformer & System Data (Inputs) [cite: 7, 8]
st.subheader("Transformer & System Data (Inputs)")
c1, c2, c3, c4 = st.columns(4)
with c1:
    mva = st.number_input("MVA", value=float(st.session_state.sys_vars["mva"]))
    hv = st.number_input("HV (kV)", value=float(st.session_state.sys_vars["hv"]))
with c2:
    lv = st.number_input("LV (kV)", value=float(st.session_state.sys_vars["lv"]))
    z = st.number_input("Z%", value=float(st.session_state.sys_vars["z"]))
with c3:
    cti = st.number_input("CTI (ms)", value=float(st.session_state.sys_vars["cti"]))
    q4 = st.number_input("Q4 CT", value=float(st.session_state.sys_vars["q4"]))
with c4:
    q5 = st.number_input("Q5 CT", value=float(st.session_state.sys_vars["q5"]))

# Update session state with current inputs
st.session_state.sys_vars.update({"mva": mva, "hv": hv, "lv": lv, "z": z, "cti": cti, "q4": q4, "q5": q5})

# Feeder Configuration [cite: 9, 10]
st.subheader("Feeder Configuration")
num_feeders = st.number_input("No. of Feeders:", min_value=0, value=len(st.session_state.feeder_data))

# Adjust feeder rows dynamically [cite: 13]
if num_feeders != len(st.session_state.feeder_data):
    st.session_state.feeder_data = [{"load": 0.0, "ct": 0.0} for _ in range(num_feeders)]

current_feeder_data = []
total_load = 0.0

for i in range(num_feeders):
    col1, col2 = st.columns(2)
    with col1:
        l_val = st.number_input(f"Q{i+1} Load (A):", value=st.session_state.feeder_data[i]["load"], key=f"l_{i}")
    with col2:
        c_val = st.number_input(f"Q{i+1} CT Ratio:", value=st.session_state.feeder_data[i]["ct"], key=f"c_{i}")
    
    # Logic for CT Alert coloring [cite: 21, 22]
    if c_val < l_val and c_val > 0:
        st.warning(f"ALERT: Feeder Q{i+1} CT ({c_val}A) is less than Load ({l_val}A)")
    
    current_feeder_data.append({"load": l_val, "ct": c_val})
    total_load += l_val

st.markdown(f"**Total Connected Load: {round(total_load, 2)} A**") [cite: 16]

# --- Calculation Logic [cite: 17, 18, 19] ---
if st.button("RUN CALCULATION"):
    if cti < 120:
        st.error("CTI Error: CTI must be greater than or equal to 120ms.")
    else:
        # Core Calculations
        cti_s = cti / 1000
        flc_lv = round((mva * 1000) / (math.sqrt(3) * lv), 2)
        flc_hv = round((mva * 1000) / (math.sqrt(3) * hv), 2)
        isc_lv = round(flc_lv / (z / 100), 2)
        if_lv = round(isc_lv * 0.9, 2)
        if_hv = round(if_lv / (hv / lv), 2)

        # Reports Storage
        oc_lines = []
        ef_lines = []

        # Critical Overload Check [cite: 34]
        if total_load > flc_lv:
            st.error(f"CRITICAL ALERT: TRANSFORMER OVERLOAD ({total_load}A > {flc_lv}A)")

        max_t_oc, max_t_ef = 0.0, 0.0
        f_oc_txt, f_ef_txt = "", ""

        # Feeder Processing [cite: 23, 24, 25, 26]
        for i, f in enumerate(current_feeder_data):
            l, ct = f['load'], f['ct']
            if ct == 0: continue
            
            # OC
            p_oc = round(1.1 * l, 2)
            r1 = round(p_oc/ct, 2)
            t_oc = round(0.025 * (0.14 / (math.pow(max(1.05, if_lv/p_oc), 0.02) - 1)), 3)
            max_t_oc = max(max_t_oc, t_oc)
            p2 = round(3*l, 2); r2 = round(p2/ct, 2)
            f_oc_txt += f"FEEDER Q{i+1}: Load={l}A, CT={ct}\n - S1 (IDMT): Pickup={p_oc}A ({r1}*In), TMS=0.025, Time={t_oc}s\n - S2 (DT):   Pickup={p2}A ({r2}*In), Time=0.0s\n\n"

            # EF
            p_ef = round(0.15 * l, 2); r_ef1 = round(p_ef/ct, 2)
            t_ef = round(0.025 * (0.14 / (math.pow(max(1.05, if_lv/p_ef), 0.02) - 1)), 3)
            max_t_ef = max(max_t_ef, t_ef)
            p_ef2 = round(1.0*l, 2); r_ef2 = round(p_ef2/ct, 2)
            f_ef_txt += f"FEEDER Q{i+1}: Load={l}A, CT={ct}\n - S1 (IDMT): Pickup={p_ef}A ({r_ef1}*In), TMS=0.025, Time={t_ef}s\n - S2 (DT):   Pickup={p_ef2}A ({r_ef2}*In), Time=0.0s\n\n"

        # Incomer/HV coordination [cite: 29, 30, 31, 32, 33]
        hv_load = total_load / (hv / lv)
        coord_data = [
            ("INCOMER Q4 (LV)", q4, if_lv, 1, round(0.9*isc_lv,2), cti, max_t_oc, max_t_ef),
            ("HV SIDE Q5 (HV)", q5, if_hv, hv/lv, round(if_hv,2), cti*2, max_t_oc+cti_s, max_t_ef+cti_s)
        ]

        i_oc, i_ef = "", ""
        for name, ct_v, fault, scale, s3, dt_ms, t_prev_oc, t_prev_ef in coord_data:
            l_cur = total_load / scale
            t_req_oc, t_req_ef = round(t_prev_oc + cti_s, 3), round(t_prev_ef + cti_s, 3)
            p_oc = round(1.1 * l_cur, 2); r1 = round(p_oc/ct_v, 2)
            tms_oc = round(t_req_oc / (0.14 / (math.pow(max(1.05, fault/p_oc), 0.02) - 1)), 3)
            p2 = round(3*l_cur, 2); r2 = round(p2/ct_v, 2); r3 = round(s3/ct_v, 2)
            i_oc += f"{name}: Load={round(l_cur,2)}A, CT={ct_v}\n - S1 (IDMT): Pickup={p_oc}A ({r1}*In), TMS={tms_oc}, Time={t_req_oc}s\n - S2 (DT):   Pickup={p2}A ({r2}*In), Time={dt_ms/1000}s\n - S3 (DT):   Pickup={s3}A ({r3}*In), Time=0.0s\n\n"

            p_ef = round(0.15 * l_cur, 2); r_ef1 = round(p_ef/ct_v, 2)
            tms_ef = round(t_req_ef / (0.14 / (math.pow(max(1.05, fault/p_ef), 0.02) - 1)), 3)
            p_ef2 = round(1.0*l_cur, 2); r_ef2 = round(p_ef2/ct_v, 2); r_ef3 = round(s3/ct_v, 2)
            i_ef += f"{name}: Load={round(l_cur,2)}A, CT={ct_v}\n - S1 (IDMT): Pickup={p_ef}A ({r_ef1}*In), TMS={tms_ef}, Time={t_req_ef}s\n - S2 (DT):   Pickup={p_ef2}A ({r_ef2}*In), Time={dt_ms/1000}s\n - S3 (DT):   Pickup={s3}A ({r_ef3}*In), Time=0.0s\n\n"

        head = f"FLC LV: {flc_lv}A | FLC HV: {flc_hv}A | Short Circuit: {isc_lv}A\n" + "="*60 + "\n"
        
        # Display Results in Tabs [cite: 11, 12]
        tab_oc, tab_ef = st.tabs([" Overcurrent (Phase) ", " Earth Fault (Neutral) "])
        with tab_oc:
            st.code(head + f_oc_txt + i_oc)
        with tab_ef:
            st.code(head + f_ef_txt + i_ef)

# Footer [cite: 12]
st.markdown('<div class="footer">By Protection and Automation Division, GOD</div>', unsafe_allow_html=True)
