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

# --- Custom Styles ---
st.markdown("""
    <style>
    .report-text {
        font-family: 'Consolas', monospace;
        background-color: #f9f9f9;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #ddd;
        white-space: pre-wrap;
    }
    .alert-text {
        color: #d9534f;
        font-weight: bold;
    }
    .footer {
        font-style: italic;
        color: #555555;
        text-align: center;
        margin-top: 50px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Helper Functions ---
def generate_pdf(oc_text, ef_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Courier", size=10)
    full_text = f"OVERCURRENT REPORT\n{oc_text}\n\nEARTH FAULT REPORT\n{ef_text}"
    for line in full_text.split('\n'):
        pdf.cell(0, 7, txt=line, ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- Sidebar / Menu Logic ---
with st.sidebar:
    st.header("File Operations")
    if st.button("Preload Default Data"):
        st.session_state['mva'] = 16.6
        st.session_state['hv'] = 33.0
        st.session_state['lv'] = 11.0
        st.session_state['z'] = 10.0
        st.session_state['cti'] = 150.0
        st.session_state['q4'] = 900.0
        st.session_state['q5'] = 300.0
        st.session_state['num_feeders'] = 3
        # Preloading specific feeder values
        st.session_state['f_l_0'], st.session_state['f_c_0'] = 200.0, 400.0
        st.session_state['f_l_1'], st.session_state['f_c_1'] = 250.0, 400.0
        st.session_state['f_l_2'], st.session_state['f_c_2'] = 300.0, 400.0
        st.rerun()

    if st.button("Reset"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

st.title("Nepal Electricity Authority (NEA)")
st.subheader("Grid Protection Coordination Tool - Protection & Automation Division, GOD")

# --- Inputs Section ---
st.header("Transformer & System Data")
col1, col2, col3, col4 = st.columns(4)

with col1:
    mva = st.number_input("MVA", value=st.session_state.get('mva', 0.0), key='mva_in')
    hv_v = st.number_input("HV (kV)", value=st.session_state.get('hv', 0.0), key='hv_in')
with col2:
    lv_v = st.number_input("LV (kV)", value=st.session_state.get('lv', 0.0), key='lv_in')
    z_pct = st.number_input("Z%", value=st.session_state.get('z', 0.0), key='z_in')
with col3:
    cti_ms = st.number_input("CTI (ms)", value=st.session_state.get('cti', 150.0), key='cti_in')
    q4_ct = st.number_input("Q4 Incomer CT", value=st.session_state.get('q4', 0.0), key='q4_in')
with col4:
    q5_ct = st.number_input("Q5 HV CT", value=st.session_state.get('q5', 0.0), key='q5_in')

# --- Feeder Configuration ---
st.header("Feeder Configuration")
num_feeders = st.number_input("Number of Feeders", min_value=1, max_value=20, value=st.session_state.get('num_feeders', 3))

feeder_data = []
total_load = 0.0

# Create dynamic rows for feeders
for i in range(int(num_feeders)):
    fcol1, fcol2, fcol3 = st.columns([1, 2, 2])
    with fcol1:
        st.write(f"**Feeder Q{i+1}**")
    with fcol2:
        l_val = st.number_input(f"Load (A)", key=f"f_l_{i}", value=st.session_state.get(f'f_l_{i}', 0.0))
    with fcol3:
        c_val = st.number_input(f"CT Ratio", key=f"f_c_{i}", value=st.session_state.get(f'f_c_{i}', 0.0))
    
    feeder_data.append({'l': l_val, 'ct': c_val})
    total_load += l_val

st.metric("Total Connected Load", f"{round(total_load, 2)} A")

# --- Calculations ---
if st.button("RUN CALCULATION", type="primary", use_container_width=True):
    if cti_ms < 120:
        st.error("CTI must be greater than or equal to 120ms.")
    elif mva == 0 or hv_v == 0 or lv_v == 0 or z_pct == 0:
        st.warning("Please ensure all Transformer parameters are non-zero.")
    else:
        # Calculations Logic
        cti_s = cti_ms / 1000
        flc_lv = round((mva * 1000) / (math.sqrt(3) * lv_v), 2)
        flc_hv = round((mva * 1000) / (math.sqrt(3) * hv_v), 2)
        isc_lv = round(flc_lv / (z_pct / 100), 2)
        if_lv = round(isc_lv * 0.9, 2)
        if_hv = round(if_lv / (hv_v / lv_v), 2)

        f_oc_txt, f_ef_txt = "", ""
        ct_alerts = []
        max_t_oc, max_t_ef = 0.0, 0.0

        # Feeders Loop
        for i, f in enumerate(feeder_data):
            l, ct = f['l'], f['ct']
            if ct < l and ct > 0:
                ct_alerts.append(f"ALERT: Feeder Q{i+1} CT ({ct}A) is less than Load ({l}A)")
            
            # OC Calculation
            p_oc = round(1.1 * l, 2)
            r1 = round(p_oc/ct, 2) if ct > 0 else 0
            t_oc = round(0.025 * (0.14 / (math.pow(max(1.05, if_lv/p_oc if p_oc > 0 else 1.05), 0.02) - 1)), 3)
            max_t_oc = max(max_t_oc, t_oc)
            p2 = round(3 * l, 2)
            r2 = round(p2/ct, 2) if ct > 0 else 0
            f_oc_txt += f"FEEDER Q{i+1}: Load={l}A, CT={ct}\n - S1 (IDMT): Pickup={p_oc}A ({r1}*In), TMS=0.025, Time={t_oc}s\n - S2 (DT):   Pickup={p2}A ({r2}*In), Time=0.0s\n\n"

            # EF Calculation
            p_ef = round(0.15 * l, 2)
            r_ef1 = round(p_ef/ct, 2) if ct > 0 else 0
            t_ef = round(0.025 * (0.14 / (math.pow(max(1.05, if_lv/p_ef if p_ef > 0 else 1.05), 0.02) - 1)), 3)
            max_t_ef = max(max_t_ef, t_ef)
            p_ef2 = round(1.0 * l, 2)
            r_ef2 = round(p_ef2/ct, 2) if ct > 0 else 0
            f_ef_txt += f"FEEDER Q{i+1}: Load={l}A, CT={ct}\n - S1 (IDMT): Pickup={p_ef}A ({r_ef1}*In), TMS=0.025, Time={t_ef}s\n - S2 (DT):   Pickup={p_ef2}A ({r_ef2}*In), Time=0.0s\n\n"

        # Incomer & HV Coordination
        hv_load = total_load / (hv_v / lv_v)
        if q4_ct < total_load: ct_alerts.append(f"ALERT: Q4 Incomer CT ({q4_ct}A) < Total Load ({total_load}A)")
        if q5_ct < hv_load: ct_alerts.append(f"ALERT: Q5 HV CT ({q5_ct}A) < HV Load ({round(hv_load,2)}A)")

        coord_data = [
            ("INCOMER Q4 (LV)", q4_ct, if_lv, 1, round(0.9*isc_lv,2), cti_ms, max_t_oc, max_t_ef),
            ("HV SIDE Q5 (HV)", q5_ct, if_hv, hv_v/lv_v, round(if_hv,2), cti_ms*2, max_t_oc+cti_s, max_t_ef+cti_s)
        ]

        i_oc, i_ef = "", ""
        for name, ct_v, fault, scale, s3, dt_ms, t_prev_oc, t_prev_ef in coord_data:
            l_cur = total_load / scale
            t_req_oc, t_req_ef = round(t_prev_oc + cti_s, 3), round(t_prev_ef + cti_s, 3)
            p_oc = round(1.1 * l_cur, 2)
            r1 = round(p_oc/ct_v, 2) if ct_v > 0 else 0
            tms_oc = round(t_req_oc / (0.14 / (math.pow(max(1.05, fault/p_oc if p_oc > 0 else 1.05), 0.02) - 1)), 3)
            p2 = round(3 * l_cur, 2)
            r2 = round(p2/ct_v, 2) if ct_v > 0 else 0
            r3 = round(s3/ct_v, 2) if ct_v > 0 else 0
            i_oc += f"{name}: Load={round(l_cur,2)}A, CT={ct_v}\n - S1 (IDMT): Pickup={p_oc}A ({r1}*In), TMS={tms_oc}, Time={t_req_oc}s\n - S2 (DT):   Pickup={p2}A ({r2}*In), Time={dt_ms/1000}s\n - S3 (DT):   Pickup={s3}A ({r3}*In), Time=0.0s\n\n"

            p_ef = round(0.15 * l_cur, 2)
            r_ef1 = round(p_ef/ct_v, 2) if ct_v > 0 else 0
            tms_ef = round(t_req_ef / (0.14 / (math.pow(max(1.05, fault/p_ef if p_ef > 0 else 1.05), 0.02) - 1)), 3)
            p_ef2 = round(1.0 * l_cur, 2)
            r_ef2 = round(p_ef2/ct_v, 2) if ct_v > 0 else 0
            r_ef3 = round(s3/ct_v, 2) if ct_v > 0 else 0
            i_ef += f"{name}: Load={round(l_cur,2)}A, CT={ct_v}\n - S1 (IDMT): Pickup={p_ef}A ({r_ef1}*In), TMS={tms_ef}, Time={t_req_ef}s\n - S2 (DT):   Pickup={p_ef2}A ({r_ef2}*In), Time={dt_ms/1000}s\n - S3 (DT):   Pickup={s3}A ({r_ef3}*In), Time=0.0s\n\n"

        # Final Reports Assembly
        header = f"FLC LV: {flc_lv}A | FLC HV: {flc_hv}A | Short Circuit: {isc_lv}A\n" + "="*60 + "\n"
        full_oc = header + f_oc_txt + i_oc
        full_ef = header + f_ef_txt + i_ef

        # Display Results
        tab1, tab2 = st.tabs(["Overcurrent (Phase)", "Earth Fault (Neutral)"])
        
        with tab1:
            if total_load > flc_lv: st.error(f"CRITICAL ALERT: TRANSFORMER OVERLOAD ({total_load}A > {flc_lv}A)")
            for alert in ct_alerts: st.warning(alert)
            st.markdown(f'<div class="report-text">{full_oc}</div>', unsafe_allow_html=True)
            
        with tab2:
            if total_load > flc_lv: st.error(f"CRITICAL ALERT: TRANSFORMER OVERLOAD ({total_load}A > {flc_lv}A)")
            for alert in ct_alerts: st.warning(alert)
            st.markdown(f'<div class="report-text">{full_ef}</div>', unsafe_allow_html=True)

        # Export Options
        st.divider()
        ecol1, ecol2 = st.columns(2)
        with ecol1:
            pdf_bytes = generate_pdf(full_oc, full_ef)
            st.download_button("Download PDF Report", data=pdf_bytes, file_name="NEA_Protection_Report.pdf", mime="application/pdf")
        with ecol2:
            # Simple CSV logic: Exporting the raw strings or structured data can be expanded here
            st.download_button("Download Text Report (.txt)", data=full_oc + "\n" + full_ef, file_name="NEA_Protection_Report.txt")

st.markdown('<div class="footer">By Protection and Automation Division, GOD</div>', unsafe_allow_html=True)
