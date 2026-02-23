import streamlit as st
import math
import pandas as pd
from fpdf import FPDF
import io

# --- Page Configuration ---
st.set_page_config(
    page_title="NEA Grid Protection Coordination Tool",
    page_icon="⚡",
    layout="wide"
)

# --- Custom CSS for Styling ---
st.markdown("""
    <style>
    .report-text {
        font-family: 'Consolas', 'Courier New', monospace;
        background-color: #f1f3f5;
        padding: 15px;
        border-radius: 5px;
        border: 1px solid #dee2e6;
        white-space: pre-wrap;
        font-size: 14px;
        color: #212529;
    }
    .footer {
        font-style: italic;
        color: #6c757d;
        text-align: center;
        margin-top: 40px;
        border-top: 1px solid #eee;
        padding-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- PDF Generation Function ---
def generate_pdf_report(oc_content, ef_content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Courier", size=10)
    
    # Combine reports
    report_title = "NEA GRID PROTECTION COORDINATION REPORT"
    pdf.cell(200, 10, txt=report_title, ln=True, align='C')
    pdf.ln(5)
    
    pdf.cell(200, 10, txt="--- OVERCURRENT (PHASE) PROTECTION ---", ln=True)
    for line in oc_content.split('\n'):
        pdf.cell(0, 6, txt=line, ln=True)
    
    pdf.add_page()
    pdf.cell(200, 10, txt="--- EARTH FAULT (NEUTRAL) PROTECTION ---", ln=True)
    for line in ef_content.split('\n'):
        pdf.cell(0, 6, txt=line, ln=True)
        
    return pdf.output()

# --- Application Logic ---
st.title("Nepal Electricity Authority (NEA)")
st.subheader("Grid Protection Coordination Tool - GOD")

# Sidebar for File Menu Operations
with st.sidebar:
    st.header("File Menu")
    if st.button("Preload Default Data"):
        st.session_state['mva'] = 16.6
        st.session_state['hv'] = 33.0
        st.session_state['lv'] = 11.0
        st.session_state['z'] = 10.0
        st.session_state['cti'] = 150.0
        st.session_state['q4'] = 900.0
        st.session_state['q5'] = 300.0
        st.session_state['num_feeders'] = 3
        st.rerun()

    if st.button("Reset All Data"):
        st.session_state.clear()
        st.rerun()

# --- 1. Transformer & System Data (Inputs) ---
with st.expander("Transformer & System Data", expanded=True):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        mva = st.number_input("MVA", value=st.session_state.get('mva', 0.0))
        hv_v = st.number_input("HV (kV)", value=st.session_state.get('hv', 0.0))
    with col2:
        lv_v = st.number_input("LV (kV)", value=st.session_state.get('lv', 0.0))
        z_pct = st.number_input("Z%", value=st.session_state.get('z', 0.0))
    with col3:
        cti_ms = st.number_input("CTI (ms)", value=st.session_state.get('cti', 150.0))
        q4_ct = st.number_input("Q4 Incomer CT", value=st.session_state.get('q4', 0.0))
    with col4:
        q5_ct = st.number_input("Q5 HV CT", value=st.session_state.get('q5', 0.0))

# --- 2. Feeder Configuration ---
st.header("Feeder Configuration")
num_feeders = st.number_input("Number of Feeders", min_value=0, max_value=20, value=st.session_state.get('num_feeders', 3))

feeder_list = []
current_total_load = 0.0

for i in range(int(num_feeders)):
    fcol1, fcol2, fcol3 = st.columns([1, 2, 2])
    with fcol1:
        st.write(f"**Feeder Q{i+1}**")
    with fcol2:
        # Default loads for preloading logic
        def_l = 0.0
        if i == 0 and 'mva' in st.session_state: def_l = 200.0
        elif i == 1 and 'mva' in st.session_state: def_l = 250.0
        elif i == 2 and 'mva' in st.session_state: def_l = 300.0
        
        l_val = st.number_input(f"Load (A)", key=f"l_{i}", value=def_l)
    with fcol3:
        def_c = 0.0
        if 'mva' in st.session_state: def_c = 400.0
        c_val = st.number_input(f"CT Ratio", key=f"c_{i}", value=def_c)
    
    feeder_list.append({'l': l_val, 'ct': c_val})
    current_total_load += l_val

st.info(f"Total Connected Load: {round(current_total_load, 2)} A")

# --- 3. Run Calculation Logic ---
if st.button("RUN CALCULATION", type="primary"):
    try:
        if cti_ms < 120: [cite: 17]
            st.error("CTI must be greater than or equal to 120ms.")
        else:
            # Constants & Conversions
            cti_s = cti_ms / 1000 [cite: 18]
            flc_lv = round((mva * 1000) / (math.sqrt(3) * lv_v), 2) [cite: 19]
            flc_hv = round((mva * 1000) / (math.sqrt(3) * hv_v), 2) [cite: 19]
            isc_lv = round(flc_lv / (z_pct / 100), 2) [cite: 19]
            if_lv = round(isc_lv * 0.9, 2) [cite: 19]
            if_hv = round(if_lv / (hv_v / lv_v), 2) [cite: 19]

            f_oc_txt, f_ef_txt = "", ""
            ct_alerts = []
            max_t_oc, max_t_ef = 0.0, 0.0

            # Feeder Calculations [cite: 21, 23, 24, 25, 26]
            for i, f in enumerate(feeder_list):
                l, ct = f['l'], f['ct']
                if ct < l and ct > 0:
                    ct_alerts.append(f"ALERT: Feeder Q{i+1} CT ({ct}A) < Load ({l}A)")
                
                # OC
                p_oc = round(1.1 * l, 2)
                r1 = round(p_oc/ct, 2) if ct > 0 else 0
                t_oc = round(0.025 * (0.14 / (math.pow(max(1.05, if_lv/p_oc if p_oc > 0 else 1.05), 0.02) - 1)), 3)
                max_t_oc = max(max_t_oc, t_oc)
                p2 = round(3*l, 2)
                r2 = round(p2/ct, 2) if ct > 0 else 0
                f_oc_txt += f"FEEDER Q{i+1}: Load={l}A, CT={ct}\n - S1 (IDMT): Pickup={p_oc}A ({r1}*In), TMS=0.025, Time={t_oc}s\n - S2 (DT):   Pickup={p2}A ({r2}*In), Time=0.0s\n\n"

                # EF
                p_ef = round(0.15 * l, 2)
                r_ef1 = round(p_ef/ct, 2) if ct > 0 else 0
                t_ef = round(0.025 * (0.14 / (math.pow(max(1.05, if_lv/p_ef if p_ef > 0 else 1.05), 0.02) - 1)), 3)
                max_t_ef = max(max_t_ef, t_ef)
                p_ef2 = round(1.0*l, 2)
                r_ef2 = round(p_ef2/ct, 2) if ct > 0 else 0
                f_ef_txt += f"FEEDER Q{i+1}: Load={l}A, CT={ct}\n - S1 (IDMT): Pickup={p_ef}A ({r_ef1}*In), TMS=0.025, Time={t_ef}s\n - S2 (DT):   Pickup={p_ef2}A ({r_ef2}*In), Time=0.0s\n\n"

            # Incomer (Q4) and HV Side (Q5) Coordination Calculations 
            hv_load = current_total_load / (hv_v / lv_v)
            if q4_ct < current_total_load:
                ct_alerts.append(f"ALERT: Q4 Incomer CT ({q4_ct}A) < Total Load ({current_total_load}A)")
            if q5_ct < hv_load:
                ct_alerts.append(f"ALERT: Q5 HV CT ({q5_ct}A) < HV Load ({round(hv_load,2)}A)")

            # Q4 & Q5 Coordination Logic
            coord_data = [
                ("INCOMER Q4 (LV)", q4_ct, if_lv, 1, round(0.9*isc_lv,2), cti_ms, max_t_oc, max_t_ef),
                ("HV SIDE Q5 (HV)", q5_ct, if_hv, hv_v/lv_v, round(if_hv,2), cti_ms*2, max_t_oc+cti_s, max_t_ef+cti_s)
            ]

            i_oc, i_ef = "", ""
            for name, ct_v, fault, scale, s3, dt_ms, t_prev_oc, t_prev_ef in coord_data:
                l_cur = current_total_load / scale
                t_req_oc, t_req_ef = round(t_prev_oc + cti_s, 3), round(t_prev_ef + cti_s, 3)
                
                # OC Coordination
                p_oc = round(1.1 * l_cur, 2)
                r1 = round(p_oc/ct_v, 2) if ct_v > 0 else 0
                tms_oc = round(t_req_oc / (0.14 / (math.pow(max(1.05, fault/p_oc if p_oc > 0 else 1.05), 0.02) - 1)), 3)
                p2 = round(3*l_cur, 2)
                r2 = round(p2/ct_v, 2) if ct_v > 0 else 0
                r3 = round(s3/ct_v, 2) if ct_v > 0 else 0
                i_oc += f"{name}: Load={round(l_cur,2)}A, CT={ct_v}\n - S1 (IDMT): Pickup={p_oc}A ({r1}*In), TMS={tms_oc}, Time={t_req_oc}s\n - S2 (DT):   Pickup={p2}A ({r2}*In), Time={dt_ms/1000}s\n - S3 (DT):   Pickup={s3}A ({r3}*In), Time=0.0s\n\n"

                # EF Coordination
                p_ef = round(0.15 * l_cur, 2)
                r_ef1 = round(p_ef/ct_v, 2) if ct_v > 0 else 0
                tms_ef = round(t_req_ef / (0.14 / (math.pow(max(1.05, fault/p_ef if p_ef > 0 else 1.05), 0.02) - 1)), 3)
                p_ef2 = round(1.0*l_cur, 2)
                r_ef2 = round(p_ef2/ct_v, 2) if ct_v > 0 else 0
                r_ef3 = round(s3/ct_v, 2) if ct_v > 0 else 0
                i_ef += f"{name}: Load={round(l_cur,2)}A, CT={ct_v}\n - S1 (IDMT): Pickup={p_ef}A ({r_ef1}*In), TMS={tms_ef}, Time={t_req_ef}s\n - S2 (DT):   Pickup={p_ef2}A ({r_ef2}*In), Time={dt_ms/1000}s\n - S3 (DT):   Pickup={s3}A ({r_ef3}*In), Time=0.0s\n\n"

            # Final Assembly
            head = f"FLC LV: {flc_lv}A | FLC HV: {flc_hv}A | Short Circuit: {isc_lv}A\n" + "="*60 + "\n"
            
            # Displays
            t1, t2 = st.tabs(["Overcurrent (Phase)", "Earth Fault (Neutral)"])
            
            with t1:
                if current_total_load > flc_lv: st.error(f"CRITICAL ALERT: TRANSFORMER OVERLOAD ({current_total_load}A > {flc_lv}A)")
                for alert in ct_alerts: st.warning(alert)
                oc_report = head + f_oc_txt + i_oc
                st.markdown(f'<div class="report-text">{oc_report}</div>', unsafe_allow_html=True)
                
            with t2:
                if current_total_load > flc_lv: st.error(f"CRITICAL ALERT: TRANSFORMER OVERLOAD ({current_total_load}A > {flc_lv}A)")
                for alert in ct_alerts: st.warning(alert)
                ef_report = head + f_ef_txt + i_ef
                st.markdown(f'<div class="report-text">{ef_report}</div>', unsafe_allow_html=True)

            # Export PDF
            st.divider()
            pdf_data = generate_pdf_report(oc_report, ef_report)
            st.download_button(
                label="Download PDF Report",
                data=pdf_data,
                file_name="NEA_Protection_Coordination.pdf",
                mime="application/pdf"
            )

    except Exception as e:
        st.error(f"Invalid Inputs or Calculation Error: {e}")

st.markdown('<div class="footer">By Protection and Automation Division, GOD</div>', unsafe_allow_html=True)
