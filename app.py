# app.py - Streamlit protection coordination tool (robust, defensive)
import streamlit as st
import math
import csv
import io
from typing import List, Tuple, Optional

# Optional PDF support
try:
    from fpdf import FPDF
    HAS_FPDF = True
except Exception:
    HAS_FPDF = False

from PIL import Image, UnidentifiedImageError

st.set_page_config(page_title="NEA Protection Coordination Tool", layout="wide")

# ---------- Utility helpers ----------
def to_float(s, name="value", default=0.0) -> Tuple[float, Optional[str]]:
    """Convert s to float. Return (value, error_message_or_None)."""
    if s is None or (isinstance(s, str) and s.strip() == ""):
        return default, None
    try:
        return float(str(s).strip()), None
    except Exception:
        return default, f"Invalid numeric input for {name}: '{s}'"

def safe_div(a, b):
    try:
        return a / b
    except Exception:
        return 0.0

# ---------- Core calculation logic ----------
def compute_reports(sys_vars: dict, feeders: List[dict]) -> Tuple[Optional[str], Optional[str], List[str]]:
    """
    Compute Overcurrent and Earth-Fault reports.
    Returns (oc_text, ef_text, list_of_warnings_or_alerts).
    If a critical input error prevents calculation, oc_text and ef_text are None and warnings contains the error message.
    """
    warnings = []
    # parse main system vars
    mva, err = to_float(sys_vars.get("mva", ""), "MVA")
    if err: warnings.append(err)
    hv_kv, err = to_float(sys_vars.get("hv", ""), "HV kV")
    if err: warnings.append(err)
    lv_kv, err = to_float(sys_vars.get("lv", ""), "LV kV")
    if err: warnings.append(err)
    z_pct, err = to_float(sys_vars.get("z", ""), "Z%")
    if err: warnings.append(err)
    cti_ms, err = to_float(sys_vars.get("cti", ""), "CTI (ms)")
    if err: warnings.append(err)
    q4_ct, err = to_float(sys_vars.get("q4", ""), "Q4 CT")
    if err: warnings.append(err)
    q5_ct, err = to_float(sys_vars.get("q5", ""), "Q5 CT")
    if err: warnings.append(err)

    # quick validations
    if cti_ms < 120:
        return None, None, ["CTI must be >= 120 ms."]

    if mva <= 0 or hv_kv <= 0 or lv_kv <= 0:
        return None, None, ["MVA, HV kV and LV kV must be positive numbers."]

    # transformer full load currents
    try:
        flc_lv = round((mva * 1000) / (math.sqrt(3) * lv_kv), 2)
    except Exception:
        return None, None, ["Error computing FLC LV. Check MVA and LV inputs."]
    try:
        flc_hv = round((mva * 1000) / (math.sqrt(3) * hv_kv), 2)
    except Exception:
        flc_hv = 0.0

    isc_lv = round(safe_div(flc_lv, (z_pct / 100.0)) , 2) if z_pct > 0 else 0.0

    # collect feeder totals and per-feeder lines
    total_load = 0.0
    feeder_oc_lines = []
    feeder_ef_lines = []
    ct_alerts = []
    for idx, f in enumerate(feeders):
        label = f"Q{idx+1}"
        l, err = to_float(f.get("l", ""), f"{label} Load (A)", default=0.0)
        if err: warnings.append(err)
        ct, err = to_float(f.get("ct", ""), f"{label} CT Ratio", default=0.0)
        if err: warnings.append(err)
        total_load += l

        # Check CT ratio relative to load; warn but continue
        if ct <= 0:
            ct_alerts.append(f"{label}: CT ratio must be > 0 (got {ct}).")
        elif ct < l:
            ct_alerts.append(f"{label}: CT ratio ({ct}A) is less than load ({l}A).")

        # Overcurrent stage sizing (feeder)
        p_oc = round(1.1 * l, 2)
        r_oc = round(safe_div(p_oc, ct), 2) if ct > 0 else float("inf")
        t_oc = compute_idmt_time(ifault=0.9 * safe_div(flc_lv, (z_pct/100.0)) if z_pct>0 else 0, pickup=p_oc)
        feeder_oc_lines.append(f"{label}: Load={l}A, CT={ct}A\n - S1 (IDMT) Pickup={p_oc}A ({r_oc}*In), Time≈{t_oc}s\n - S2 (DT)   Pickup={round(3*l,2)}A, Time=0.0s\n")

        # Earth-fault stage sizing (feeder)
        p_ef = round(0.15 * l, 2)
        r_ef = round(safe_div(p_ef, ct), 2) if ct>0 else float("inf")
        t_ef = compute_idmt_time(ifault=0.9 * safe_div(flc_lv, (z_pct/100.0)) if z_pct>0 else 0, pickup=p_ef)
        feeder_ef_lines.append(f"{label}: Load={l}A, CT={ct}A\n - S1 (IDMT) Pickup={p_ef}A ({r_ef}*In), Time≈{t_ef}s\n - S2 (DT)   Pickup={round(1*l,2)}A, Time=0.0s\n")

    # transform LV/HV loads
    hv_load = safe_div(total_load, safe_div(hv_kv, lv_kv)) if hv_kv>0 and lv_kv>0 else 0.0
    if q5_ct < hv_load:
        ct_alerts.append(f"Q5 HV CT ({q5_ct}A) is less than HV-side transformed load ({round(hv_load,2)}A).")

    # Coordination for incomer Q4 (LV) and Q5 (HV)
    incomer_lines_oc = []
    incomer_lines_ef = []
    max_feeder_oc_time = max((extract_time_from_line(l) for l in feeder_oc_lines), default=0.0)
    max_feeder_ef_time = max((extract_time_from_line(l) for l in feeder_ef_lines), default=0.0)
    cti_s = cti_ms / 1000.0

    for name, ct_val, scale, dt_ms in [("INCOMER Q4 (LV)", q4_ct, 1.0, 0), ("HV SIDE Q5 (HV)", q5_ct, safe_div(hv_kv, lv_kv) if lv_kv>0 else 1.0, cti_ms)]:
        if ct_val <= 0:
            ct_alerts.append(f"{name}: CT ratio must be > 0 (got {ct_val}).")
        l_cur = safe_div(total_load, scale) if scale>0 else 0.0

        # Overcurrent incomer sizing
        p_oc = round(1.1 * l_cur, 2)
        r_oc = round(safe_div(p_oc, ct_val), 2) if ct_val>0 else float("inf")
        t_prev = max_feeder_oc_time
        t_req = round(t_prev + cti_s, 3)
        tms = compute_tms_for_required_time(pickup=p_oc, fault=safe_div(0.9*isc_lv,1) if isc_lv>0 else 0.0, required_time=t_req)
        incomer_lines_oc.append(f"{name}: Load={round(l_cur,2)}A, CT={ct_val}A\n - S1 (IDMT) Pickup={p_oc}A ({r_oc}*In), TMS={tms}, Time={t_req}s\n - S2 (DT)   Pickup={round(3*l_cur,2)}A, Time={round(dt_ms/1000,3)}s\n")

        # Earth-fault incomer sizing
        p_ef = round(0.15 * l_cur, 2)
        r_ef = round(safe_div(p_ef, ct_val), 2) if ct_val>0 else float("inf")
        t_prev_ef = max_feeder_ef_time
        t_req_ef = round(t_prev_ef + cti_s, 3)
        tms_ef = compute_tms_for_required_time(pickup=p_ef, fault=safe_div(0.9*isc_lv,1) if isc_lv>0 else 0.0, required_time=t_req_ef)
        incomer_lines_ef.append(f"{name}: Load={round(l_cur,2)}A, CT={ct_val}A\n - S1 (IDMT) Pickup={p_ef}A ({r_ef}*In), TMS={tms_ef}, Time={t_req_ef}s\n - S2 (DT)   Pickup={round(1*l_cur,2)}A, Time={round(dt_ms/1000,3)}s\n")

    # Build report texts
    header = f"Transformer FLC (LV)={flc_lv}A | FLC (HV)={flc_hv}A | Short-Circuit @ LV ≈ {isc_lv}A\n" + ("="*70) + "\n\n"
    oc_report = header + "FEEDER OVERCURRENT SETTINGS\n\n" + "\n".join(feeder_oc_lines) + "\nINCOMER SETTINGS\n\n" + "\n".join(incomer_lines_oc)
    ef_report = header + "FEEDER EARTH-FAULT SETTINGS\n\n" + "\n".join(feeder_ef_lines) + "\nINCOMER SETTINGS\n\n" + "\n".join(incomer_lines_ef)

    # overload alert
    if total_load > flc_lv:
        alert = f"CRITICAL: TRANSFORMER OVERLOAD: total connected load {round(total_load,2)}A > FLC LV {flc_lv}A"
        oc_report = alert + "\n\n" + oc_report
        ef_report = alert + "\n\n" + ef_report
        warnings.append(alert)

    # append CT/ratio alerts
    warnings.extend(ct_alerts)

    return oc_report, ef_report, warnings

def compute_idmt_time(ifault: float, pickup: float) -> float:
    """
    Approximate IDMT time using a form of the standard inverse-time formula.
    This is a conservative approximation to produce a consistent time number for display.
    """
    try:
        if pickup <= 0 or ifault <= 0:
            return 0.0
        m = max(1.05, safe_div(ifault, pickup))
        # Use a nominal formula that avoids domain errors
        val = 0.025 * (0.14 / (math.pow(m, 0.02) - 1.0))
        return round(val, 3) if val > 0 else 0.0
    except Exception:
        return 0.0

def compute_tms_for_required_time(pickup: float, fault: float, required_time: float) -> float:
    """
    Solve for TMS so that IDMT time * TMS ≈ required_time using same base curve.
    Output a TMS rounded to 3 decimals. If impossible, return 0.0
    """
    try:
        if pickup <= 0:
            return 0.0
        base = compute_idmt_time(ifault=fault, pickup=pickup)
        if base <= 0:
            return 0.0
        tms = safe_div(required_time, base)
        return round(tms, 3)
    except Exception:
        return 0.0

def extract_time_from_line(line: str) -> float:
    """Find 'Time≈X' or 'Time=Xs' in a line and return the numeric value. Fallback 0."""
    import re
    m = re.search(r"Time[≈=]\s*([0-9]*\.?[0-9]+)", line)
    if m:
        try:
            return float(m.group(1))
        except:
            return 0.0
    return 0.0

# ---------- Export helpers ----------
def generate_tabulated_csv(oc_text: str, ef_text: str) -> str:
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["EQUIPMENT", "FAULT TYPE", "STAGE", "PICKUP (A)", "RATIO (*In)", "TMS/DELAY", "TIME (s)"])

    def write_from_report(text: str, fault_label: str):
        if not text:
            return
        lines = text.splitlines()
        current_equipment = ""
        for ln in lines:
            ln = ln.strip()
            if ln.startswith("Q") and ":" in ln and "Load=" in ln:
                current_equipment = ln.split(":")[0].strip()
            elif ln.startswith("- S"):
                # try to parse "- S1 (IDMT) Pickup=123A (1.23*In), TMS=0.025, Time=0.123s"
                try:
                    stage = ln.split()[1]
                    # naive splits
                    parts = ln.split("Pickup=")
                    pickup_part = parts[1].split()[0].strip().strip(",")
                    pickup_val = pickup_part.replace("A", "")
                    # ratio
                    ratio = ""
                    if "(" in pickup_part and "*" in pickup_part:
                        ratio = pickup_part.split("(")[-1].replace(")","")
                    tms = ""
                    time = ""
                    if "TMS=" in ln:
                        tms = ln.split("TMS=")[1].split(",")[0].strip()
                    if "Time" in ln:
                        # Time=0.123s or Time≈0.123s
                        import re
                        m = re.search(r"Time[≈=]\s*([0-9]*\.?[0-9]+)", ln)
                        if m:
                            time = m.group(1)
                    writer.writerow([current_equipment, fault_label, stage, pickup_val, ratio, tms, time])
                except Exception:
                    continue

    write_from_report(oc_text or "", "Overcurrent")
    write_from_report(ef_text or "", "Earth Fault")
    return out.getvalue()

def generate_pdf_bytes(oc_text: str, ef_text: str) -> Optional[bytes]:
    if not HAS_FPDF:
        return None
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Courier", size=10)
    text = (oc_text or "") + "\n\n" + (ef_text or "")
    for row in text.splitlines():
        # ensure line fits, otherwise cell will wrap automatically with multi_cell
        pdf.multi_cell(0, 6, txt=row)
    return pdf.output(dest="S").encode("latin-1", errors="ignore")

# ---------- Session state initialization ----------
if "sys_vars" not in st.session_state:
    st.session_state.sys_vars = {"mva":"16.6","hv":"33","lv":"11","z":"10","cti":"150","q4":"900","q5":"300"}
if "num_feeders" not in st.session_state:
    st.session_state.num_feeders = 3
if "feeders" not in st.session_state:
    st.session_state.feeders = [{"l":"200","ct":"400"},{"l":"250","ct":"400"},{"l":"300","ct":"400"}]
if "oc_text" not in st.session_state:
    st.session_state.oc_text = ""
if "ef_text" not in st.session_state:
    st.session_state.ef_text = ""
if "warnings" not in st.session_state:
    st.session_state.warnings = []

# ---------- UI Layout ----------
st.title("NEA Protection Coordination Tool — Protection & Automation Division")

# top row: optional logo and quick actions
col1, col2 = st.columns([1,5])
with col1:
    try:
        logo = Image.open("logo.png")
        st.image(logo, width=140)
    except (FileNotFoundError, UnidentifiedImageError):
        # Missing logo is non-fatal
        st.write("")  # placeholder

with col2:
    st.subheader("Quick Actions")
    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        if st.button("Preload Default Data"):
            st.session_state.sys_vars = {"mva":"16.6","hv":"33","lv":"11","z":"10","cti":"150","q4":"900","q5":"300"}
            st.session_state.num_feeders = 3
            st.session_state.feeders = [{"l":"200","ct":"400"},{"l":"250","ct":"400"},{"l":"300","ct":"400"}]
            st.session_state.oc_text = ""
            st.session_state.ef_text = ""
            st.session_state.warnings = []
            st.experimental_rerun()
    with c2:
        if st.button("Reset All"):
            st.session_state.sys_vars = {"mva":"","hv":"","lv":"","z":"","cti":"","q4":"","q5":""}
            st.session_state.num_feeders = 0
            st.session_state.feeders = []
            st.session_state.oc_text = ""
            st.session_state.ef_text = ""
            st.session_state.warnings = []
            st.experimental_rerun()
    with c3:
        if st.button("Clear Reports"):
            st.session_state.oc_text = ""
            st.session_state.ef_text = ""
            st.session_state.warnings = []
            st.experimental_rerun()

st.markdown("---")

# Input form
with st.form("input_form"):
    st.subheader("Transformer & System Data (Inputs)")
    cols = st.columns(7)
    labels = [("MVA","mva"),("HV (kV)","hv"),("LV (kV)","lv"),("Z (%)","z"),("CTI (ms)","cti"),("Q4 CT (A)","q4"),("Q5 CT (A)","q5")]
    for col, (label,key) in zip(cols, labels):
        val = col.text_input(label, value=st.session_state.sys_vars.get(key,""))
        st.session_state.sys_vars[key] = val

    st.subheader("Feeder Configuration")
    nf = st.number_input("Number of feeders", min_value=0, value=st.session_state.num_feeders, step=1)
    st.session_state.num_feeders = int(nf)

    # adjust feeders list length
    if len(st.session_state.feeders) < st.session_state.num_feeders:
        for _ in range(st.session_state.num_feeders - len(st.session_state.feeders)):
            st.session_state.feeders.append({"l":"0","ct":"0"})
    elif len(st.session_state.feeders) > st.session_state.num_feeders:
        st.session_state.feeders = st.session_state.feeders[:st.session_state.num_feeders]

    # feeder input rows
    for i in range(st.session_state.num_feeders):
        r1, r2, r3 = st.columns([1,1,3])
        with r1:
            st.markdown(f"**Q{i+1}**")
        with r2:
            lval = st.text_input(f"Load (A) Q{i+1}", value=st.session_state.feeders[i].get("l",""), key=f"load_{i}")
            st.session_state.feeders[i]["l"] = lval
        with r3:
            ctval = st.text_input(f"CT Ratio (A) Q{i+1}", value=st.session_state.feeders[i].get("ct",""), key=f"ct_{i}")
            st.session_state.feeders[i]["ct"] = ctval

    run = st.form_submit_button("RUN CALCULATION")
    if run:
        oc_text, ef_text, warnings = compute_reports(dict(st.session_state.sys_vars), list(st.session_state.feeders))
        if oc_text is None and warnings:
            # show first critical warning
            st.error("Calculation failed: " + "; ".join(warnings))
            st.session_state.warnings = warnings
            st.session_state.oc_text = ""
            st.session_state.ef_text = ""
        else:
            st.success("Calculation completed.")
            st.session_state.oc_text = oc_text or ""
            st.session_state.ef_text = ef_text or ""
            st.session_state.warnings = warnings

# display total connected load
try:
    total_load = sum(float(f.get("l",0) or 0) for f in st.session_state.feeders)
except Exception:
    total_load = 0.0
st.markdown(f"**Total Connected Load:** {round(total_load,2)} A")

# display warnings (non-blocking)
if st.session_state.warnings:
    with st.expander("Warnings / Alerts (click to expand)"):
        for w in st.session_state.warnings:
            st.warning(w)

# report areas with download buttons
tab1, tab2, tab3 = st.tabs(["Overcurrent (Phase)", "Earth Fault (Neutral)", "Exports"])
with tab1:
    st.subheader("Overcurrent Report")
    st.text_area("Overcurrent Report", value=st.session_state.oc_text, height=320)
    st.download_button("Download Overcurrent TXT", data=st.session_state.oc_text or "","overcurrent_report.txt", mime="text/plain")

with tab2:
    st.subheader("Earth Fault Report")
    st.text_area("Earth Fault Report", value=st.session_state.ef_text, height=320)
    st.download_button("Download Earth Fault TXT", data=st.session_state.ef_text or "","earthfault_report.txt", mime="text/plain")

with tab3:
    st.subheader("Export / Save")
    csv_data = generate_tabulated_csv(st.session_state.oc_text, st.session_state.ef_text)
    st.download_button("Download Tabulated CSV", data=csv_data or "","tabulated_report.csv", mime="text/csv")
    if HAS_FPDF:
        pdf_bytes = generate_pdf_bytes(st.session_state.oc_text, st.session_state.ef_text)
        if pdf_bytes:
            st.download_button("Download PDF Report", data=pdf_bytes, file_name="nea_report.pdf", mime="application/pdf")
        else:
            st.info("PDF generation produced no content.")
    else:
        st.info("Install 'fpdf' to enable PDF export: pip install fpdf")

st.markdown("---")
st.markdown("By Protection & Automation Division — NEA")

# End of app
