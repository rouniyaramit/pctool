import streamlit as st
import pandas as pd
import math
import csv
import io
from fpdf import FPDF
import base64

# Page configuration
st.set_page_config(
    page_title="NEA Protection Coordination Tool",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 24px;
        font-weight: bold;
        color: #0056b3;
        margin-bottom: 20px;
    }
    .sub-header {
        font-size: 18px;
        font-weight: bold;
        color: #333;
        margin-top: 10px;
        margin-bottom: 10px;
    }
    .total-load {
        font-size: 16px;
        font-weight: bold;
        color: #d9534f;
        padding: 10px;
        border-radius: 5px;
        background-color: #f8f9fa;
        text-align: center;
    }
    .alert-red {
        color: #ff0000;
        font-weight: bold;
        background-color: #ffe6e6;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    .ct-alert {
        background-color: #ffcccc;
        padding: 5px;
        border-radius: 3px;
    }
    .footer {
        text-align: center;
        color: #555;
        font-style: italic;
        font-size: 12px;
        margin-top: 30px;
        padding: 10px;
    }
    .report-box {
        background-color: #f9f9f9;
        padding: 15px;
        border-radius: 5px;
        font-family: 'Courier New', monospace;
        font-size: 12px;
        border: 1px solid #ddd;
        margin-top: 10px;
    }
    .stButton > button {
        background-color: #0056b3;
        color: white;
        font-weight: bold;
        width: 100%;
    }
    .stButton > button:hover {
        background-color: #004494;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'feeder_rows' not in st.session_state:
    st.session_state.feeder_rows = []
if 'oc_report' not in st.session_state:
    st.session_state.oc_report = ""
if 'ef_report' not in st.session_state:
    st.session_state.ef_report = ""
if 'total_load' not in st.session_state:
    st.session_state.total_load = 0.0

# Header with logo
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown('<p class="main-header">Nepal Electricity Authority (NEA) Grid Protection Coordination Tool</p>', unsafe_allow_html=True)
with col2:
    # Try to display logo if exists
    try:
        st.image("logo.png", width=100)
    except:
        st.markdown("**NEA**")

# Sidebar for File menu equivalent
with st.sidebar:
    st.markdown('<p class="sub-header">File Menu</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📂 Preload Data", use_container_width=True):
            st.session_state.preload_data = True
        if st.button("📊 Save CSV", use_container_width=True):
            st.session_state.save_csv = True
    with col2:
        if st.button("📄 Save PDF", use_container_width=True):
            st.session_state.save_pdf = True
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.reset_data = True
    
    st.markdown("---")
    st.markdown('<p class="footer">By Protection and Automation Division, GOD</p>', unsafe_allow_html=True)

# Transformer & System Data Section
st.markdown('<p class="sub-header">Transformer & System Data (Inputs)</p>', unsafe_allow_html=True)

# Create columns for input parameters
col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

with col1:
    mva = st.number_input("MVA", min_value=0.0, value=16.6, step=0.1, format="%.2f")
with col2:
    hv = st.number_input("HV (kV)", min_value=0.0, value=33.0, step=1.0, format="%.2f")
with col3:
    lv = st.number_input("LV (kV)", min_value=0.0, value=11.0, step=1.0, format="%.2f")
with col4:
    z = st.number_input("Z%", min_value=0.0, value=10.0, step=0.1, format="%.2f")
with col5:
    cti = st.number_input("CTI (ms)", min_value=120.0, value=150.0, step=10.0, format="%.0f")
with col6:
    q4_ct = st.number_input("Q4 CT", min_value=0.0, value=900.0, step=50.0, format="%.0f")
with col7:
    q5_ct = st.number_input("Q5 CT", min_value=0.0, value=300.0, step=50.0, format="%.0f")

# Feeder Configuration Section
st.markdown('<p class="sub-header">Feeder Configuration</p>', unsafe_allow_html=True)

# Number of feeders control
col1, col2 = st.columns([1, 5])
with col1:
    num_feeders = st.number_input("No. of Feeders:", min_value=0, max_value=20, value=3, step=1, key="num_feeders")
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Update Rows", key="update_rows"):
        st.rerun()

# Create feeder input rows
feeder_data = []
total_load = 0.0

for i in range(num_feeders):
    cols = st.columns([1, 2, 1, 2, 4])
    with cols[0]:
        st.markdown(f"**Q{i+1}**")
    with cols[1]:
        load = st.number_input(f"Load (A)", min_value=0.0, value=200.0 if i == 0 else 250.0 if i == 1 else 300.0, 
                               step=10.0, key=f"load_{i}", format="%.2f")
        total_load += load
    with cols[2]:
        st.markdown("**CT Ratio:**")
    with cols[3]:
        ct = st.number_input(f"CT Ratio", min_value=0.0, value=400.0, 
                            step=50.0, key=f"ct_{i}", format="%.0f")
    with cols[4]:
        # CT alert check
        if ct < load:
            st.markdown(f'<p style="color:red; font-weight:bold;">⚠ CT < Load</p>', unsafe_allow_html=True)
        else:
            st.markdown("✓")
    
    feeder_data.append({'load': load, 'ct': ct, 'index': i})

# Update session state total load
st.session_state.total_load = total_load

# Display total connected load
st.markdown(f'<p class="total-load">Total Connected Load: {total_load:.2f} A</p>', unsafe_allow_html=True)

# Run Calculation Button
if st.button("RUN CALCULATION", key="calculate", use_container_width=True):
    try:
        # Validate CTI
        if cti < 120:
            st.error("CTI must be greater than or equal to 120ms.")
        else:
            # Calculations
            cti_s = cti / 1000
            
            # Calculate transformer values
            flc_lv = round((mva * 1000) / (math.sqrt(3) * lv), 2)
            flc_hv = round((mva * 1000) / (math.sqrt(3) * hv), 2)
            isc_lv = round(flc_lv / (z / 100), 2)
            if_lv = round(isc_lv * 0.9, 2)
            if_hv = round(if_lv / (hv / lv), 2)
            
            # Initialize reports
            oc_report_lines = []
            ef_report_lines = []
            ct_alerts = []
            max_t_oc, max_t_ef = 0.0, 0.0
            
            # Process each feeder
            for i, fd in enumerate(feeder_data):
                l, ct_val = fd['load'], fd['ct']
                
                # CT alert
                if ct_val < l:
                    ct_alerts.append(f"ALERT: Feeder Q{i+1} CT ({ct_val}A) is less than Load ({l}A)")
                
                # Overcurrent calculations
                p_oc = round(1.1 * l, 2)
                r1 = round(p_oc/ct_val, 2)
                t_oc = round(0.025 * (0.14 / (math.pow(max(1.05, if_lv/p_oc), 0.02) - 1)), 3)
                max_t_oc = max(max_t_oc, t_oc)
                p2 = round(3*l, 2)
                r2 = round(p2/ct_val, 2)
                
                oc_report_lines.append(f"FEEDER Q{i+1}: Load={l}A, CT={ct_val}")
                oc_report_lines.append(f" - S1 (IDMT): Pickup={p_oc}A ({r1}*In), TMS=0.025, Time={t_oc}s")
                oc_report_lines.append(f" - S2 (DT):   Pickup={p2}A ({r2}*In), Time=0.0s")
                oc_report_lines.append("")
                
                # Earth fault calculations
                p_ef = round(0.15 * l, 2)
                r_ef1 = round(p_ef/ct_val, 2)
                t_ef = round(0.025 * (0.14 / (math.pow(max(1.05, if_lv/p_ef), 0.02) - 1)), 3)
                max_t_ef = max(max_t_ef, t_ef)
                p_ef2 = round(1.0*l, 2)
                r_ef2 = round(p_ef2/ct_val, 2)
                
                ef_report_lines.append(f"FEEDER Q{i+1}: Load={l}A, CT={ct_val}")
                ef_report_lines.append(f" - S1 (IDMT): Pickup={p_ef}A ({r_ef1}*In), TMS=0.025, Time={t_ef}s")
                ef_report_lines.append(f" - S2 (DT):   Pickup={p_ef2}A ({r_ef2}*In), Time=0.0s")
                ef_report_lines.append("")
            
            # HV Load calculation
            hv_load = total_load / (hv / lv)
            
            # Q5 CT alert
            if q5_ct < hv_load:
                ct_alerts.append(f"ALERT: Q5 HV CT ({q5_ct}A) is less than HV Load ({round(hv_load,2)}A)")
            
            # Coordination data
            coord_data = [
                ("INCOMER Q4 (LV)", q4_ct, if_lv, 1, round(0.9*isc_lv,2), cti, max_t_oc, max_t_ef),
                ("HV SIDE Q5 (HV)", q5_ct, if_hv, hv/lv, round(if_hv,2), cti*2, max_t_oc+cti_s, max_t_ef+cti_s)
            ]
            
            # Process coordination data
            for name, ct_val, fault, scale, s3, dt_ms, t_prev_oc, t_prev_ef in coord_data:
                l_cur = total_load / scale
                t_req_oc = round(t_prev_oc + cti_s, 3)
                t_req_ef = round(t_prev_ef + cti_s, 3)
                
                # Overcurrent
                p_oc = round(1.1 * l_cur, 2)
                r1 = round(p_oc/ct_val, 2)
                tms_oc = round(t_req_oc / (0.14 / (math.pow(max(1.05, fault/p_oc), 0.02) - 1)), 3)
                p2 = round(3*l_cur, 2)
                r2 = round(p2/ct_val, 2)
                r3 = round(s3/ct_val, 2)
                
                oc_report_lines.append(f"{name}: Load={round(l_cur,2)}A, CT={ct_val}")
                oc_report_lines.append(f" - S1 (IDMT): Pickup={p_oc}A ({r1}*In), TMS={tms_oc}, Time={t_req_oc}s")
                oc_report_lines.append(f" - S2 (DT):   Pickup={p2}A ({r2}*In), Time={dt_ms/1000}s")
                oc_report_lines.append(f" - S3 (DT):   Pickup={s3}A ({r3}*In), Time=0.0s")
                oc_report_lines.append("")
                
                # Earth fault
                p_ef = round(0.15 * l_cur, 2)
                r_ef1 = round(p_ef/ct_val, 2)
                tms_ef = round(t_req_ef / (0.14 / (math.pow(max(1.05, fault/p_ef), 0.02) - 1)), 3)
                p_ef2 = round(1.0*l_cur, 2)
                r_ef2 = round(p_ef2/ct_val, 2)
                r_ef3 = round(s3/ct_val, 2)
                
                ef_report_lines.append(f"{name}: Load={round(l_cur,2)}A, CT={ct_val}")
                ef_report_lines.append(f" - S1 (IDMT): Pickup={p_ef}A ({r_ef1}*In), TMS={tms_ef}, Time={t_req_ef}s")
                ef_report_lines.append(f" - S2 (DT):   Pickup={p_ef2}A ({r_ef2}*In), Time={dt_ms/1000}s")
                ef_report_lines.append(f" - S3 (DT):   Pickup={s3}A ({r_ef3}*In), Time=0.0s")
                ef_report_lines.append("")
            
            # Header
            header = f"FLC LV: {flc_lv}A | FLC HV: {flc_hv}A | Short Circuit: {isc_lv}A\n" + "="*60
            
            # Store reports in session state
            full_oc_report = []
            full_ef_report = []
            
            # Add alerts
            if total_load > flc_lv:
                full_oc_report.append(f"CRITICAL ALERT: TRANSFORMER OVERLOAD ({total_load}A > {flc_lv}A)")
                full_ef_report.append(f"CRITICAL ALERT: TRANSFORMER OVERLOAD ({total_load}A > {flc_lv}A)")
            
            full_oc_report.extend(ct_alerts)
            full_ef_report.extend(ct_alerts)
            
            full_oc_report.append(header)
            full_ef_report.append(header)
            
            full_oc_report.extend(oc_report_lines)
            full_ef_report.extend(ef_report_lines)
            
            st.session_state.oc_report = "\n".join(full_oc_report)
            st.session_state.ef_report = "\n".join(full_ef_report)
            
            # Display success message
            st.success("Calculation completed successfully!")

    except Exception as e:
        st.error(f"Invalid Inputs: {e}")

# Display Reports in Tabs
if st.session_state.oc_report or st.session_state.ef_report:
    tab1, tab2 = st.tabs(["Overcurrent (Phase)", "Earth Fault (Neutral)"])
    
    with tab1:
        st.markdown(f'<div class="report-box">{st.session_state.oc_report}</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown(f'<div class="report-box">{st.session_state.ef_report}</div>', unsafe_allow_html=True)

# Handle File Menu Actions
if 'preload_data' in st.session_state and st.session_state.preload_data:
    st.session_state.preload_data = False
    # Data is preloaded through default values in number inputs
    st.rerun()

if 'reset_data' in st.session_state and st.session_state.reset_data:
    st.session_state.reset_data = False
    # Clear reports
    st.session_state.oc_report = ""
    st.session_state.ef_report = ""
    # Reset number inputs to default values
    # This will be handled by rerunning
    st.rerun()

if 'save_csv' in st.session_state and st.session_state.save_csv:
    st.session_state.save_csv = False
    if st.session_state.oc_report and st.session_state.ef_report:
        # Create CSV in memory
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(["EQUIPMENT", "FAULT TYPE", "STAGE", "PICKUP (A)", "RATIO (*In)", "TMS/DELAY", "TIME (s)"])
        
        def parse_and_write(txt, fault_type):
            curr = ""
            for line in txt.split('\n'):
                if ":" in line and "Load" in line:
                    curr = line.split(":")[0]
                elif "- S" in line:
                    parts = line.split(":")
                    if len(parts) > 1:
                        stage = parts[0].strip("- ")
                        details = parts[1].split(",")
                        pick_raw = details[0].split("=")[1].strip()
                        val = pick_raw.split("(")[0].strip()
                        rat = pick_raw.split("(")[1].replace("*In)", "").strip() if "(" in pick_raw else ""
                        tms = details[1].split("=")[1].strip()
                        op = details[2].split("=")[1].strip() if len(details) > 2 else "0.0s"
                        writer.writerow([curr, fault_type, stage, val, rat, tms, op])
        
        parse_and_write(st.session_state.oc_report, "Overcurrent")
        parse_and_write(st.session_state.ef_report, "Earth Fault")
        
        # Create download button
        csv_data = csv_buffer.getvalue()
        b64 = base64.b64encode(csv_data.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="protection_coordination.csv">Click here to download CSV</a>'
        st.markdown(href, unsafe_allow_html=True)
        st.success("CSV file ready for download!")

if 'save_pdf' in st.session_state and st.session_state.save_pdf:
    st.session_state.save_pdf = False
    if st.session_state.oc_report and st.session_state.ef_report and FPDF:
        # Create PDF in memory
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Courier", size=8)
        
        full_text = st.session_state.oc_report + "\n\n" + st.session_state.ef_report
        for line in full_text.split('\n'):
            pdf.cell(200, 4, txt=line[:95], ln=True)
        
        pdf_buffer = io.BytesIO()
        pdf.output(pdf_buffer)
        pdf_buffer.seek(0)
        
        # Create download button
        b64 = base64.b64encode(pdf_buffer.read()).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="protection_coordination.pdf">Click here to download PDF</a>'
        st.markdown(href, unsafe_allow_html=True)
        st.success("PDF file ready for download!")
    elif not FPDF:
        st.error("FPDF library not available")

# Footer
st.markdown("---")
st.markdown('<p class="footer">By Protection and Automation Division, GOD</p>', unsafe_allow_html=True)
