# app.py - Streamlit port of ef.py (fixed Preload/Reset/Save flows)
import streamlit as st
import math
import csv
import io
from PIL import Image

# Optional: fpdf for PDF export (same dependency as ef.py)
try:
    from fpdf import FPDF
    HAS_FPDF = True
except Exception:
    HAS_FPDF = False

st.set_page_config(page_title="NEA Protection Coordination Tool", layout="wide")

# --- Calculation logic (identical to ef.py) ---
def compute_reports(sys_vars, feeder_rows):
    try:
        cti_ms = float(sys_vars.get('cti', '') or 0)
        if cti_ms < 120:
            return None, None, ["CTI_ERROR"], None, None, None

        mva = float(sys_vars.get('mva', '') or 0)
        hv_v = float(sys_vars.get('hv', '') or 0)
        lv_v = float(sys_vars.get('lv', '') or 0)
        z_pct = float(sys_vars.get('z', '') or 0)
        q4_ct = float(sys_vars.get('q4', '') or 0)
        q5_ct = float(sys_vars.get('q5', '') or 0)
        cti_s = cti_ms / 1000.0

        flc_lv = round((mva * 1000) / (math.sqrt(3) * lv_v), 2) if lv_v != 0 else 0.0
        flc_hv = round((mva * 1000) / (math.sqrt(3) * hv_v), 2) if hv_v != 0 else 0.0
        isc_lv = round(flc_lv / (z_pct / 100), 2) if z_pct != 0 else 0.0
        if_lv = round(isc_lv * 0.9, 2)
        if_hv = round(if_lv / (hv_v / lv_v), 2) if (hv_v != 0 and lv_v != 0) else 0.0

        total_load = 0.0
        max_t_oc = 0.0
        max_t_ef = 0.0
        f_oc_txt = ""
        f_ef_txt = ""
        ct_alerts = []

        for i, fr in enumerate(feeder_rows):
            try:
                l = float(fr.get('l', '') or 0)
            except:
                raise ValueError(f"Invalid feeder load at Q{i+1}")
            try:
                ct = float(fr.get('ct', '') or 0)
            except:
                raise ValueError(f"Invalid feeder CT at Q{i+1}")

            total_load += l
            if ct < l:
                ct_alerts.append(f"ALERT: Feeder Q{i+1} CT ({ct}A) is less than Load ({l}A)\n")

            p_oc = round(1.1 * l, 2)
            r1 = round(p_oc/ct, 2) if ct != 0 else float('inf')
            t_oc = round(0.025 * (0.14 / (math.pow(max(1.05, if_lv/p_oc), 0.02) - 1)), 3) if p_oc != 0 else 0.0
            max_t_oc = max(max_t_oc, t_oc)
            p2 = round(3*l, 2)
            r2 = round(p2/ct, 2) if ct != 0 else float('inf')
            f_oc_txt += f"FEEDER Q{i+1}: Load={l}A, CT={ct}\n - S1 (IDMT): Pickup={p_oc}A ({r1}*In), TMS=0.025, Time={t_oc}s\n - S2 (DT):   Pickup={p2}A ({r2}*In), Time=0.0s\n\n"

            p_ef = round(0.15 * l, 2)
            r_ef1 = round(p_ef/ct, 2) if ct != 0 else float('inf')
            t_ef = round(0.025 * (0.14 / (math.pow(max(1.05, if_lv/p_ef), 0.02) - 1)), 3) if p_ef != 0 else 0.0
            max_t_ef = max(max_t_ef, t_ef)
            p_ef2 = round(1.0*l, 2)
            r_ef2 = round(p_ef2/ct, 2) if ct != 0 else float('inf')
            f_ef_txt += f"FEEDER Q{i+1}: Load={l}A, CT={ct}\n - S1 (IDMT): Pickup={p_ef}A ({r_ef1}*In), TMS=0.025, Time={t_ef}s\n - S2 (DT):   Pickup={p_ef2}A ({r_ef2}*In), Time=0.0s\n\n"

        hv_load = total_load / (hv_v / lv_v) if (hv_v != 0 and lv_v != 0) else 0.0

        if q5_ct < hv_load:
            ct_alerts.append(f"ALERT: Q5 HV CT ({q5_ct}A) is less than HV Load ({round(hv_load,2)}A)\n")

        coord_data = [
            ("INCOMER Q4 (LV)", q4_ct, if_lv, 1, round(0.9*isc_lv,2), cti_ms, max_t_oc, max_t_ef),
            ("HV SIDE Q5 (HV)", q5_ct, if_hv, hv_v/lv_v if lv_v != 0 else 0.0, round(if_hv,2), cti_ms*2, max_t_oc+cti_s, max_t_ef+cti_s)
        ]

        i_oc = ""
        i_ef = ""
        for name, ct_v, fault, scale, s3, dt_ms, t_prev_oc, t_prev_ef in coord_data:
            l_cur = total_load / scale if scale != 0 else 0.0
            t_req_oc = round(t_prev_oc + cti_s, 3)
            t_req_ef = round(t_prev_ef + cti_s, 3)
            p_oc = round(1.1 * l_cur, 2)
            r1 = round(p_oc/ct_v, 2) if ct_v != 0 else float('inf')
            denom_oc = (0.14 / (math.pow(max(1.05, fault/p_oc), 0.02) - 1)) if p_oc != 0 else 1.0
            tms_oc = round(t_req_oc / denom_oc, 3) if denom_oc != 0 else 0.0
            p2 = round(3*l_cur, 2)
            r2 = round(p2/ct_v, 2) if ct_v != 0 else float('inf')
            r3 = round(s3/ct_v, 2) if ct_v != 0 else float('inf')
            i_oc += f"{name}: Load={round(l_cur,2)}A, CT={ct_v}\n - S1 (IDMT): Pickup={p_oc}A ({r1}*In), TMS={tms_oc}, Time={t_req_oc}s\n - S2 (DT):   Pickup={p2}A ({r2}*In), Time={dt_ms/1000}s\n - S3 (DT):   Pickup={s3}A ({r3}*In), Time=0.0s\n\n"

            p_ef = round(0.15 * l_cur, 2)
            r_ef1 = round(p_ef/ct_v, 2) if ct_v != 0 else float('inf')
            denom_ef = (0.14 / (math.pow(max(1.05, fault/p_ef), 0.02) - 1)) if p_ef != 0 else 1.0
            tms_ef = round(t_req_ef / denom_ef, 3) if denom_ef != 0 else 0.0
            p_ef2 = round(1.0*l_cur, 2)
            r_ef2 = round(p_ef2/ct_v, 2) if ct_v != 0 else float('inf')
            r_ef3 = round(s3/ct_v, 2) if ct_v != 0 else float('inf')
            i_ef += f"{name}: Load={round(l_cur,2)}A, CT={ct_v}\n - S1 (IDMT): Pickup={p_ef}A ({r_ef1}*In), TMS={tms_ef}, Time={t_req_ef}s\n - S2 (DT):   Pickup={p_ef2}A ({r_ef2}*In), Time={dt_ms/1000}s\n - S3 (DT):   Pickup={s3}A ({r_ef3}*In), Time=0.0s\n\n"

        head = f"FLC LV: {flc_lv}A | FLC HV: {flc_hv}A | Short Circuit: {isc_lv}A\n" + "="*60 + "\n"

        oc_prefix = ""
        ef_prefix = ""
        if total_load > flc_lv:
            oc_prefix += f"CRITICAL ALERT: TRANSFORMER OVERLOAD ({total_load}A > {flc_lv}A)\n"
            ef_prefix += f"CRITICAL ALERT: TRANSFORMER OVERLOAD ({total_load}A > {flc_lv}A)\n"

        for alert in ct_alerts:
            oc_prefix += alert
            ef_prefix += alert

        oc_report_text = oc_prefix + head + (f_oc_txt + i_oc)
        ef_report_text = ef_prefix + head + (f_ef_txt + i_ef)

        return oc_report_text, ef_report_text, ct_alerts, flc_lv, flc_hv, isc_lv

    except Exception as e:
        return None, None, [f"ERROR:{e}"], None, None, None

# CSV generation identical to ef.py.save_csv parsing
def generate_tabulated_csv(oc_text, ef_text):
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
                pick_raw = details[0].split("=")[1].strip()
                val = pick_raw.split("(")[0].strip()
                rat = pick_raw.split("(")[1].replace("*In)", "").strip()
                tms = details[1].split("=")[1].strip() if len(details) > 1 else ""
                op = details[2].split("=")[1].strip() if len(details) > 2 else "0.0s"
                writer.writerow([curr, label, stage, val, rat, tms, op])

    parse(oc_text or "", "Overcurrent")
    parse(ef_text or "", "Earth Fault")
    return out.getvalue()

def generate_pdf_bytes(oc_text, ef_text):
    if not HAS_FPDF:
        return None
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Courier", size=10)
    t = (oc_text or "") + "\n" + (ef_text or "")
    for l in t.split('\n'):
        pdf.cell(200, 7, txt=l, ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- App state & UI ---

# Initialize session state
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

# Sidebar: use explicit buttons that set flags or perform actions safely
st.sidebar.header("File")
if st.sidebar.button("Preload Default Data (Set)"):
    st.session_state['sys_vars'] = {"mva":"16.6", "hv":"33", "lv":"11", "z":"10", "cti":"150", "q4":"900", "q5":"300"}
    st.session_state['num_feeders'] = 3
    st.session_state['feeders'] = [{'l': '200', 'ct': '400'},{'l': '250', 'ct': '400'},{'l': '300', 'ct': '400'}]
    st.session_state['oc_text'] = ""
    st.session_state['ef_text'] = ""
    st.experimental_rerun()

if st.sidebar.button("Reset (Clear)"):
    st.session_state['sys_vars'] = {'mva': '', 'hv': '', 'lv': '', 'z': '', 'cti': '', 'q4': '', 'q5': ''}
    st.session_state['num_feeders'] = 0
    st.session_state['feeders'] = []
    st.session_state['oc_text'] = ""
    st.session_state['ef_text'] = ""
    st.experimental_rerun()

# For downloads, generate data and expose download buttons (no immediate action from sidebar buttons)
st.sidebar.markdown("### Save / Export")
csv_data_for_download = generate_tabulated_csv(st.session_state.get('oc_text', ""), st.session_state.get('ef_text', ""))
st.sidebar.download_button("Download Tabulated CSV", data=csv_data_for_download, file_name="tabulated_report.csv", mime="text/csv")

if HAS_FPDF:
    pdf_bytes_for_download = generate_pdf_bytes(st.session_state.get('oc_text', ""), st.session_state.get('ef_text', ""))
    if pdf_bytes_for_download:
        st.sidebar.download_button("Download PDF", data=pdf_bytes_for_download, file_name="nea_report.pdf", mime="application/pdf")
else:
    st.sidebar.info("PDF export requires 'fpdf' in requirements.txt")

if st.sidebar.button("Exit (Clear Session)"):
    st.session_state.clear()
    st.experimental_rerun()

# Main header & logo
col_logo, col_title = st.columns([1,6])
with col_logo:
    try:
        img = Image.open("logo.png")
        st.image(img, width=140)
    except Exception:
        pass
with col_title:
    st.title("Nepal Electricity Authority (NEA) Grid Protection Coordination Tool")
    st.markdown("By Protection and Automation Division, GOD")

# Inputs form
with st.form("inputs"):
    st.subheader("Transformer & System Data (Inputs)")
    cols = st.columns(7)
    keys = [("MVA","mva"), ("HV (kV)","hv"), ("LV (kV)","lv"), ("Z%","z"), ("CTI (ms)","cti"), ("Q4 CT","q4"), ("Q5 CT","q5")]
    for c, (label, key) in zip(cols, keys):
        with c:
            val = st.text_input(label, value=st.session_state['sys_vars'].get(key,""))
            st.session_state['sys_vars'][key] = val

    st.subheader("Feeder Configuration")
    numf = st.number_input("No. of Feeders:", min_value=0, value=st.session_state['num_feeders'], step=1)
    st.session_state['num_feeders'] = int(numf)

    # Resize feeders
    if len(st.session_state['feeders']) < st.session_state['num_feeders']:
        for _ in range(st.session_state['num_feeders'] - len(st.session_state['feeders'])):
            st.session_state['feeders'].append({'l':'0','ct':'0'})
    elif len(st.session_state['feeders']) > st.session_state['num_feeders']:
        st.session_state['feeders'] = st.session_state['feeders'][:st.session_state['num_feeders']]

    # Feeder rows
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

    run = st.form_submit_button("RUN CALCULATION")
    if run:
        oc_text, ef_text, ct_alerts, flc_lv, flc_hv, isc_lv = compute_reports(st.session_state['sys_vars'], st.session_state['feeders'])
        if oc_text is None and ct_alerts and ct_alerts[0] == "CTI_ERROR":
            st.warning("CTI must be greater than or equal to 120ms.")
        elif oc_text is None:
            st.error("Invalid Inputs: please check values.")
        else:
            st.session_state['oc_text'] = oc_text
            st.session_state['ef_text'] = ef_text
            st.success("Calculation completed.")

# Total connected load display
try:
    total_load_val = sum(float(fr['l'] or 0) for fr in st.session_state['feeders'])
except:
    total_load_val = 0.0
st.markdown(f"**Total Connected Load:** {round(total_load_val,2)} A")

# Reports tabs
tab1, tab2 = st.tabs(["Overcurrent (Phase)", "Earth Fault (Neutral)"])
with tab1:
    st.subheader("Overcurrent (Phase)")
    st.text_area("Report", value=st.session_state.get('oc_text', ""), height=300)
    st.download_button("Download Overcurrent Report (TXT)", data=st.session_state.get('oc_text', ""), file_name="overcurrent_report.txt")

with tab2:
    st.subheader("Earth Fault (Neutral)")
    st.text_area("Report", value=st.session_state.get('ef_text', ""), height=300)
    st.download_button("Download Earth Fault Report (TXT)", data=st.session_state.get('ef_text', ""), file_name="earthfault_report.txt")

st.markdown("---")
st.markdown("By Protection and Automation Division, GOD")
