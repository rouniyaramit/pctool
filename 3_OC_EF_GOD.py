import os
import math
import io
import csv
from typing import List, Optional, Tuple

import streamlit as st

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_PATH = os.path.join(BASE_DIR, "logo.jpg")

def safe_float(x) -> Optional[float]:
    try:
        s = str(x).strip()
        if s == "":
            return None
        return float(s)
    except Exception:
        return None

def default_state():
    # Same idea as preload_data in OC_EF_GOD.py (3 feeders default)
    return {
        "mva": "16.6",
        "hv": "33",
        "lv": "11",
        "z": "10",
        "cti": "150",
        "q4": "900",
        "q5": "300",
        "num_feeders": "3",
        "feeders": [
            {"load": "0", "ct": "0"},
            {"load": "0", "ct": "0"},
            {"load": "0", "ct": "0"},
        ],
    }

def calculate(state: dict) -> Tuple[str, str, List[str]]:
    alerts: List[str] = []

    cti_ms = float(state["cti"])
    if cti_ms < 120:
        raise ValueError("CTI must be greater than or equal to 120ms.")
    cti_s = cti_ms / 1000.0

    mva = float(state["mva"])
    hv_v = float(state["hv"])
    lv_v = float(state["lv"])
    z_pct = float(state["z"])
    q4_ct = float(state["q4"])
    q5_ct = float(state["q5"])

    flc_lv = round((mva * 1000) / (math.sqrt(3) * lv_v), 2)
    flc_hv = round((mva * 1000) / (math.sqrt(3) * hv_v), 2)
    isc_lv = round(flc_lv / (z_pct / 100), 2)
    if_lv = round(isc_lv * 0.9, 2)
    if_hv = round(if_lv / (hv_v / lv_v), 2)

    total_load, max_t_oc, max_t_ef = 0.0, 0.0, 0.0
    f_oc_txt, f_ef_txt = "", ""
    ct_alerts = []

    feeders = state["feeders"]

    for i, f in enumerate(feeders):
        l = float(f["load"])
        ct = float(f["ct"])
        total_load += l

        if ct < l:
            ct_alerts.append(f"ALERT: Feeder Q{i+1} CT ({ct}A) is less than Load ({l}A)\n")

        # OC
        p_oc = round(1.1 * l, 2)
        r1 = round(p_oc / ct, 2) if ct != 0 else 0.0
        t_oc = round(0.025 * (0.14 / (math.pow(max(1.05, if_lv / max(p_oc, 1e-9)), 0.02) - 1)), 3)
        max_t_oc = max(max_t_oc, t_oc)
        p2 = round(3 * l, 2)
        r2 = round(p2 / ct, 2) if ct != 0 else 0.0
        f_oc_txt += (
            f"FEEDER Q{i+1}: Load={l}A, CT={ct}\n"
            f" - S1 (IDMT): Pickup={p_oc}A ({r1}*In), TMS=0.025, Time={t_oc}s\n"
            f" - S2 (DT):   Pickup={p2}A ({r2}*In), Time=0.0s\n\n"
        )

        # EF
        p_ef = round(0.15 * l, 2)
        r_ef1 = round(p_ef / ct, 2) if ct != 0 else 0.0
        t_ef = round(0.025 * (0.14 / (math.pow(max(1.05, if_lv / max(p_ef, 1e-9)), 0.02) - 1)), 3)
        max_t_ef = max(max_t_ef, t_ef)
        p_ef2 = round(1.0 * l, 2)
        r_ef2 = round(p_ef2 / ct, 2) if ct != 0 else 0.0
        f_ef_txt += (
            f"FEEDER Q{i+1}: Load={l}A, CT={ct}\n"
            f" - S1 (IDMT): Pickup={p_ef}A ({r_ef1}*In), TMS=0.025, Time={t_ef}s\n"
            f" - S2 (DT):   Pickup={p_ef2}A ({r_ef2}*In), Time=0.0s\n\n"
        )

    hv_load = total_load / (hv_v / lv_v)

    if q4_ct < total_load:
        ct_alerts.append(f"ALERT: Q4 Incomer CT ({q4_ct}A) is less than Total Load ({total_load}A)\n")
    if q5_ct < hv_load:
        ct_alerts.append(f"ALERT: Q5 HV CT ({q5_ct}A) is less than HV Load ({round(hv_load,2)}A)\n")

    coord_data = [
        ("INCOMER Q4 (LV)", q4_ct, if_lv, 1, round(0.9 * isc_lv, 2), cti_ms, max_t_oc, max_t_ef),
        ("HV SIDE Q5 (HV)", q5_ct, if_hv, hv_v / lv_v, round(if_hv, 2), cti_ms * 2, max_t_oc + cti_s, max_t_ef + cti_s)
    ]

    i_oc, i_ef = "", ""
    for name, ct_v, fault, scale, s3, dt_ms, t_prev_oc, t_prev_ef in coord_data:
        l_cur = total_load / scale
        t_req_oc = round(t_prev_oc + cti_s, 3)
        t_req_ef = round(t_prev_ef + cti_s, 3)

        p_oc = round(1.1 * l_cur, 2)
        r1 = round(p_oc / ct_v, 2) if ct_v != 0 else 0.0
        tms_oc = round(t_req_oc / (0.14 / (math.pow(max(1.05, fault / max(p_oc, 1e-9)), 0.02) - 1)), 3)
        p2 = round(3 * l_cur, 2)
        r2 = round(p2 / ct_v, 2) if ct_v != 0 else 0.0
        r3 = round(s3 / ct_v, 2) if ct_v != 0 else 0.0
        i_oc += (
            f"{name}: Load={round(l_cur,2)}A, CT={ct_v}\n"
            f" - S1 (IDMT): Pickup={p_oc}A ({r1}*In), TMS={tms_oc}, Time={t_req_oc}s\n"
            f" - S2 (DT):   Pickup={p2}A ({r2}*In), Time={dt_ms/1000}s\n"
            f" - S3 (DT):   Pickup={s3}A ({r3}*In), Time=0.0s\n\n"
        )

        p_ef = round(0.15 * l_cur, 2)
        r_ef1 = round(p_ef / ct_v, 2) if ct_v != 0 else 0.0
        tms_ef = round(t_req_ef / (0.14 / (math.pow(max(1.05, fault / max(p_ef, 1e-9)), 0.02) - 1)), 3)
        p_ef2 = round(1.0 * l_cur, 2)
        r_ef2 = round(p_ef2 / ct_v, 2) if ct_v != 0 else 0.0
        r_ef3 = round(s3 / ct_v, 2) if ct_v != 0 else 0.0
        i_ef += (
            f"{name}: Load={round(l_cur,2)}A, CT={ct_v}\n"
            f" - S1 (IDMT): Pickup={p_ef}A ({r_ef1}*In), TMS={tms_ef}, Time={t_req_ef}s\n"
            f" - S2 (DT):   Pickup={p_ef2}A ({r_ef2}*In), Time={dt_ms/1000}s\n"
            f" - S3 (DT):   Pickup={s3}A ({r_ef3}*In), Time=0.0s\n\n"
        )

    head = f"FLC LV: {flc_lv}A | FLC HV: {flc_hv}A | Short Circuit: {isc_lv}A\n" + "=" * 60 + "\n"

    if total_load > flc_lv:
        alerts.append(f"CRITICAL ALERT: TRANSFORMER OVERLOAD ({total_load}A > {flc_lv}A)\n")
    alerts.extend(ct_alerts)

    oc_report = head + f_oc_txt + i_oc
    ef_report = head + f_ef_txt + i_ef
    return oc_report, ef_report, alerts


# ================== UI (Tkinter-like) ==================
st.set_page_config(page_title="Nepal Electricity Authority (NEA) Grid Protection Coordination Tool", layout="wide")

st.markdown(
    """
    <style>
      .block-container {padding-top: 10px;}
      .footer {color:#555; font-style:italic; font-size:14px; text-align:center; padding-top:10px;}
      .total {color:#d9534f; font-weight:800;}
    </style>
    """,
    unsafe_allow_html=True
)

if "grid_state" not in st.session_state:
    st.session_state.grid_state = default_state()
state = st.session_state.grid_state

st.title("Nepal Electricity Authority (NEA) Grid Protection Coordination Tool")

# Top frame with inputs + logo right (like Tkinter)
top_left, top_right = st.columns([6, 1])
with top_left:
    st.subheader("Transformer & System Data (Inputs)")

    params = [("MVA", "mva"), ("HV (kV)", "hv"), ("LV (kV)", "lv"), ("Z%", "z"), ("CTI (ms)", "cti"), ("Q4 CT", "q4"), ("Q5 CT", "q5")]
    cols = st.columns(len(params))
    for i, (lab, key) in enumerate(params):
        state[key] = cols[i].text_input(lab, value=state[key])
with top_right:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=90)

# "File menu" (like Tkinter menu bar)
with st.expander("File", expanded=False):
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        if st.button("Preload Default Data"):
            st.session_state.grid_state = default_state()
            st.rerun()
    with c2:
        st.caption("Save Tabulated CSV shown after RUN")
    with c3:
        st.caption("Save PDF (optional)")
    with c4:
        if st.button("Reset"):
            st.session_state.grid_state = {"mva":"","hv":"","lv":"","z":"","cti":"","q4":"","q5":"","num_feeders":"0","feeders":[]}
            st.rerun()
    with c5:
        st.caption("Exit: close browser tab")

st.subheader("Feeder Configuration")

# No. of feeders + Update Rows
ctrl1, ctrl2, ctrl3 = st.columns([1, 1, 4])
with ctrl1:
    state["num_feeders"] = ctrl1.text_input("No. of Feeders:", value=state["num_feeders"])
with ctrl2:
    update_rows = st.button("Update Rows")

# Update feeder rows like Tkinter Update Rows button
if update_rows:
    try:
        n = int(float(state["num_feeders"]))
        if n < 0:
            n = 0
    except Exception:
        n = 0
    state["feeders"] = state.get("feeders", [])
    while len(state["feeders"]) < n:
        state["feeders"].append({"load": "0", "ct": "0"})
    state["feeders"] = state["feeders"][:n]

# Feeder rows
feeders = state.get("feeders", [])
total_load = 0.0
for i in range(len(feeders)):
    row = feeders[i]
    r1, r2, r3, r4 = st.columns([1.2, 1, 1.2, 3])
    r1.write(f"Q{i+1} Load (A):")
    row["load"] = r2.text_input("", value=row["load"], key=f"load_{i}")
    r3.write("CT Ratio:")
    row["ct"] = r4.text_input("", value=row["ct"], key=f"ct_{i}")

    try:
        total_load += float(row["load"])
    except Exception:
        pass

st.markdown(f'<div class="total">Total Connected Load: {round(total_load,2)} A</div>', unsafe_allow_html=True)

# RUN button like Tkinter
run = st.button("RUN CALCULATION", type="primary", use_container_width=True)

if run:
    try:
        # Validate numeric first (like Tkinter behavior)
        required = ["mva","hv","lv","z","cti","q4","q5"]
        for k in required:
            float(state[k])  # raises if invalid
        for f in feeders:
            float(f["load"]); float(f["ct"])

        oc_report, ef_report, alerts = calculate(state)

        # Show RED_BOLD alerts
        if alerts:
            for a in alerts:
                st.error(a.strip())

        t1, t2 = st.tabs([" Overcurrent (Phase) ", " Earth Fault (Neutral) "])
        with t1:
            st.text_area("OC Report", value=oc_report, height=420)
        with t2:
            st.text_area("EF Report", value=ef_report, height=420)

        # Save CSV (tabulated) like Tkinter save_csv()
        csv_buf = io.StringIO()
        w = csv.writer(csv_buf)
        w.writerow(["EQUIPMENT", "FAULT TYPE", "STAGE", "PICKUP (A)", "RATIO (*In)", "TMS/DELAY", "TIME (s)"])

        def parse_and_write(txt: str, label: str):
            curr = ""
            for line in txt.split("\n"):
                if ":" in line and "Load" in line:
                    curr = line.split(":")[0]
                elif "- S" in line:
                    p = line.split(":")
                    stage = p[0].strip("- ").strip()
                    details = p[1].split(",")
                    pick_raw = details[0].split("=")[1].strip()
                    val = pick_raw.split("(")[0].strip()
                    rat = pick_raw.split("(")[1].replace("*In)", "").strip() if "(" in pick_raw else ""
                    tms = details[1].split("=")[1].strip() if len(details) > 1 else ""
                    op = details[2].split("=")[1].strip() if len(details) > 2 else "0.0s"
                    w.writerow([curr, label, stage, val, rat, tms, op])

        parse_and_write(oc_report, "Overcurrent")
        parse_and_write(ef_report, "Earth Fault")

        st.download_button("Save Tabulated CSV", data=csv_buf.getvalue().encode("utf-8"),
                           file_name="NEA_Tabulated_Report.csv", mime="text/csv")

    except Exception as e:
        st.error(f"Invalid Inputs: {e}")

st.markdown('<div class="footer">By Protection and Automation Division, GOD</div>', unsafe_allow_html=True)
