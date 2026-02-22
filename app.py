import streamlit as st
import pandas as pd
import math
import csv
from io import BytesIO, StringIO

# Import FPDF for PDF generation with error handling
try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

# --- Page Configuration ---
st.set_page_config(page_title="NEA Grid Protection Coordination Tool", layout="wide")

# --- Custom Styling (Matching Tkinter Look) ---
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    .footer { position: fixed; bottom: 0; width: 100%; color: #555555; font-style: italic; text-align: center; padding: 10px; background-color: white; }
    .stButton>button { font-weight: bold; }
    /* Match the 'Run.TButton' style from original */
    div.stButton > button:first-child {
        background-color: #0056b3;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Session State Initialization ---
# This prevents NameErrors by ensuring variables exist before the UI renders
if 'sys_vars' not in st.session_state:
    st.session_state.sys_vars = {"mva": 0.0, "hv": 0.0, "lv": 0.0, "z": 0.0, "cti": 0.0, "q4": 0.0, "q5": 0.0}
if 'feeder_data' not in st.session_state:
    st.session_state.feeder_data = [{"l": 0.0, "c": 0.0} for _ in range(3)]
if 'oc_report_txt' not in st.session_state:
    st.session_state.oc_report_txt = ""
if 'ef_report_txt' not in st.session_state:
    st.session_state.ef_report_txt = ""

# --- File Menu Logic (Sidebar) ---
with st.sidebar:
    st.header("📁 File Menu")
    
    # Preload Default Data [cite: 41, 42, 43]
    if st.button("Preload Default Data"):
        st.session_state.sys_vars = {"mva": 16.6, "hv": 33.0, "lv": 11.0, "z": 10.0, "cti": 150.0, "q4": 900.0, "q5": 300.0}
        st.session_state.feeder_data = [{"l": 200.0, "c": 400.0}, {"l": 250.0, "c": 400.0}, {"l": 300.0, "c": 400.0}]
        st.rerun()

    # Save Tabulated CSV [cite: 3, 35, 36]
    if st.session_state.oc_report_txt:
        csv_buffer = StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(["EQUIPMENT", "FAULT TYPE", "STAGE", "PICKUP (A)", "RATIO (*In)", "TMS/DELAY", "TIME (s)"])
        # (CSV parsing logic would go here based on generated text)
        st.download_button("Save Tabulated CSV", data=csv_buffer.getvalue(), file_name="NEA_Coordination.csv", mime="text/csv")

    # Save PDF [cite: 3, 46, 47]
    if FPDF and st.session_state.oc_report_txt:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Courier", size=10)
        full_txt = st.session_state.oc_report_txt + "\n" + st.session_state.ef_report_txt
        for line in full_txt.split('\n'):
            pdf.cell(200, 7, txt=line, ln=True)
        pdf_output = pdf.output(dest='S').encode('latin-1')
        st.download_button("Save PDF", data=pdf_output, file_name="NEA_Coordination.pdf", mime="application/pdf")

    # Reset [cite: 3, 44, 45]
    if st.button("Reset"):
        st.session_state.sys_vars = {k: 0.0 for k in st.session_state.sys_vars}
        st.session_state.feeder_data = []
        st.session_state.oc_report_txt = ""
        st.session_state.ef_report_txt = ""
        st.rerun()

# --- Main UI ---
st.title("Nepal Electricity Authority (NEA) Grid Protection Coordination Tool")

# Transformer & System Data (Inputs) [cite: 7, 8, 9]
with st.container():
    st.subheader("Transformer & System Data (Inputs)")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        mva = st.number_input("MVA", value=float(st.session_state.sys_vars["mva"]))
        hv = st.number_input("HV (kV)", value=float(st.session_state.sys_vars["hv"]))
    with col2:
        lv = st.number_input("LV (kV)", value=float(st.session_state.sys_vars["lv"]))
        z_pct = st.number_input("Z%", value=float(st.session_state.sys_vars["z"]))
    with col3:
        cti_ms = st.number_input("CTI (ms)", value=float(st.session_state.sys_vars["cti"]))
        q4_ct = st.number_input("Q4 CT", value=float(st.session_state.sys_vars["q4"]))
    with col4:
        q5_ct = st.number_input("Q5 CT", value=float(st.session_state.sys_vars["q5"]))

# Feeder Configuration [cite: 9, 10, 14, 15]
st.subheader("Feeder Configuration")
num_feeders = st.number_input("No. of Feeders:", min_value=0, value=len(st.session_state.feeder_data))

# Ensure feeder data list matches the number of feeders
if len(st.session_state.feeder_data) != num_feeders:
    st.session_state.feeder_data = [{"l": 0.0, "c": 0.0} for _ in range(num_feeders)]

temp_feeder_list = []
total_load = 0.0
ct_alerts = []

for i in range(num_feeders):
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        l_val = st.number_input(f"Q{i+1} Load (A):", value=st.session_state.feeder_data[i]["l"], key=f"l_{i}")
    with f_col2:
        c_val = st.number_input(f"Q{i+1} CT Ratio:", value=st.session_state.feeder_data[i]["c"], key=f"c_{i}")
    
    if c_val < l_val and c_val > 0:
        ct_alerts.append(f"ALERT: Feeder Q{i+1} CT ({c_val}A) is less than Load ({l_val}A)") [cite: 21]
    
    total_load += l_val
    temp_feeder_list.append({"l": l_val, "c": c_val})

st.markdown(f"**Total Connected Load: {round(total_load, 2)} A**") [cite: 10, 16]

# --- Calculation Engine [cite: 17, 18, 19, 20, 24, 25, 26, 28, 30, 31, 32, 33] ---
if st.button("RUN CALCULATION"):
    if cti_ms < 120:
        st.error("CTI Error: CTI must be greater than or equal to 120ms.") [cite: 17]
    else:
        try:
            cti_s = cti_ms / 1000
            flc_lv = round((mva * 1000) / (math.sqrt(3) * lv), 2)
            flc_hv = round((mva * 1000) / (math.sqrt(3) * hv), 2)
            isc_lv = round(flc_lv / (z_pct / 100), 2)
            if_lv = round(isc_lv * 0.9, 2)
            if_hv = round(if_lv / (hv / lv), 2)

            f_oc_txt, f_ef_txt = "", ""
            max_t_oc, max_t_ef = 0.0, 0.0

            for i, f in enumerate(temp_feeder_list):
                l, ct = f['l'], f['c']
                if ct == 0: continue
                # OC Calculations [cite: 23, 24]
                p_oc = round(1.1 * l, 2); r1 = round(p_oc/ct, 2)
                t_oc = round(0.025 * (0.14 / (math.pow(max(1.05, if_lv/p_oc), 0.02) - 1)), 3)
                max_t_oc = max(max_t_oc, t_oc)
                p2 = round(3*l, 2); r2 = round(p2/ct, 2)
                f_oc_txt += f"FEEDER Q{i+1}: Load={l}A, CT={ct}\n - S1 (IDMT): Pickup={p_oc}A ({r1}*In), TMS=0.025, Time={t_oc}s\n - S2 (DT):   Pickup={p2}A ({r2}*In), Time=0.0s\n\n"
                # EF Calculations [cite: 25, 26]
                p_ef = round(0.15 * l, 2); r_ef1 = round(p_ef/ct, 2)
                t_ef = round(0.025 * (0.14 / (math.pow(max(1.05, if_lv/p_ef), 0.02) - 1)), 3)
                max_t_ef = max(max_t_ef, t_ef)
                p_ef2 = round(1.0*l, 2); r_ef2 = round(p_ef2/ct, 2)
                f_ef_txt += f"FEEDER Q{i+1}: Load={l}A, CT={ct}\n - S1 (IDMT): Pickup={p_ef}A ({r_ef1}*In), TMS=0.025, Time={t_ef}s\n - S2 (DT):   Pickup={p_ef2}A ({r_ef2}*In), Time=0.0s\n\n"

            # Incomer/HV Coordination [cite: 29, 30, 31, 32, 33]
            hv_load = total_load / (hv / lv)
            coord_data = [
                ("INCOMER Q4 (LV)", q4_ct, if_lv, 1, round(0.9*isc_lv,2), cti_ms, max_t_oc, max_t_ef),
                ("HV SIDE Q5 (HV)", q5_ct, if_hv, hv/lv, round(if_hv,2), cti_ms*2, max_t_oc+cti_s, max_t_ef+cti_s)
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

            # Final Report Compilation [cite: 34]
            head = f"FLC LV: {flc_lv}A | FLC HV: {flc_hv}A | Short Circuit: {isc_lv}A\n" + "="*60 + "\n"
            st.session_state.oc_report_txt = head + f_oc_txt + i_oc
            st.session_state.ef_report_txt = head + f_ef_txt + i_ef

            # Display Alerts
            if total_load > flc_lv:
                st.error(f"CRITICAL ALERT: TRANSFORMER OVERLOAD ({total_load}A > {flc_lv}A)")
            for alert in ct_alerts:
                st.warning(alert)
                
        except Exception as e:
            st.error(f"Invalid Inputs or Calculation Error: {e}") [cite: 35]

# --- Output Display (Tabs) [cite: 11, 12] ---
if st.session_state.oc_report_txt:
    tab_oc, tab_ef = st.tabs([" Overcurrent (Phase) ", " Earth Fault (Neutral) "])
    with tab_oc:
        st.code(st.session_state.oc_report_txt)
    with tab_ef:
        st.code(st.session_state.ef_report_txt)

st.markdown('<div class="footer">By Protection and Automation Division, GOD</div>', unsafe_allow_html=True)
