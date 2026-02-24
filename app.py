# app.py
# Streamlit port of ef.py (NEAProtectionCoordinationTool)
# Keeps the exact calculation logic, report text format, CSV columns and PDF export.

import streamlit as st
import math
import csv
import io
from datetime import datetime
from PIL import Image
import base64

# Optional: fpdf for PDF export (same as ef.py)
try:
    from fpdf import FPDF
    HAS_FPDF = True
except Exception:
    HAS_FPDF = False

st.set_page_config(page_title="NEA Protection Coordination Tool", layout="wide")

# --- Helper functions that mirror ef.py logic exactly ---

def validate_numeric_str(s):
    if s is None or s == "":
        return True
    try:
        float(s)
        return True
    except:
        return False

def compute_reports(sys_vars, feeder_rows):
    """
    sys_vars: dict with keys mva,hv,lv,z,cti,q4,q5 (strings convertible to float)
    feeder_rows: list of dicts {'l': str, 'ct': str}
    Returns oc_text, ef_text, ct_alerts_list, flc_lv, flc_hv, isc_lv
    """
    # replicate ef.py behaviour and text formatting exactly
    try:
        cti_ms = float(sys_vars['cti'])
        if cti_ms < 120:
            return None, None, ["CTI_ERROR"], None, None, None
        mva = float(sys_vars['mva'])
        hv_v = float(sys_vars['hv'])
        lv_v = float(sys_vars['lv'])
        z_pct = float(sys_vars['z'])
        q4_ct = float(sys_vars['q4'])
        q5_ct = float(sys_vars['q5'])
        cti_s = cti_ms / 1000.0

        flc_lv = round((mva * 1000) / (math.sqrt(3) * lv_v), 2)
        flc_hv = round((mva * 1000) / (math.sqrt(3) * hv_v), 2)
        isc_lv = round(flc_lv / (z_pct / 100), 2)
        if_lv = round(isc_lv * 0.9, 2)
        if_hv = round(if_lv / (hv_v / lv_v), 2)

        total_load = 0.0
        max_t_oc = 0.0
        max_t_ef = 0.0
        f_oc_txt = ""
        f_ef_txt = ""
        ct_alerts = []

        # feeder loop
        for i, fr in enumerate(feeder_rows):
            l = float(fr.get('l', 0) or 0)
            ct = float(fr.get('ct', 0) or 0)
            total_load += l
            if ct < l:
                ct_alerts.append(f"ALERT: Feeder Q{i+1} CT ({ct}A) is less than Load ({l}A)\n")

            p_oc = round(1.1 * l, 2); r1 = round(p_oc/ct, 2) if ct != 0 else float('inf')
            # t_oc formula exactly as ef.py
            t_oc = round(0.025 * (0.14 / (math.pow(max(1.05, if_lv/p_oc), 0.02) - 1)), 3) if p_oc != 0 else 0.0
            max_t_oc = max(max_t_oc, t_oc)
            p2 = round(3*l, 2); r2 = round(p2/ct, 2) if ct != 0 else float('inf')
            f_oc_txt += f"FEEDER Q{i+1}: Load={l}A, CT={ct}\n - S1 (IDMT): Pickup={p_oc}A ({r1}*In), TMS=0.025, Time={t_oc}s\n - S2 (DT):   Pickup={p2}A ({r2}*In), Time=0.0s\n\n"

            p_ef = round(0.15 * l, 2); r_ef1 = round(p_ef/ct, 2) if ct != 0 else float('inf')
            t_ef = round(0.025 * (0.14 / (math.pow(max(1.05, if_lv/p_ef), 0.02) - 1)), 3) if p_ef != 0 else 0.0
            max_t_ef = max(max_t_ef, t_ef)
            p_ef2 = round(1.0*l, 2); r_ef2 = round(p_ef2/ct, 2) if ct != 0 else float('inf')
            f_ef_txt += f"FEEDER Q{i+1}: Load={l}A, CT={ct}\n - S1 (IDMT): Pickup={p_ef}A ({r_ef1}*In), TMS=0.025, Time={t_ef}s\n - S2 (DT):   Pickup={p_ef2}A ({r_ef2}*In), Time=0.0s\n\n"

        hv_load = total_load / (hv_v / lv_v) if (hv_v / lv_v) != 0 else 0.0

        if q5_ct < hv_load:
            ct_alerts.append(f"ALERT: Q5 HV CT ({q5_ct}A) is less than HV Load ({round(hv_load,2)}A)\n")

        coord_data = [
            ("INCOMER Q4 (LV)", q4_ct, if_lv, 1, round(0.9*isc_lv,2), cti_ms, max_t_oc, max_t_ef),
            ("HV SIDE Q5 (HV)", q5_ct, if_hv, hv_v/lv_v, round(if_hv,2), cti_ms*2, max_t_oc+cti_s, max_t_ef+cti_s)
        ]

        i_oc = ""
        i_ef = ""
        for name, ct_v, fault, scale, s3, dt_ms, t_prev_oc, t_prev_ef in coord_data:
            l_cur = total_load / scale if scale != 0 else 0.0
            t_req_oc = round(t_prev_oc + cti_s, 3)
            t_req_ef = round(t_prev_ef + cti_s, 3)
            p_oc = round(1.1 * l_cur, 2); r1 = round(p_oc/ct_v, 2) if ct_v != 0 else float('inf')
            denom_oc = (0.14 / (math.pow(max(1.05, fault/p_oc), 0.02) - 1)) if p_oc != 0 else 1.0
            tms_oc = round(t_req_oc / denom_oc, 3) if denom_oc != 0 else 0.0
            p2 = round(3*l_cur, 2)
            r2 = round(p2/ct_v, 2) if ct_v != 0 else float('inf')
            r3 = round(s3/ct_v, 2) if ct_v != 0 else float('inf')
            i_oc += f"{name}: Load={round(l_cur,2)}A, CT={ct_v}\n - S1 (IDMT): Pickup={p_oc}A ({r1}*In), TMS={tms_oc}, Time={t_req_oc}s\n - S2 (DT):   Pickup={p2}A ({r2}*In), Time={dt_ms/1000}s\n - S3 (DT):   Pickup={s3}A ({r3}*In), Time=0.0s\n\n"

            p_ef = round(0.15 * l_cur, 2); r_ef1 = round(p_ef/ct_v, 2) if ct_v != 0 else float('inf')
            denom_ef = (0.14 / (math.pow(max(1.05, fault/p_ef), 0.02) - 1)) if p_ef != 0 else 1.0
            tms_ef = round(t_req_ef / denom_ef, 3) if denom_ef != 0 else 0.0
            p_ef2 = round(1.0*l_cur, 2)
            r_ef2 = round(p_ef2/ct_v, 2) if ct_v != 0 else float('inf')
            r_ef3 = round(s3/ct_v, 2) if ct_v != 0 else float('inf')
            i_ef += f"{name}: Load={round(l_cur,2)}A, CT={ct_v}\n - S1 (IDMT): Pickup={p_ef}A ({r_ef1}*In), TMS={tms_ef}, Time={t_req_ef}s\n - S2 (DT):   Pickup={p_ef2}A ({r_ef2}*In), Time={dt_ms/1000}s\n - S3 (DT):   Pickup={s3}A ({r_ef3}*In), Time=0.0s\n\n"

        head = f"FLC LV: {flc_lv}A | FLC HV: {flc_hv}A | Short Circuit: {isc_lv}A\n" + "="*60 + "\n"

        oc_report_text = ""
        ef_report_text = ""
        # build reports same way ef.py does:
        # Insert critical alert and ct_alerts before the head, then the feeder text and i_oc / i_ef
        oc_prefix = ""
        ef_prefix = ""

        if total_load > flc_lv:
            oc_prefix += f"CRITICAL ALERT: TRANSFORMER OVERLOAD ({total_load}A > {flc_lv}A)\n"
            # ef.py inserts same alert into both reports
            ef_prefix += f"CRITICAL ALERT: TRANSFORMER OVERLOAD ({total_load}A > {flc_lv}A)\n"

        for alert in ct_alerts:
            oc_prefix += alert
            ef_prefix += alert

        oc_report_text = oc_prefix + head + (f_oc_txt + i_oc)
        ef_report_text = ef_prefix + head + (f_ef_txt + i_ef)

        return oc_report_text, ef_report_text, ct_alerts, flc_lv, flc_hv, isc_lv

    except Exception as e:
        return None, None, [f"ERROR:{e}"], None, None, None

def generate_tabulated_csv(oc_text, ef_text):
    """
    Recreate the CSV produced by ef.py.save_csv()
    Columns: ["EQUIPMENT","FAULT TYPE","STAGE","PICKUP (A)","RATIO (*In)","TMS/DELAY","TIME (s)"]
    We'll parse the report texts the same way ef.py.parse does.
    """
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["EQUIPMENT", "FAULT TYPE", "STAGE", "PICKUP (A)", "RATIO (*In)", "TMS/DELAY", "TIME (s)"])

    def parse(txt, label):
        curr = ""
        for line in txt.split('\n'):
            if ":" in line and "Load" in line:
                curr = line.split(":")[0]
            elif "- S" in line:
                p = line.split(":")
                stage = p[0].strip("- ")
                details = p[1].split(",")
                # pick_raw like " Pickup=xxxA (yy*In)"
                pick_raw = details[0].split("=")[1].strip()
                val = pick_raw.split("(")[0].strip()
                rat = pick_raw.split("(")[1].replace("*In)", "").strip()
                # tms
                tms = details[1].split("=")[1].strip() if len(details) > 1 else ""
                # op/time
                op = details[2].split("=")[1].strip() if len(details) > 2 else "0.0s"
                writer.writerow([curr, label, stage, val, rat, tms, op])

    parse(oc_text, "Overcurrent")
    parse(ef_text, "Earth Fault")
    return out.getvalue()

def generate_pdf_bytes(oc_text, ef_text):
    if not HAS_FPDF:
        return None
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Courier", size=10)
    t = oc_text + "\n" + ef_text
    for l in t.split('\n'):
        # FPDF cell width may need truncation; replicate ef.py which used Courier and cell(200,7)
        pdf.cell(200, 7, txt=l, ln=True)
    return pdf.output(dest='S').encode('latin-1')  # return bytes

# --- Sidebar / Controls (replicating the File menu) ---

st.sidebar.image("logo.png" if st.file_uploader is None and True else "logo.png", use_column_width=False) if False else None
# We will show the logo at top-left of main area instead.

st.sidebar.header("File")
if st.sidebar.button("Preload Default Data"):
    st.session_state['preload'] = True
if st.sidebar.button("Save Tabulated CSV"):
    st.session_state['_save_csv'] = True
if st.sidebar.button("Save PDF"):
    st.session_state['_save_pdf'] = True
if st.sidebar.button("Reset"):
    st.session_state['reset'] = True
# "Exit" — in web we can't close window; provide a clear-state action
if st.sidebar.button("Exit"):
    st.session_state.clear()
    st.experimental_rerun()

# --- Main layout: show logo and title similar to original ---

col_logo, col_title = st.columns([1,4])
with col_logo:
    try:
        img = Image.open("logo.png")
        st.image(img, width=140)
    except Exception:
        pass
with col_title:
    st.title("Nepal Electricity Authority (NEA) Grid Protection Coordination Tool")
    st.markdown("By Protection and Automation Division, GOD")

# Initialize session state variables to hold inputs, preserving values across reruns
if 'sys_vars' not in st.session_state:
    st.session_state['sys_vars'] = {'mva': '', 'hv': '', 'lv': '', 'z': '', 'cti': '', 'q4': '', 'q5': ''}
if 'num_feeders' not in st.session_state:
    st.session_state['num_feeders'] = 3
if 'feeders' not in st.session_state:
    st.session_state['feeders'] = [{'l': '0', 'ct': '0'} for _ in range(st.session_state['num_feeders'])]
if 'oc_text' not in st.session_state:
    st.session_state['oc_text'] = ""
if 'ef_text' not in st.session_state:
    st.session_state['ef_text'] = ""

# Handle Preload / Reset triggered from sidebar buttons
if st.session_state.get('preload', False):
    st.session_state['sys_vars'] = {"mva":"16.6", "hv":"33", "lv":"11", "z":"10", "cti":"150", "q4":"900", "q5":"300"}
    st.session_state['num_feeders'] = 3
    st.session_state['feeders'] = [{'l': '200', 'ct': '400'},{'l': '250', 'ct': '400'},{'l': '300', 'ct': '400'}]
    st.session_state['preload'] = False

if st.session_state.get('reset', False):
    st.session_state['sys_vars'] = {'mva': '', 'hv': '', 'lv': '', 'z': '', 'cti': '', 'q4': '', 'q5': ''}
    st.session_state['num_feeders'] = 0
    st.session_state['feeders'] = []
    st.session_state['oc_text'] = ""
    st.session_state['ef_text'] = ""
    st.session_state['reset'] = False

# --- Inputs area (replicating top_frame) ---
with st.form(key="inputs_form"):
    st.subheader("Transformer & System Data (Inputs)")
    cols = st.columns(7)
    keys = [("MVA","mva"), ("HV (kV)","hv"), ("LV (kV)","lv"), ("Z%","z"), ("CTI (ms)","cti"), ("Q4 CT","q4"), ("Q5 CT","q5")]
    for c, (label, key) in zip(cols, keys):
        with c:
            val = st.text_input(label, value=st.session_state['sys_vars'].get(key,""))
            st.session_state['sys_vars'][key] = val

    st.markdown("---")
    st.subheader("Feeder Configuration")
    cols_f = st.columns([1,3,1,3])
    with cols_f[0]:
        numf = st.number_input("No. of Feeders:", min_value=0, value=st.session_state['num_feeders'], step=1)
    st.session_state['num_feeders'] = int(numf)

    # adjust feeder list size
    if len(st.session_state['feeders']) < st.session_state['num_feeders']:
        for _ in range(st.session_state['num_feeders'] - len(st.session_state['feeders'])):
            st.session_state['feeders'].append({'l':'0','ct':'0'})
    elif len(st.session_state['feeders']) > st.session_state['num_feeders']:
        st.session_state['feeders'] = st.session_state['feeders'][:st.session_state['num_feeders']]

    # display feeders
    for i in range(st.session_state['num_feeders']):
        cols_row = st.columns([1,1,1,1,1,1])
        with cols_row[0]:
            st.markdown(f"**Q{i+1}**")
        with cols_row[1]:
            lval = st.text_input(f"Q{i+1} Load (A)", value=st.session_state['feeders'][i]['l'], key=f"l_{i}")
            st.session_state['feeders'][i]['l'] = lval
        with cols_row[2]:
            ctval = st.text_input(f"Q{i+1} CT Ratio", value=st.session_state['feeders'][i]['ct'], key=f"ct_{i}")
            st.session_state['feeders'][i]['ct'] = ctval

    submitted = st.form_submit_button("RUN CALCULATION")
    if submitted:
        oc_text, ef_text, ct_alerts, flc_lv, flc_hv, isc_lv = compute_reports(st.session_state['sys_vars'], st.session_state['feeders'])
        if oc_text is None and ct_alerts and ct_alerts[0] == "CTI_ERROR":
            st.warning("CTI must be greater than or equal to 120ms.")
        elif oc_text is None:
            st.error("Invalid inputs. Please check values.")
        else:
            st.session_state['oc_text'] = oc_text
            st.session_state['ef_text'] = ef_text
            st.success("Calculation completed.")

# Show total connected load (like total_load_display_var)
try:
    total_load_val = sum(float(fr['l'] or 0) for fr in st.session_state['feeders'])
except:
    total_load_val = 0.0
st.markdown(f"**Total Connected Load:** {round(total_load_val,2)} A")

# Display reports in tabs (replicating notebook)
tab1, tab2 = st.tabs(["Overcurrent (Phase)", "Earth Fault (Neutral)"])
with tab1:
    st.subheader("Overcurrent (Phase)")
    st.text_area("Report", value=st.session_state['oc_text'], height=300, key="oc_area")
    # Optionally allow copy
    st.download_button("Download Overcurrent Report (TXT)", data=st.session_state['oc_text'], file_name="overcurrent_report.txt")

with tab2:
    st.subheader("Earth Fault (Neutral)")
    st.text_area("Report", value=st.session_state['ef_text'], height=300, key="ef_area")
    st.download_button("Download Earth Fault Report (TXT)", data=st.session_state['ef_text'], file_name="earthfault_report.txt")

# Save Tabulated CSV (either via sidebar button or this area)
if st.session_state.get('_save_csv', False):
    oc_text = st.session_state['oc_text']
    ef_text = st.session_state['ef_text']
    csv_str = generate_tabulated_csv(oc_text, ef_text)
    st.session_state['_save_csv'] = False
    st.download_button("Download Tabulated CSV", data=csv_str, file_name="tabulated_report.csv", mime="text/csv")

# Save PDF
if st.session_state.get('_save_pdf', False):
    oc_text = st.session_state['oc_text']
    ef_text = st.session_state['ef_text']
    if not HAS_FPDF:
        st.error("FPDF package not available on server. Include fpdf in requirements to enable PDF export.")
        st.session_state['_save_pdf'] = False
    else:
        pdf_bytes = generate_pdf_bytes(oc_text, ef_text)
        st.session_state['_save_pdf'] = False
        if pdf_bytes:
            st.download_button("Download Report PDF", data=pdf_bytes, file_name="nea_report.pdf", mime="application/pdf")

# Provide direct download buttons in UI as well
csv_str_ui = generate_tabulated_csv(st.session_state['oc_text'], st.session_state['ef_text'])
st.download_button("Download Tabulated CSV", data=csv_str_ui, file_name="tabulated_report.csv", mime="text/csv")

if HAS_FPDF:
    pdf_bytes_ui = generate_pdf_bytes(st.session_state['oc_text'], st.session_state['ef_text'])
    if pdf_bytes_ui:
        st.download_button("Download Report PDF", data=pdf_bytes_ui, file_name="nea_report.pdf", mime="application/pdf")
else:
    st.info("PDF export requires fpdf in requirements.txt")

# Footer
st.markdown("---")
st.markdown("By Protection and Automation Division, GOD")
