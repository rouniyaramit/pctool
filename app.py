import streamlit as st
import pandas as pd
import math
import csv
import io
from fpdf import FPDF
import base64
import tempfile
import os

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
        white-space: pre-wrap;
        max-height: 600px;
        overflow-y: auto;
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
    div[data-testid="stNumberInput"] label {
        font-size: 12px;
        font-weight: normal;
    }
    .download-btn {
        display: inline-block;
        padding: 10px 20px;
        background-color: #0056b3;
        color: white;
        text-decoration: none;
        border-radius: 5px;
        margin-top: 10px;
        text-align: center;
    }
    .download-btn:hover {
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
if 'calculation_done' not in st.session_state:
    st.session_state.calculation_done = False
if 'show_csv_download' not in st.session_state:
    st.session_state.show_csv_download = False
if 'show_pdf_download' not in st.session_state:
    st.session_state.show_pdf_download = False
if 'csv_data' not in st.session_state:
    st.session_state.csv_data = None
if 'pdf_data' not in st.session_state:
    st.session_state.pdf_data = None

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
    if st.session_state.calculation_done:
        st.success("✅ Calculation completed")
    
    st.markdown('<p class="footer">By Protection and Automation Division, GOD</p>', unsafe_allow_html=True)

# Transformer & System Data Section
st.markdown('<p class="sub-header">Transformer & System Data (Inputs)</p>', unsafe_allow_html=True)

# Create columns for input parameters
col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

with col1:
    mva = st.number_input("MVA", min_value=0.0, value=16.6, step=0.1, format="%.2f", key="mva")
with col2:
    hv = st.number_input("HV (kV)", min_value=0.0, value=33.0, step=1.0, format="%.2f", key="hv")
with col3:
    lv = st.number_input("LV (kV)", min_value=0.0, value=11.0, step=1.0, format="%.2f", key="lv")
with col4:
    z = st.number_input("Z%", min_value=0.0, value=10.0, step=0.1, format="%.2f", key="z")
with col5:
    cti = st.number_input("CTI (ms)", min_value=120.0, value=150.0, step=10.0, format="%.0f", key="cti")
with col6:
    q4_ct = st.number_input("Q4 CT", min_value=0.0, value=900.0, step=50.0, format="%.0f", key="q4_ct")
with col7:
    q5_ct = st.number_input("Q5 CT", min_value=0.0, value=300.0, step=50.0, format="%.0f", key="q5_ct")

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

# Default load values for preload
default_loads = [200, 250, 300]
default_cts = [400, 400, 400]

for i in range(num_feeders):
    cols = st.columns([1, 2, 1, 2, 4])
    with cols[0]:
        st.markdown(f"**Q{i+1}**")
    with cols[1]:
        default_load = default_loads[i] if i < len(default_loads) else 200
        load = st.number_input(f"Load (A)", min_value=0.0, value=float(default_load), 
                               step=10.0, key=f"load_{i}", format="%.2f", label_visibility="collapsed")
        total_load += load
    with cols[2]:
        st.markdown("**CT:**")
    with cols[3]:
        default_ct = default_cts[i] if i < len(default_cts) else 400
        ct = st.number_input(f"CT Ratio", min_value=0.0, value=float(default_ct), 
                            step=50.0, key=f"ct_{i}", format="%.0f", label_visibility="collapsed")
    with cols[4]:
        # CT alert check
        if ct < load:
            st.markdown(f'<p style="color:red; font-weight:bold;">⚠ CT &lt; Load</p>', unsafe_allow_html=True)
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
            
            st.write("Debug: Processing feeders...")  # Debug
            
            # Process each feeder
            for i, fd in enumerate(feeder_data):
                l, ct_val = fd['load'], fd['ct']
                
                # CT alert
                if ct_val < l:
                    ct_alerts.append(f"ALERT: Feeder Q{i+1} CT ({ct_val}A) is less than Load ({l}A)")
                
                # Overcurrent calculations
                p_oc = round(1.1 * l, 2)
                r1 = round(p_oc/ct_val, 2) if ct_val > 0 else 0
                # Calculate IDMT time using standard inverse curve
                try:
                    t_oc = round(0.025 * (0.14 / (math.pow(max(1.05, if_lv/p_oc), 0.02) - 1)), 3)
                except:
                    t_oc = 0
                max_t_oc = max(max_t_oc, t_oc)
                p2 = round(3*l, 2)
                r2 = round(p2/ct_val, 2) if ct_val > 0 else 0
                
                oc_report_lines.append(f"FEEDER Q{i+1}: Load={l}A, CT={ct_val}")
                oc_report_lines.append(f" - S1 (IDMT): Pickup={p_oc}A ({r1}*In), TMS=0.025, Time={t_oc}s")
                oc_report_lines.append(f" - S2 (DT):   Pickup={p2}A ({r2}*In), Time=0.0s")
                oc_report_lines.append("")
                
                # Earth fault calculations
                p_ef = round(0.15 * l, 2)
                r_ef1 = round(p_ef/ct_val, 2) if ct_val > 0 else 0
                try:
                    t_ef = round(0.025 * (0.14 / (math.pow(max(1.05, if_lv/p_ef), 0.02) - 1)), 3)
                except:
                    t_ef = 0
                max_t_ef = max(max_t_ef, t_ef)
                p_ef2 = round(1.0*l, 2)
                r_ef2 = round(p_ef2/ct_val, 2) if ct_val > 0 else 0
                
                ef_report_lines.append(f"FEEDER Q{i+1}: Load={l}A, CT={ct_val}")
                ef_report_lines.append(f" - S1 (IDMT): Pickup={p_ef}A ({r_ef1}*In), TMS=0.025, Time={t_ef}s")
                ef_report_lines.append(f" - S2 (DT):   Pickup={p_ef2}A ({r_ef2}*In), Time=0.0s")
                ef_report_lines.append("")
            
            st.write("Debug: Processing Q4 and Q5...")  # Debug
            
            # HV Load calculation
            hv_load = total_load / (hv / lv) if hv > 0 and lv > 0 else 0
            
            # Q5 CT alert
            if q5_ct < hv_load:
                ct_alerts.append(f"ALERT: Q5 HV CT ({q5_ct}A) is less than HV Load ({round(hv_load,2)}A)")
            
            # Q4 CT alert
            if q4_ct < total_load:
                ct_alerts.append(f"ALERT: Q4 LV CT ({q4_ct}A) is less than LV Load ({round(total_load,2)}A)")
            
            # Coordination data for Q4 and Q5
            # INCOMER Q4 (LV Side)
            l_cur_q4 = total_load  # Load on LV side
            t_req_oc_q4 = round(max_t_oc + cti_s, 3)
            t_req_ef_q4 = round(max_t_ef + cti_s, 3)
            
            # Overcurrent for Q4
            p_oc_q4 = round(1.1 * l_cur_q4, 2)
            r1_q4 = round(p_oc_q4/q4_ct, 2) if q4_ct > 0 else 0
            try:
                denominator_oc_q4 = max(1.05, if_lv/p_oc_q4)
                tms_oc_q4 = round(t_req_oc_q4 / (0.14 / (math.pow(denominator_oc_q4, 0.02) - 1)), 3)
            except:
                tms_oc_q4 = 0
            
            p2_q4 = round(3 * l_cur_q4, 2)
            r2_q4 = round(p2_q4/q4_ct, 2) if q4_ct > 0 else 0
            s3_q4 = round(0.9 * isc_lv, 2)
            r3_q4 = round(s3_q4/q4_ct, 2) if q4_ct > 0 else 0
            
            oc_report_lines.append(f"INCOMER Q4 (LV Side): Load={round(l_cur_q4,2)}A, CT={q4_ct}")
            oc_report_lines.append(f" - S1 (IDMT): Pickup={p_oc_q4}A ({r1_q4}*In), TMS={tms_oc_q4}, Time={t_req_oc_q4}s")
            oc_report_lines.append(f" - S2 (DT):   Pickup={p2_q4}A ({r2_q4}*In), Time={cti/1000}s")
            oc_report_lines.append(f" - S3 (DT):   Pickup={s3_q4}A ({r3_q4}*In), Time=0.0s")
            oc_report_lines.append("")
            
            # Earth Fault for Q4
            p_ef_q4 = round(0.15 * l_cur_q4, 2)
            r_ef1_q4 = round(p_ef_q4/q4_ct, 2) if q4_ct > 0 else 0
            try:
                denominator_ef_q4 = max(1.05, if_lv/p_ef_q4)
                tms_ef_q4 = round(t_req_ef_q4 / (0.14 / (math.pow(denominator_ef_q4, 0.02) - 1)), 3)
            except:
                tms_ef_q4 = 0
            
            p_ef2_q4 = round(1.0 * l_cur_q4, 2)
            r_ef2_q4 = round(p_ef2_q4/q4_ct, 2) if q4_ct > 0 else 0
            r_ef3_q4 = round(s3_q4/q4_ct, 2) if q4_ct > 0 else 0
            
            ef_report_lines.append(f"INCOMER Q4 (LV Side): Load={round(l_cur_q4,2)}A, CT={q4_ct}")
            ef_report_lines.append(f" - S1 (IDMT): Pickup={p_ef_q4}A ({r_ef1_q4}*In), TMS={tms_ef_q4}, Time={t_req_ef_q4}s")
            ef_report_lines.append(f" - S2 (DT):   Pickup={p_ef2_q4}A ({r_ef2_q4}*In), Time={cti/1000}s")
            ef_report_lines.append(f" - S3 (DT):   Pickup={s3_q4}A ({r_ef3_q4}*In), Time=0.0s")
            ef_report_lines.append("")
            
            # HV SIDE Q5 (HV Side)
            l_cur_q5 = total_load / (hv / lv) if hv > 0 and lv > 0 else 0
            t_req_oc_q5 = round(max_t_oc + (2 * cti_s), 3)  # Double CTI for HV side
            t_req_ef_q5 = round(max_t_ef + (2 * cti_s), 3)
            
            # Overcurrent for Q5
            p_oc_q5 = round(1.1 * l_cur_q5, 2)
            r1_q5 = round(p_oc_q5/q5_ct, 2) if q5_ct > 0 else 0
            try:
                denominator_oc_q5 = max(1.05, if_hv/p_oc_q5)
                tms_oc_q5 = round(t_req_oc_q5 / (0.14 / (math.pow(denominator_oc_q5, 0.02) - 1)), 3)
            except:
                tms_oc_q5 = 0
            
            p2_q5 = round(3 * l_cur_q5, 2)
            r2_q5 = round(p2_q5/q5_ct, 2) if q5_ct > 0 else 0
            s3_q5 = round(if_hv, 2)
            r3_q5 = round(s3_q5/q5_ct, 2) if q5_ct > 0 else 0
            
            oc_report_lines.append(f"HV SIDE Q5 (HV Side): Load={round(l_cur_q5,2)}A, CT={q5_ct}")
            oc_report_lines.append(f" - S1 (IDMT): Pickup={p_oc_q5}A ({r1_q5}*In), TMS={tms_oc_q5}, Time={t_req_oc_q5}s")
            oc_report_lines.append(f" - S2 (DT):   Pickup={p2_q5}A ({r2_q5}*In), Time={(2*cti)/1000}s")
            oc_report_lines.append(f" - S3 (DT):   Pickup={s3_q5}A ({r3_q5}*In), Time=0.0s")
            oc_report_lines.append("")
            
            # Earth Fault for Q5
            p_ef_q5 = round(0.15 * l_cur_q5, 2)
            r_ef1_q5 = round(p_ef_q5/q5_ct, 2) if q5_ct > 0 else 0
            try:
                denominator_ef_q5 = max(1.05, if_hv/p_ef_q5)
                tms_ef_q5 = round(t_req_ef_q5 / (0.14 / (math.pow(denominator_ef_q5, 0.02) - 1)), 3)
            except:
                tms_ef_q5 = 0
            
            p_ef2_q5 = round(1.0 * l_cur_q5, 2)
            r_ef2_q5 = round(p_ef2_q5/q5_ct, 2) if q5_ct > 0 else 0
            r_ef3_q5 = round(s3_q5/q5_ct, 2) if q5_ct > 0 else 0
            
            ef_report_lines.append(f"HV SIDE Q5 (HV Side): Load={round(l_cur_q5,2)}A, CT={q5_ct}")
            ef_report_lines.append(f" - S1 (IDMT): Pickup={p_ef_q5}A ({r_ef1_q5}*In), TMS={tms_ef_q5}, Time={t_req_ef_q5}s")
            ef_report_lines.append(f" - S2 (DT):   Pickup={p_ef2_q5}A ({r_ef2_q5}*In), Time={(2*cti)/1000}s")
            ef_report_lines.append(f" - S3 (DT):   Pickup={s3_q5}A ({r_ef3_q5}*In), Time=0.0s")
            ef_report_lines.append("")
            
            # Header
            header = f"FLC LV: {flc_lv}A | FLC HV: {flc_hv}A | Short Circuit LV: {isc_lv}A | If LV: {if_lv}A | If HV: {if_hv}A\n" + "="*80
            
            # Store reports in session state
            full_oc_report = []
            full_ef_report = []
            
            # Add alerts
            if total_load > flc_lv:
                alert_msg = f"CRITICAL ALERT: TRANSFORMER OVERLOAD ({total_load}A > {flc_lv}A)"
                full_oc_report.append(alert_msg)
                full_ef_report.append(alert_msg)
                full_oc_report.append("")
                full_ef_report.append("")
            
            if ct_alerts:
                for alert in ct_alerts:
                    full_oc_report.append(alert)
                    full_ef_report.append(alert)
                full_oc_report.append("")
                full_ef_report.append("")
            
            full_oc_report.append(header)
            full_ef_report.append(header)
            full_oc_report.append("")
            full_ef_report.append("")
            
            full_oc_report.extend(oc_report_lines)
            full_ef_report.extend(ef_report_lines)
            
            st.session_state.oc_report = "\n".join(full_oc_report)
            st.session_state.ef_report = "\n".join(full_ef_report)
            st.session_state.calculation_done = True
            
            # Clear download flags
            st.session_state.show_csv_download = False
            st.session_state.show_pdf_download = False
            
            st.success("✅ Calculation completed successfully!")
            st.rerun()

    except Exception as e:
        st.error(f"❌ Invalid Inputs: {e}")
        st.exception(e)

# Display Reports in Tabs
if st.session_state.oc_report or st.session_state.ef_report:
    tab1, tab2 = st.tabs(["🔴 Overcurrent (Phase)", "🟢 Earth Fault (Neutral)"])
    
    with tab1:
        st.markdown(f'<div class="report-box">{st.session_state.oc_report}</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown(f'<div class="report-box">{st.session_state.ef_report}</div>', unsafe_allow_html=True)

# Handle File Menu Actions
if 'preload_data' in st.session_state and st.session_state.preload_data:
    st.session_state.preload_data = False
    # Data is preloaded through default values in number inputs
    st.session_state.oc_report = ""
    st.session_state.ef_report = ""
    st.session_state.calculation_done = False
    st.rerun()

if 'reset_data' in st.session_state and st.session_state.reset_data:
    st.session_state.reset_data = False
    st.session_state.oc_report = ""
    st.session_state.ef_report = ""
    st.session_state.calculation_done = False
    st.session_state.show_csv_download = False
    st.session_state.show_pdf_download = False
    st.rerun()

# CSV Generation
if 'save_csv' in st.session_state and st.session_state.save_csv:
    st.session_state.save_csv = False
    if st.session_state.oc_report and st.session_state.ef_report:
        try:
            # Create CSV in memory
            csv_buffer = io.StringIO()
            writer = csv.writer(csv_buffer)
            writer.writerow(["EQUIPMENT", "FAULT TYPE", "STAGE", "PICKUP (A)", "RATIO (*In)", "TMS/DELAY", "TIME (s)"])
            
            def parse_and_write(txt, fault_type):
                curr = ""
                lines = txt.split('\n')
                for line in lines:
                    if ":" in line and "Load" in line:
                        curr = line.split(":")[0].strip()
                    elif "- S" in line:
                        try:
                            # Parse line like "- S1 (IDMT): Pickup=220A (0.55*In), TMS=0.025, Time=0.123s"
                            if "Pickup=" in line:
                                parts = line.split(":", 1)
                                if len(parts) > 1:
                                    stage = parts[0].strip()
                                    details = parts[1].strip()
                                    
                                    # Extract pickup
                                    if "Pickup=" in details:
                                        pickup_part = details.split("Pickup=")[1].split(",")[0].strip()
                                        if "(" in pickup_part and ")" in pickup_part:
                                            pickup_val = pickup_part.split("(")[0].replace("A", "").strip()
                                            ratio = pickup_part.split("(")[1].split(")")[0].replace("*In", "").strip()
                                        else:
                                            pickup_val = pickup_part.replace("A", "").strip()
                                            ratio = ""
                                        
                                        # Extract TMS
                                        if "TMS=" in details:
                                            tms = details.split("TMS=")[1].split(",")[0].strip()
                                        else:
                                            tms = ""
                                        
                                        # Extract Time
                                        if "Time=" in details:
                                            op_time = details.split("Time=")[1].strip()
                                        else:
                                            op_time = ""
                                        
                                        writer.writerow([curr, fault_type, stage, pickup_val, ratio, tms, op_time])
                        except Exception as e:
                            continue
            
            parse_and_write(st.session_state.oc_report, "Overcurrent")
            parse_and_write(st.session_state.ef_report, "Earth Fault")
            
            # Store CSV data in session state
            st.session_state.csv_data = csv_buffer.getvalue()
            st.session_state.show_csv_download = True
            
        except Exception as e:
            st.error(f"Error creating CSV: {e}")
    else:
        st.warning("Please run calculation first before saving CSV.")

# PDF Generation
if 'save_pdf' in st.session_state and st.session_state.save_pdf:
    st.session_state.save_pdf = False
    if st.session_state.oc_report and st.session_state.ef_report:
        try:
            # Check if FPDF is available
            try:
                from fpdf import FPDF
                
                # Create PDF
                pdf = FPDF()
                pdf.add_page()
                
                # Add title
                pdf.set_font("Arial", 'B', 14)
                pdf.cell(200, 10, txt="NEA Protection Coordination Report", ln=True, align='C')
                pdf.ln(10)
                
                # Add date
                from datetime import datetime
                pdf.set_font("Arial", '', 10)
                pdf.cell(200, 5, txt=f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align='C')
                pdf.ln(5)
                
                # Add content
                pdf.set_font("Courier", '', 8)
                
                # Write OC report
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(200, 8, txt="OVERCURRENT (PHASE) REPORT", ln=True)
                pdf.set_font("Courier", '', 8)
                
                for line in st.session_state.oc_report.split('\n'):
                    # Handle long lines
                    if len(line) > 95:
                        # Split long lines
                        while len(line) > 95:
                            try:
                                pdf.cell(200, 4, txt=line[:95], ln=True)
                            except:
                                pdf.cell(200, 4, txt=line[:95].encode('latin-1', 'ignore').decode('latin-1'), ln=True)
                            line = line[95:]
                        if line:
                            try:
                                pdf.cell(200, 4, txt=line, ln=True)
                            except:
                                pdf.cell(200, 4, txt=line.encode('latin-1', 'ignore').decode('latin-1'), ln=True)
                    else:
                        try:
                            pdf.cell(200, 4, txt=line, ln=True)
                        except:
                            pdf.cell(200, 4, txt=line.encode('latin-1', 'ignore').decode('latin-1'), ln=True)
                
                pdf.ln(5)
                
                # Write EF report
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(200, 8, txt="EARTH FAULT (NEUTRAL) REPORT", ln=True)
                pdf.set_font("Courier", '', 8)
                
                for line in st.session_state.ef_report.split('\n'):
                    # Handle long lines
                    if len(line) > 95:
                        # Split long lines
                        while len(line) > 95:
                            try:
                                pdf.cell(200, 4, txt=line[:95], ln=True)
                            except:
                                pdf.cell(200, 4, txt=line[:95].encode('latin-1', 'ignore').decode('latin-1'), ln=True)
                            line = line[95:]
                        if line:
                            try:
                                pdf.cell(200, 4, txt=line, ln=True)
                            except:
                                pdf.cell(200, 4, txt=line.encode('latin-1', 'ignore').decode('latin-1'), ln=True)
                    else:
                        try:
                            pdf.cell(200, 4, txt=line, ln=True)
                        except:
                            pdf.cell(200, 4, txt=line.encode('latin-1', 'ignore').decode('latin-1'), ln=True)
                
                # Save to bytes
                pdf_buffer = io.BytesIO()
                pdf_output = pdf.output(dest='S').encode('latin-1')
                pdf_buffer.write(pdf_output)
                pdf_buffer.seek(0)
                
                # Store PDF data in session state
                st.session_state.pdf_data = pdf_buffer.getvalue()
                st.session_state.show_pdf_download = True
                
            except ImportError:
                st.error("FPDF library not available. Please install it using: pip install fpdf")
            except Exception as e:
                st.error(f"Error creating PDF: {e}")
                
        except Exception as e:
            st.error(f"Error in PDF generation: {e}")
    else:
        st.warning("Please run calculation first before saving PDF.")

# Display download buttons
if st.session_state.show_csv_download and st.session_state.csv_data:
    b64 = base64.b64encode(st.session_state.csv_data.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="protection_coordination.csv" class="download-btn">📥 Download CSV File</a>'
    st.markdown(href, unsafe_allow_html=True)

if st.session_state.show_pdf_download and st.session_state.pdf_data:
    b64 = base64.b64encode(st.session_state.pdf_data).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="protection_coordination.pdf" class="download-btn">📥 Download PDF File</a>'
    st.markdown(href, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown('<p class="footer">By Protection and Automation Division, GOD</p>', unsafe_allow_html=True)
