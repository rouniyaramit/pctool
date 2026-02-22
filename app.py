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

# --- CSS to Mimic Your Original Styles ---
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    .stButton>button { background-color: #0056b3; color: white; font-weight: bold; width: 100%; }
    .stButton>button:hover { background-color: #004494; color: white; }
    .footer { position: fixed; bottom: 0; width: 100%; color: #555555; font-style: italic; text-align: center; background-color: white; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- Initialize Session State (Prevents NameErrors) ---
if 'sys_vars' not in st.session_state:
    st.session_state.sys_vars = {"mva": 0.0, "hv": 0.0, "lv": 0.0, "z": 0.0, "cti": 0.0, "q4": 0.0, "q5": 0.0}
if 'feeder_data' not in st.session_state:
    st.session_state.feeder_data = [{"l": 0.0, "c": 0.0} for _ in range(3)]
if 'oc_txt' not in st.session_state:
    st.session_state.oc_txt = ""
if 'ef_txt' not in st.session_state:
    st.session_state.ef_txt = ""

# --- Top File Menu (Simulated via Sidebar) ---
with st.sidebar:
    st.header("File Menu")
    
    if st.button("Preload Default Data"):
        st.session_state.sys_vars = {"mva": 16.6, "hv": 33.0, "lv": 11.0, "z": 10.0, "cti": 150.0, "q4": 900.0, "q5": 300.0}
        st.session_state.feeder_data = [{"l": 200.0, "c": 400.0}, {"l": 250.0, "c": 400.0}, {"l": 300.0, "c": 400.0}]
        st.rerun()

    if st.button("Reset"):
        st.session_state.sys_vars = {k: 0.0 for k in st.session_state.sys_vars}
        st.session_state.feeder_data = [{"l": 0.0, "c": 0.0} for _ in range(3)]
        st.session_state.oc_txt = ""
        st.session_state.ef_txt = ""
        st.rerun()

    st.divider()
    
    # Export options available only after calculation
    if st.session_state.oc_txt:
        # CSV Export
        csv_buffer = StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(["REPORT OUTPUT"])
        writer.writerow([st.session_state.oc_txt])
        writer.writerow([st.session_state.ef_txt])
        st.download_button("Save Tabulated CSV", data=csv_buffer.getvalue(), file_name="NEA_Report.csv", mime="text/csv")

        # PDF Export
        if FPDF:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Courier", size=10)
            full_text = st.session_state.oc_txt + "\n" + st.session_state.ef_txt
            for line in full_text.split('\n'):
                pdf.cell(200, 7, txt=line, ln=True)
            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            st.download_button("Save PDF", data=pdf_bytes, file_name="NEA_Report.pdf", mime="application/pdf")

# --- Main GUI Structure ---
st.title("Nepal Electricity Authority (NEA) Grid Protection Coordination Tool")

# Transformer & System Data (Inputs) [cite: 7, 8]
st.subheader("Transformer & System Data (Inputs)")
col1, col2, col3, col4 = st.columns(4)
with col1:
    mva = st.number_input("MVA", value=float(st.session_state.sys_vars["mva"]))
    hv = st.number_input("HV (kV)", value=float(st.session_state.sys_vars["hv"]))
with col2:
    lv = st.number_input("LV (kV)", value=float(st.session_state.sys_vars["lv"]))
    z = st.number_input("Z%", value=float(st.session_state.sys_vars["z"]))
with col3:
    cti = st.number_input("CTI (ms)", value=float(st.session_state.sys_vars["cti"]))
    q4 = st.number_input("Q4 CT", value=float(st.session_state.sys_vars["q4"]))
with col4:
    q5 = st.number_input("Q5 CT", value=float(st.session_state.sys_vars["q5"]))

# Feeder Configuration [cite: 9, 10]
st.subheader("Feeder Configuration")
num_feeders = st.number_input("No. of Feeders:", min_value=1, step=1, value=len(st.session_state.feeder_data))

# Adjust internal data if number of feeders changes
if len(st.session_state.feeder_data) != num_feeders:
    st.session_state.feeder_data = [{"l": 0.0, "c": 0.0} for _ in range(int(num_feeders))]

current_feeder_input = []
total_load = 0.0

for i in range(int(num_feeders)):
    fcol1, fcol2 = st.columns(2)
    with fcol1:
        l_in = st.number_input(f"Q{i+1} Load (A):", value=st.session_state.feeder_data[i]["l"], key=f"l{i}")
    with fcol2:
        c_in = st.number_input(f"Q{i+1} CT Ratio:", value=st.session_state.feeder_data[i]["c"], key=f"c{i}")
    
    if c_in < l_in and c_in > 0:
        st.warning(f"ALERT: Feeder Q{i+1} CT ({c_in}A) is less than Load ({l_in}A)") [cite: 21]
    
    total_load += l_in
    current_feeder_input.append({"l": l_in, "c": c_in})

st.markdown(f"**Total Connected Load: {round(total_load, 2)} A**") [cite: 16]

# --- Calculation Logic (Exact Match to Your Code) --- [cite: 17, 18, 19]
if st.button("RUN CALCULATION"):
    if cti < 120:
        st.error("CTI Error: CTI must be greater than or equal to 120ms.") [cite: 17]
    else:
        try:
            cti_s = cti / 1000 [cite: 18]
            flc_lv = round((mva * 1000) / (math.sqrt(3) * lv), 2) [cite: 19]
            flc_hv = round((mva * 1000) / (math.sqrt(3) * hv), 2) [cite: 19]
            isc_lv = round(flc_lv / (z / 100), 2) [cite: 19]
            if_lv = round(isc_lv * 0.9, 2) [cite: 19]
            if_hv = round(if_lv / (hv / lv), 2) [cite: 19]

            f_oc, f_ef = "", ""
            max_t_oc, max_t_ef = 0.0, 0.0

            for i, f in enumerate(current_feeder_input):
                l_v, ct_v = f['l'], f['c']
                if ct_v == 0: continue
                # OC Stage 1 & 2 [cite: 23, 24]
                p_oc = round(1.1 * l_v, 2); r1 = round(p_oc/ct_v, 2)
                t_oc = round(0.025 * (0.14 / (math.pow(max(1.05, if_lv/p_oc), 0.02) - 1)), 3)
                max_t_oc = max(max_t_oc, t_oc)
                p2 = round(3*l_v, 2); r2 = round(p2/ct_v, 2)
                f_oc += f"FEEDER Q{i+1}: Load={l_v}A, CT={ct_v}\n - S1 (IDMT): Pickup={p_oc}A ({r1}*In), TMS=0.025, Time={t_oc}s\n - S2 (DT):   Pickup={p2}A ({r2}*In), Time=0.0s\n\n"
                # EF Stage 1 & 2 [cite: 25, 26]
                p_ef = round(0.15 * l_v, 2); r_ef1 = round(p_ef/ct_v, 2)
                t_ef = round(0.025 * (0.14 / (math.pow(max(1.05, if_lv/p_ef), 0.02) - 1)), 3)
                max_t_ef = max(max_t_ef, t_ef)
                p_ef2 = round(1.0*l_v, 2); r_ef2 = round(p_ef2/ct_v, 2)
                f_ef += f"FEEDER Q{i+1}: Load={l_v}A, CT={ct_v}\n - S1 (IDMT): Pickup={p_ef}A ({r_ef1}*In), TMS=0.025, Time={t_ef}s\n - S2 (DT):   Pickup={p_ef2}A ({r_ef2}*In), Time=0.0s\n\n"

            # Incomer & HV Coordination [cite: 29, 30, 31, 32, 33]
            coord = [
                ("INCOMER Q4 (LV)", q4, if_lv, 1, round(0.9*isc_lv,2), cti, max_t_oc, max_t_ef),
                ("HV SIDE Q5 (HV)", q5, if_hv, hv/lv, round(if_hv,2), cti*2, max_t_oc+cti_s, max_t_ef+cti_s)
            ]
            i_oc, i_ef = "", ""
            for name, ct_val, fault, scale, s3, dt_ms, t_prev_oc, t_prev_ef in coord:
                l_cur = total_load / scale
                t_req_oc, t_req_ef = round(t_prev_oc + cti_s, 3), round(t_prev_ef + cti_s, 3)
                p_oc = round(1.1 * l_cur, 2); r1 = round(p_oc/ct_val, 2)
                tms_oc = round(t_req_oc / (0.14 / (math.pow(max(1.05, fault/p_oc), 0.02) - 1)), 3)
                p2 = round(3*l_cur, 2); r2 = round(p2/ct_val, 2); r3 = round(s3/ct_val, 2)
                i_oc += f"{name}: Load={round(l_cur,2)}A, CT={ct_val}\n - S1 (IDMT): Pickup={p_oc}A ({r1}*In), TMS={tms_oc}, Time={t_req_oc}s\n - S2 (DT):   Pickup={p2}A ({r2}*In), Time={dt_ms/1000}s\n - S3 (DT):   Pickup={s3}A ({r3}*In), Time=0.0s\n\n"
                p_ef = round(0.15 * l_cur, 2); r_ef1 = round(p_ef/ct_val, 2)
                tms_ef = round(t_req_ef / (0.14 / (math.pow(max(1.05, fault/p_ef), 0.02) - 1)), 3)
                p_ef2 = round(1.0*l_cur, 2); r_ef2 = round(p_ef2/ct_val, 2); r_ef3 = round(s3/ct_val, 2)
                i_ef += f"{name}: Load={round(l_cur,2)}A, CT={ct_val}\n - S1 (IDMT): Pickup={p_ef}A ({r_ef1}*In), TMS={tms_ef}, Time={t_req_ef}s\n - S2 (DT):   Pickup={p_ef2}A ({r_ef2}*In), Time={dt_ms/1000}s\n - S3 (DT):   Pickup={s3}A ({r_ef3}*In), Time=0.0s\n\n"

            header = f"FLC LV: {flc_lv}A | FLC HV: {flc_hv}A | Short Circuit: {isc_lv}A\n" + "="*60 + "\n"
            if total_load > flc_lv:
                header = f"CRITICAL ALERT: TRANSFORMER OVERLOAD ({total_load}A > {flc_lv}A)\n" + header [cite: 34]
            
            st.session_state.oc_txt = header + f_oc + i_oc
            st.session_state.ef_txt = header + f_ef + i_ef
                
        except Exception as e:
            st.error(f"Error in calculations: {e}")

# --- Output Display (Tabs) --- [cite: 11, 12]
if st.session_state.oc_txt:
    tab1, tab2 = st.tabs([" Overcurrent (Phase) ", " Earth Fault (Neutral) "])
    with tab1:
        st.code(st.session_state.oc_txt)
    with tab2:
        st.code(st.session_state.ef_txt)

st.markdown('<div class="footer">By Protection and Automation Division, GOD</div>', unsafe_allow_html=True) [cite: 12]
