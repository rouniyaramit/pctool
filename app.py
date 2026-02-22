import streamlit as st
import pandas as pd
import math
import csv
from io import BytesIO, StringIO

# Import FPDF for PDF generation [cite: 46]
try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

# --- Page Setup ---
st.set_page_config(page_title="NEA Grid Protection Coordination Tool", layout="wide")

# --- Initialize Session State to prevent NameErrors  ---
if 'sys_vars' not in st.session_state:
    st.session_state.sys_vars = {"mva": 16.6, "hv": 33.0, "lv": 11.0, "z": 10.0, "cti": 150.0, "q4": 900.0, "q5": 300.0}
if 'feeder_data' not in st.session_state:
    st.session_state.feeder_data = [{"l": 200.0, "c": 400.0}, {"l": 250.0, "c": 400.0}, {"l": 300.0, "c": 400.0}]
if 'oc_report' not in st.session_state:
    st.session_state.oc_report = ""
if 'ef_report' not in st.session_state:
    st.session_state.ef_report = ""

# --- Sidebar "File Menu"  ---
with st.sidebar:
    st.title("📁 File Menu")
    
    if st.button("Preload Default Data"):
        st.session_state.sys_vars = {"mva": 16.6, "hv": 33.0, "lv": 11.0, "z": 10.0, "cti": 150.0, "q4": 900.0, "q5": 300.0}
        st.session_state.feeder_data = [{"l": 200.0, "c": 400.0}, {"l": 250.0, "c": 400.0}, {"l": 300.0, "c": 400.0}]
        st.rerun()

    if st.button("Reset"):
        st.session_state.sys_vars = {k: 0.0 for k in st.session_state.sys_vars}
        st.session_state.feeder_data = []
        st.session_state.oc_report = ""
        st.session_state.ef_report = ""
        st.rerun()

    st.divider()
    
    # Download Buttons (Only active if calculation has run)
    if st.session_state.oc_report:
        # CSV Export [cite: 36]
        csv_data = f"Overcurrent Report\n{st.session_state.oc_report}\n\nEarth Fault Report\n{st.session_state.ef_report}"
        st.download_button("Save Tabulated CSV", data=csv_data, file_name="NEA_Coordination.csv", mime="text/csv")
        
        # PDF Export [cite: 46, 47]
        if FPDF:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Courier", size=10)
            for line in csv_data.split('\n'):
                pdf.cell(200, 7, txt=line, ln=True)
            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            st.download_button("Save PDF", data=pdf_bytes, file_name="NEA_Coordination.pdf", mime="application/pdf")

# --- Main GUI [cite: 8, 9] ---
st.title("Nepal Electricity Authority (NEA) Grid Protection Coordination Tool")

# Transformer & System Data Section [cite: 7, 8]
st.header("Transformer & System Data (Inputs)")
c1, c2, c3 = st.columns(3)
with c1:
    mva = st.number_input("MVA", value=float(st.session_state.sys_vars["mva"]))
    hv = st.number_input("HV (kV)", value=float(st.session_state.sys_vars["hv"]))
with c2:
    lv = st.number_input("LV (kV)", value=float(st.session_state.sys_vars["lv"]))
    z = st.number_input("Z%", value=float(st.session_state.sys_vars["z"]))
with c3:
    cti = st.number_input("CTI (ms)", value=float(st.session_state.sys_vars["cti"]))
    q4_ct = st.number_input("Q4 CT", value=float(st.session_state.sys_vars["q4"]))
    q5_ct = st.number_input("Q5 CT", value=float(st.session_state.sys_vars["q5"]))

# Feeder Configuration Section [cite: 10, 14]
st.header("Feeder Configuration")
num_feeders = st.number_input("No. of Feeders:", min_value=0, step=1, value=len(st.session_state.feeder_data))

# Adjust data list if number of feeders changes [cite: 13]
if len(st.session_state.feeder_data) != num_feeders:
    st.session_state.feeder_data = [{"l": 0.0, "c": 0.0} for _ in range(int(num_feeders))]

current_feeders = []
total_load = 0.0

for i in range(int(num_feeders)):
    f1, f2 = st.columns(2)
    with f1:
        l = st.number_input(f"Q{i+1} Load (A):", value=st.session_state.feeder_data[i]["l"], key=f"l{i}")
    with f2:
        c = st.number_input(f"Q{i+1} CT Ratio:", value=st.session_state.feeder_data[i]["c"], key=f"c{i}")
    
    if c < l and c > 0:
        st.warning(f"⚠️ Feeder Q{i+1} CT ({c}A) is less than Load ({l}A)") [cite: 21]
    
    total_load += l
    current_feeders.append({"l": l, "c": c})

st.subheader(f"Total Connected Load: {round(total_load, 2)} A") [cite: 16]

# --- Calculation Logic [cite: 17, 18, 19] ---
if st.button("RUN CALCULATION", type="primary"):
    if cti < 120:
        st.error("CTI Error: CTI must be greater than or equal to 120ms.") [cite: 17]
    else:
        try:
            # Base Calculations [cite: 18, 19]
            cti_s = cti / 1000
            flc_lv = round((mva * 1000) / (math.sqrt(3) * lv), 2)
            flc_hv = round((mva * 1000) / (math.sqrt(3) * hv), 2)
            isc_lv = round(flc_lv / (z / 100), 2)
            if_lv = round(isc_lv * 0.9, 2)
            if_hv = round(if_lv / (hv / lv), 2)

            f_oc, f_ef = "", ""
            max_t_oc, max_t_ef = 0.0, 0.0

            # Process Feeders [cite: 21, 23, 24, 25, 26]
            for i, f in enumerate(current_feeders):
                l_val, ct_val = f['l'], f['c']
                if ct_val == 0: continue
                
                # Overcurrent [cite: 23, 24]
                p_oc = round(1.1 * l_val, 2); r1 = round(p_oc/ct_val, 2)
                t_oc = round(0.025 * (0.14 / (math.pow(max(1.05, if_lv/p_oc), 0.02) - 1)), 3)
                max_t_oc = max(max_t_oc, t_oc)
                p2 = round(3*l_val, 2); r2 = round(p2/ct_val, 2)
                f_oc += f"FEEDER Q{i+1}: Load={l_val}A, CT={ct_val}\n - S1 (IDMT): Pickup={p_oc}A ({r1}*In), TMS=0.025, Time={t_oc}s\n - S2 (DT):   Pickup={p2}A ({r2}*In), Time=0.0s\n\n"
                
                # Earth Fault [cite: 25, 26]
                p_ef = round(0.15 * l_val, 2); r_ef1 = round(p_ef/ct_val, 2)
                t_ef = round(0.025 * (0.14 / (math.pow(max(1.05, if_lv/p_ef), 0.02) - 1)), 3)
                max_t_ef = max(max_t_ef, t_ef)
                p_ef2 = round(1.0*l_val, 2); r_ef2 = round(p_ef2/ct_val, 2)
                f_ef += f"FEEDER Q{i+1}: Load={l_val}A, CT={ct_val}\n - S1 (IDMT): Pickup={p_ef}A ({r_ef1}*In), TMS=0.025, Time={t_ef}s\n - S2 (DT):   Pickup={p_ef2}A ({r_ef2}*In), Time=0.0s\n\n"

            # Coordination (Incomer/HV) [cite: 29, 30, 31, 32, 33]
            hv_load = total_load / (hv / lv)
            coord = [
                ("INCOMER Q4 (LV)", q4_ct, if_lv, 1, round(0.9*isc_lv,2), cti, max_t_oc, max_t_ef),
                ("HV SIDE Q5 (HV)", q5_ct, if_hv, hv/lv, round(if_hv,2), cti*2, max_t_oc+cti_s, max_t_ef+cti_s)
            ]
            
            i_oc, i_ef = "", ""
            for name, ct_v, fault, scale, s3, dt_ms, t_prev_oc, t_prev_ef in coord:
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

            header = f"FLC LV: {flc_lv}A | FLC HV: {flc_hv}A | Short Circuit: {isc_lv}A\n" + "="*60 + "\n"
            st.session_state.oc_report = header + f_oc + i_oc
            st.session_state.ef_report = header + f_ef + i_ef
            
            # Critical Overload Check [cite: 34]
            if total_load > flc_lv:
                st.error(f"🚨 CRITICAL: TRANSFORMER OVERLOAD ({total_load}A > {flc_lv}A)")
            
        except Exception as e:
            st.error(f"Error in calculations: {e}")

# --- Output Display [cite: 11, 12] ---
if st.session_state.oc_report:
    t1, t2 = st.tabs([" Overcurrent (Phase) ", " Earth Fault (Neutral) "])
    with t1:
        st.code(st.session_state.oc_report)
    with t2:
        st.code(st.session_state.ef_report)

st.markdown("---")
st.caption("By Protection and Automation Division, GOD")
