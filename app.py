import streamlit as st
import pandas as pd
import math
import csv
from io import BytesIO, StringIO
from streamlit_option_menu import option_menu

# --- PDF Library Setup ---
try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

# --- Page Setup ---
st.set_page_config(page_title="NEA Grid Protection Coordination Tool", layout="wide")

# --- Initialize Session State ---
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

# --- Navigation Menu ---
selected_menu = option_menu(
    menu_title=None, 
    options=["Home", "Preload Default Data", "Save Tabulated CSV", "Save PDF", "Reset"],
    icons=["house", "cloud-download", "file-earmark-spreadsheet", "file-pdf", "arrow-counterclockwise"],
    menu_icon="cast", 
    default_index=0,
    orientation="horizontal",
)

# --- Menu Logic ---
if selected_menu == "Preload Default Data":
    st.session_state.sys_vars = {"mva": 16.6, "hv": 33.0, "lv": 11.0, "z": 10.0, "cti": 150.0, "q4": 900.0, "q5": 300.0}
    st.session_state.feeder_data = [{"l": 200.0, "c": 400.0}, {"l": 250.0, "c": 400.0}, {"l": 300.0, "c": 400.0}]
    st.rerun()

if selected_menu == "Reset":
    st.session_state.sys_vars = {k: 0.0 for k in st.session_state.sys_vars}
    st.session_state.feeder_data = []
    st.session_state.oc_report = ""
    st.session_state.ef_report = ""
    st.rerun()

# --- Main Application Header ---
st.title("Nepal Electricity Authority (NEA) Grid Protection Coordination Tool")

# --- Inputs: Transformer & System Data ---
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
    q4_ct = st.number_input("Q4 CT Ratio", value=float(st.session_state.sys_vars["q4"]))
     if q4_ct < total_load:
                self.sys_entries['q4'].config(bg="#ffcccc")
                ct_alerts.append(f"ALERT: Q4 Incomer CT ({q4_ct}A) is less than Total Load ({total_load}A)\n")
            else: self.sys_entries['q4'].config(bg="white")
with c4:
    q5_ct = st.number_input("Q5 CT Ratio", value=float(st.session_state.sys_vars["q5"]))

# --- Inputs: Feeder Configuration ---
st.subheader("Feeder Configuration")
num_feeders = st.number_input("No. of Feeders:", min_value=0, step=1, value=len(st.session_state.feeder_data))

# Sync session state with feeder count
if len(st.session_state.feeder_data) != num_feeders:
    st.session_state.feeder_data = [{"l": 0.0, "c": 0.0} for _ in range(int(num_feeders))]

current_feeders = []
total_load = 0.0

for i in range(int(num_feeders)):
    f1, f2 = st.columns(2)
    with f1:
        l_val = st.number_input(f"Q{i+1} Load (A):", value=st.session_state.feeder_data[i]["l"], key=f"l{i}")
    with f2:
        c_val = st.number_input(f"Q{i+1} CT Ratio:", value=st.session_state.feeder_data[i]["c"], key=f"c{i}")
    
    if c_val < l_val and c_val > 0:
        st.warning(f"Feeder Q{i+1} CT ({c_val}A) is less than Load ({l_val}A)")
    
    total_load += l_val
    current_feeders.append({"l": l_val, "c": c_val})

st.markdown(f"**Total Connected Load: {round(total_load, 2)} A**")

# --- Export/Download Section ---
if selected_menu == "Save Tabulated CSV" and st.session_state.oc_report:
    combined_csv = f"Overcurrent Report\n{st.session_state.oc_report}\n\nEarth Fault Report\n{st.session_state.ef_report}"
    st.download_button("Click to Download CSV", data=combined_csv, file_name="NEA_Coordination.csv", mime="text/csv")

if selected_menu == "Save PDF" and st.session_state.oc_report:
    if FPDF:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Courier", size=10)
        report_text = st.session_state.oc_report + "\n" + st.session_state.ef_report
        for line in report_text.split('\n'):
            pdf.cell(200, 7, txt=line, ln=True)
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        st.download_button("Click to Download PDF", data=pdf_bytes, file_name="NEA_Coordination.pdf", mime="application/pdf")
    else:
        st.error("FPDF library not installed. Please run 'pip install fpdf'")

# --- Calculation Logic ---
if st.button("RUN CALCULATION", type="primary"):
    if cti < 120:
        st.error("CTI Error: CTI must be greater than or equal to 120ms.")
    elif hv == 0 or lv == 0 or z == 0:
        st.error("Calculation Error: Voltage and Impedance (Z%) must be greater than 0.")
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

            # Feeder Level Calculations
            for i, f in enumerate(current_feeders):
                l_v, ct_v = f['l'], f['c']
                if ct_v == 0: continue
                
                # Overcurrent (OC)
                p_oc = round(1.1 * l_v, 2)
                r1 = round(p_oc/ct_v, 2)
                t_oc = round(0.025 * (0.14 / (math.pow(max(1.05, if_lv/p_oc), 0.02) - 1)), 3)
                max_t_oc = max(max_t_oc, t_oc)
                p2 = round(3 * l_v, 2)
                r2 = round(p2/ct_v, 2)
                f_oc += f"FEEDER Q{i+1}: Load={l_v}A, CT={ct_v}\n - S1 (IDMT): Pickup={p_oc}A ({r1}*In), TMS=0.025, Time={t_oc}s\n - S2 (DT):   Pickup={p2}A ({r2}*In), Time=0.0s\n\n"
                
                # Earth Fault (EF)
                p_ef = round(0.15 * l_v, 2)
                r_ef1 = round(p_ef/ct_v, 2)
                t_ef = round(0.025 * (0.14 / (math.pow(max(1.05, if_lv/p_ef), 0.02) - 1)), 3)
                max_t_ef = max(max_t_ef, t_ef)
                p_ef2 = round(1.0 * l_v, 2)
                r_ef2 = round(p_ef2/ct_v, 2)
                f_ef += f"FEEDER Q{i+1}: Load={l_v}A, CT={ct_v}\n - S1 (IDMT): Pickup={p_ef}A ({r_ef1}*In), TMS=0.025, Time={t_ef}s\n - S2 (DT):   Pickup={p_ef2}A ({r_ef2}*In), Time=0.0s\n\n"

            # Incomer and HV Side Coordination
            coord = [
                ("INCOMER Q4 (LV)", q4_ct, if_lv, 1, round(0.9 * isc_lv, 2), cti, max_t_oc, max_t_ef),
                ("HV SIDE Q5 (HV)", q5_ct, if_hv, hv/lv, round(if_hv, 2), cti * 2, max_t_oc + cti_s, max_t_ef + cti_s)
            ]
            
            i_oc, i_ef = "", ""
            for name, ct_v, fault, scale, s3, dt_ms, t_prev_oc, t_prev_ef in coord:
                if ct_v == 0: continue
                l_cur = total_load / scale
                
                # OC Incomer
                t_req_oc = round(t_prev_oc + cti_s, 3)
                p_oc = round(1.1 * l_cur, 2)
                r1 = round(p_oc/ct_v, 2)
                tms_oc = round(t_req_oc / (0.14 / (math.pow(max(1.05, fault/p_oc), 0.02) - 1)), 3)
                p2 = round(3 * l_cur, 2); r2 = round(p2/ct_v, 2); r3 = round(s3/ct_v, 2)
                i_oc += f"{name}: Load={round(l_cur,2)}A, CT={ct_v}\n - S1 (IDMT): Pickup={p_oc}A ({r1}*In), TMS={tms_oc}, Time={t_req_oc}s\n - S2 (DT):   Pickup={p2}A ({r2}*In), Time={dt_ms/1000}s\n - S3 (DT):   Pickup={s3}A ({r3}*In), Time=0.0s\n\n"
                
                # EF Incomer
                t_req_ef = round(t_prev_ef + cti_s, 3)
                p_ef = round(0.15 * l_cur, 2)
                r_ef1 = round(p_ef/ct_v, 2)
                tms_ef = round(t_req_ef / (0.14 / (math.pow(max(1.05, fault/p_ef), 0.02) - 1)), 3)
                p_ef2 = round(1.0 * l_cur, 2); r_ef2 = round(p_ef2/ct_v, 2); r_ef3 = round(s3/ct_v, 2)
                i_ef += f"{name}: Load={round(l_cur,2)}A, CT={ct_v}\n - S1 (IDMT): Pickup={p_ef}A ({r_ef1}*In), TMS={tms_ef}, Time={t_req_ef}s\n - S2 (DT):   Pickup={p_ef2}A ({r_ef2}*In), Time={dt_ms/1000}s\n - S3 (DT):   Pickup={s3}A ({r_ef3}*In), Time=0.0s\n\n"

            # Finalize Reports
            header = f"FLC LV: {flc_lv}A | FLC HV: {flc_hv}A | Short Circuit: {isc_lv}A\n" + "="*60 + "\n"
            st.session_state.oc_report = header + f_oc + i_oc
            st.session_state.ef_report = header + f_ef + i_ef

            if total_load > flc_lv:
                st.error(f"CRITICAL: TRANSFORMER OVERLOAD ({total_load}A > {flc_lv}A)")
                
        except Exception as e:
            st.error(f"Calculation Error: {e}")

# --- Output Display ---
if st.session_state.oc_report:
    tab1, tab2 = st.tabs([" Overcurrent (Phase) ", " Earth Fault (Neutral) "])
    with tab1:
        st.code(st.session_state.oc_report, language="text")
    with tab2:
        st.code(st.session_state.ef_report, language="text")

st.markdown("---")
st.caption("By Protection and Automation Division, GOD")

