import streamlit as st
import pandas as pd
import math
from io import BytesIO

# Try to import FPDF for PDF generation
try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

# --- Page Configuration ---
st.set_page_config(page_title="NEA Grid Protection Coordination Tool", layout="wide")

# --- Custom Styling ---
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    .stAlert { margin-top: 10px; }
    .footer { position: fixed; bottom: 0; width: 100%; color: #555555; font-style: italic; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- Title and Header ---
col_title, col_logo = st.columns([4, 1])
with col_title:
    st.title("🇳🇵 NEA Grid Protection Coordination Tool")
    st.subheader("Protection and Automation Division, GOD")

# --- Helper Functions ---
def calculate_results(sys_data, feeder_data):
    # Extract System Variables [cite: 18]
    mva = sys_data['mva']
    hv_v = sys_data['hv']
    lv_v = sys_data['lv']
    z_pct = sys_data['z']
    cti_ms = sys_data['cti']
    q4_ct = sys_data['q4']
    q5_ct = sys_data['q5']
    
    cti_s = cti_ms / 1000

    # Base Calculations [cite: 19]
    flc_lv = round((mva * 1000) / (math.sqrt(3) * lv_v), 2)
    flc_hv = round((mva * 1000) / (math.sqrt(3) * hv_v), 2)
    isc_lv = round(flc_lv / (z_pct / 100), 2)
    if_lv = round(isc_lv * 0.9, 2)
    if_hv = round(if_lv / (hv_v / lv_v), 2)

    total_load = sum(f['load'] for f in feeder_data)
    hv_load = total_load / (hv_v / lv_v)

    reports = {"OC": [], "EF": [], "Alerts": []}
    
    # Overload Alert [cite: 34]
    if total_load > flc_lv:
        reports["Alerts"].append(f"CRITICAL: TRANSFORMER OVERLOAD ({total_load}A > {flc_lv}A)")

    # Feeder Calculations [cite: 23, 24, 25, 26]
    max_t_oc, max_t_ef = 0.0, 0.0
    
    for i, f in enumerate(feeder_data):
        l, ct = f['load'], f['ct']
        if ct < l:
            reports["Alerts"].append(f"Feeder Q{i+1} CT ({ct}A) < Load ({l}A)")
            
        # OC Calculations
        p_oc = round(1.1 * l, 2)
        r1 = round(p_oc/ct, 2)
        t_oc = round(0.025 * (0.14 / (math.pow(max(1.05, if_lv/p_oc), 0.02) - 1)), 3)
        max_t_oc = max(max_t_oc, t_oc)
        p2 = round(3*l, 2)
        r2 = round(p2/ct, 2)
        
        reports["OC"].append({
            "Equip": f"FEEDER Q{i+1}", "Load": l, "CT": ct,
            "S1_P": p_oc, "S1_R": r1, "S1_T": t_oc,
            "S2_P": p2, "S2_R": r2, "S2_T": 0.0
        })

        # EF Calculations
        p_ef = round(0.15 * l, 2)
        r_ef1 = round(p_ef/ct, 2)
        t_ef = round(0.025 * (0.14 / (math.pow(max(1.05, if_lv/p_ef), 0.02) - 1)), 3)
        max_t_ef = max(max_t_ef, t_ef)
        p_ef2 = round(1.0*l, 2)
        r_ef2 = round(p_ef2/ct, 2)

        reports["EF"].append({
            "Equip": f"FEEDER Q{i+1}", "Load": l, "CT": ct,
            "S1_P": p_ef, "S1_R": r_ef1, "S1_T": t_ef,
            "S2_P": p_ef2, "S2_R": r_ef2, "S2_T": 0.0
        })

    # Incomer and HV Coordination [cite: 29, 30, 31, 32, 33]
    coord_configs = [
        ("INCOMER Q4 (LV)", q4_ct, if_lv, 1, round(0.9*isc_lv,2), cti_ms, max_t_oc, max_t_ef),
        ("HV SIDE Q5 (HV)", q5_ct, if_hv, hv_v/lv_v, round(if_hv,2), cti_ms*2, max_t_oc+cti_s, max_t_ef+cti_s)
    ]

    for name, ct_v, fault, scale, s3, dt_ms, t_prev_oc, t_prev_ef in coord_configs:
        l_cur = total_load / scale
        t_req_oc, t_req_ef = round(t_prev_oc + cti_s, 3), round(t_prev_ef + cti_s, 3)
        
        # OC S1/S2/S3
        p_oc = round(1.1 * l_cur, 2); r1 = round(p_oc/ct_v, 2)
        tms_oc = round(t_req_oc / (0.14 / (math.pow(max(1.05, fault/p_oc), 0.02) - 1)), 3)
        p2 = round(3*l_cur, 2); r2 = round(p2/ct_v, 2); r3 = round(s3/ct_v, 2)
        
        reports["OC"].append({
            "Equip": name, "Load": round(l_cur,2), "CT": ct_v,
            "S1_P": p_oc, "S1_R": r1, "S1_T": t_req_oc, "TMS": tms_oc,
            "S2_P": p2, "S2_R": r2, "S2_T": dt_ms/1000,
            "S3_P": s3, "S3_R": r3, "S3_T": 0.0
        })

        # EF S1/S2/S3
        p_ef = round(0.15 * l_cur, 2); r_ef1 = round(p_ef/ct_v, 2)
        tms_ef = round(t_req_ef / (0.14 / (math.pow(max(1.05, fault/p_ef), 0.02) - 1)), 3)
        p_ef2 = round(1.0*l_cur, 2); r_ef2 = round(p_ef2/ct_v, 2); r_ef3 = round(s3/ct_v, 2)
        
        reports["EF"].append({
            "Equip": name, "Load": round(l_cur,2), "CT": ct_v,
            "S1_P": p_ef, "S1_R": r_ef1, "S1_T": t_req_ef, "TMS": tms_ef,
            "S2_P": p_ef2, "S2_R": r_ef2, "S2_T": dt_ms/1000,
            "S3_P": s3, "S3_R": r_ef3, "S3_T": 0.0
        })

    return reports, flc_lv, flc_hv, isc_lv

# --- Sidebar / Inputs ---
with st.sidebar:
    st.header("System Settings")
    if st.button("Preload Default Data"):
        st.session_state.mva = 16.6
        st.session_state.hv = 33.0
        st.session_state.lv = 11.0
        st.session_state.z = 10.0
        st.session_state.cti = 150.0
        st.session_state.q4 = 900.0
        st.session_state.q5 = 300.0

    mva = st.number_input("MVA", value=st.session_state.get('mva', 16.6))
    hv = st.number_input("HV (kV)", value=st.session_state.get('hv', 33.0))
    lv = st.number_input("LV (kV)", value=st.session_state.get('lv', 11.0))
    z = st.number_input("Z%", value=st.session_state.get('z', 10.0))
    cti = st.number_input("CTI (ms)", value=st.session_state.get('cti', 150.0))
    q4 = st.number_input("Q4 CT", value=st.session_state.get('q4', 900.0))
    q5 = st.number_input("Q5 CT", value=st.session_state.get('q5', 300.0))

# --- Main UI ---
st.header("Transformer & Feeder Data")
num_feeders = st.number_input("Number of Feeders", min_value=1, max_value=20, value=3)

feeder_data = []
cols = st.columns(2)
for i in range(num_feeders):
    with st.expander(f"Feeder Q{i+1} Configuration", expanded=True):
        c1, c2 = st.columns(2)
        load = c1.number_input(f"Load (A)", key=f"l{i}", value=200.0 if i==0 else 250.0 if i==1 else 300.0 if i==2 else 0.0)
        ct = c2.number_input(f"CT Ratio", key=f"c{i}", value=400.0)
        feeder_data.append({'load': load, 'ct': ct})

total_load_val = sum(f['load'] for f in feeder_data)
st.metric("Total Connected Load", f"{total_load_val} A")

if st.button("RUN CALCULATION", type="primary", use_container_width=True):
    if cti < 120:
        st.error("CTI must be greater than or equal to 120ms.")
    else:
        sys_data = {'mva': mva, 'hv': hv, 'lv': lv, 'z': z, 'cti': cti, 'q4': q4, 'q5': q5}
        res, flc_lv, flc_hv, isc_lv = calculate_results(sys_data, feeder_data)
        
        # Display Alerts
        for alert in res['Alerts']:
            st.error(alert)
            
        st.info(f"FLC LV: {flc_lv}A | FLC HV: {flc_hv}A | Short Circuit: {isc_lv}A")
        
        tab1, tab2 = st.tabs(["Overcurrent (Phase)", "Earth Fault (Neutral)"])
        
        with tab1:
            for item in res['OC']:
                st.markdown(f"**{item['Equip']}** (Load: {item['Load']}A, CT: {item['CT']})")
                st.text(f" - S1 (IDMT): Pickup={item['S1_P']}A ({item['S1_R']}*In), TMS={item.get('TMS', 0.025)}, Time={item['S1_T']}s")
                st.text(f" - S2 (DT):   Pickup={item['S2_P']}A ({item['S2_R']}*In), Time={item['S2_T']}s")
                if "S3_P" in item:
                    st.text(f" - S3 (DT):   Pickup={item['S3_P']}A ({item['S3_R']}*In), Time=0.0s")
                st.divider()

        with tab2:
            for item in res['EF']:
                st.markdown(f"**{item['Equip']}** (Load: {item['Load']}A, CT: {item['CT']})")
                st.text(f" - S1 (IDMT): Pickup={item['S1_P']}A ({item['S1_R']}*In), TMS={item.get('TMS', 0.025)}, Time={item['S1_T']}s")
                st.text(f" - S2 (DT):   Pickup={item['S2_P']}A ({item['S2_R']}*In), Time={item['S2_T']}s")
                if "S3_P" in item:
                    st.text(f" - S3 (DT):   Pickup={item['S3_P']}A ({item['S3_R']}*In), Time=0.0s")
                st.divider()

st.markdown('<div class="footer">By Protection and Automation Division, GOD</div>', unsafe_allow_html=True)






