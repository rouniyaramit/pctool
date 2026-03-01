import os
import math
import io
import csv
from typing import List, Optional, Tuple

import streamlit as st

# ===================== Paths =====================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_PATH = os.path.join(BASE_DIR, "logo.png")

# ===================== Tkinter-Clone CSS =====================
st.set_page_config(
    page_title="Nepal Electricity Authority (NEA) Grid Protection Coordination Tool",
    layout="wide",
)

st.markdown(
    """
<style>
/* Hide Streamlit sidebar */
[data-testid="stSidebar"] {display:none !important;}

/* Tight paddings like Tkinter */
.block-container {
    padding-top: 6px !important;
    padding-left: 14px !important;
    padding-right: 14px !important;
    padding-bottom: 10px !important;
}

/* Reduce widget spacing */
div[data-testid="stVerticalBlock"] {gap: 0.35rem !important;}

/* Frames like Tkinter */
.tk_left {
    background:#e9e9e9;
    border:1px solid #c9c9c9;
    border-radius:10px;
    padding:12px;
}
.tk_right {
    background:#ffffff;
    border:1px solid #c9c9c9;
    border-radius:10px;
    padding:12px;
}
.tk_header {
    font-size: 22px;
    font-weight: 900;
}
.tk_small {
    font-size: 13px;
    font-weight: 800;
}

/* Compact label/input */
label {font-size: 13px !important; font-weight: 700 !important;}
input, textarea {font-size: 14px !important;}

/* Buttons */
div.stButton > button {
    height: 38px !important;
    font-weight: 900 !important;
    border-radius: 6px !important;
}

/* Report box style (similar to Tkinter text area) */
textarea {
    font-family: Consolas, monospace !important;
    font-size: 13.5px !important;
}

/* Alerts */
.alert_red {
    color:#b00020;
    font-weight: 900;
}

/* Small separator */
hr {margin: 6px 0 10px 0;}
</style>
""",
    unsafe_allow_html=True
)

# ===================== Helpers =====================
def safe_float(x) -> Optional[float]:
    try:
        s = str(x).strip()
        if s == "":
            return None
        return float(s)
    except Exception:
        return None

def default_state():
    # Default like your tool: 3 feeders ready
    return {
        "mva": "16.6",
        "hv": "33",
        "lv": "11",
        "z": "10",
        "cti": "150",
        "q4ct": "900",
        "q5ct": "300",
        "num_feeders": "3",
        "feeders": [
            {"load": "200", "ct": "400"},
            {"load": "250", "ct": "400"},
            {"load": "300", "ct": "400"},
        ],
        "last_oc": "",
        "last_ef": "",
        "last_alerts": [],
    }

def blank_state():
    return {
        "mva": "",
        "hv": "",
        "lv": "",
        "z": "",
        "cti": "",
        "q4ct": "",
        "q5ct": "",
        "num_feeders": "0",
        "feeders": [],
        "last_oc": "",
        "last_ef": "",
        "last_alerts": [],
    }

# ===================== Core Logic (same math) =====================
def calculate(state: dict) -> Tuple[str, str, List[str]]:
    alerts: List[str] = []

    cti_ms = safe_float(state["cti"])
    if cti_ms is None:
        raise ValueError("CTI (ms) is invalid.")
    if cti_ms < 120:
        raise ValueError("CTI must be >= 120ms.")

    mva = safe_float(state["mva"])
    hv_v = safe_float(state["hv"])
    lv_v = safe_float(state["lv"])
    z_pct = safe_float(state["z"])
    q4_ct = safe_float(state["q4ct"])
    q5_ct = safe_float(state["q5ct"])
    if None in (mva, hv_v, lv_v, z_pct, q4_ct, q5_ct):
        raise ValueError("Transformer/System inputs invalid.")

    cti_s = cti_ms / 1000.0

    flc_lv = round((mva * 1000) / (math.sqrt(3) * lv_v), 2)
    flc_hv = round((mva * 1000) / (math.sqrt(3) * hv_v), 2)
    isc_lv = round(flc_lv / (z_pct / 100), 2)
    if_lv = round(isc_lv * 0.9, 2)
    if_hv = round(if_lv / (hv_v / lv_v), 2)

    # feeders
    try:
        nfeed = int(float(state["num_feeders"]))
        if nfeed < 0:
            nfeed = 0
    except Exception:
        nfeed = 0

    feeders = state["feeders"][:nfeed]

    total_load = 0.0
    max_t_oc = 0.0
    max_t_ef = 0.0

    feeder_oc_txt = ""
    feeder_ef_txt = ""
    ct_alerts: List[str] = []

    for i, row in enumerate(feeders):
        l = safe_float(row.get("load", "")) or 0.0
        ct = safe_float(row.get("ct", "")) or 0.0
        total_load += l

        if ct < l:
            ct_alerts.append(f"ALERT: Feeder Q{i+1} CT ({ct}A) is less than Load ({l}A)")

        # -------- OC feeder --------
        p_oc = round(1.1 * l, 2)
        r1 = round(p_oc / ct, 2) if ct != 0 else float("inf")
        t_oc = round(0.025 * (0.14 / (math.pow(max(1.05, if_lv / max(p_oc, 1e-9)), 0.02) - 1)), 3)
        max_t_oc = max(max_t_oc, t_oc)

        p2 = round(3 * l, 2)
        r2 = round(p2 / ct, 2) if ct != 0 else float("inf")

        feeder_oc_txt += (
            f"FEEDER Q{i+1}: Load={l}A, CT={ct}\n"
            f" - S1 (IDMT): Pickup={p_oc}A ({r1}*In), TMS=0.025, Time={t_oc}s\n"
            f" - S2 (DT):   Pickup={p2}A ({r2}*In), Time=0.0s\n\n"
        )

        # -------- EF feeder --------
        p_ef = round(0.15 * l, 2)
        r_ef1 = round(p_ef / ct, 2) if ct != 0 else float("inf")
        t_ef = round(0.025 * (0.14 / (math.pow(max(1.05, if_lv / max(p_ef, 1e-9)), 0.02) - 1)), 3)
        max_t_ef = max(max_t_ef, t_ef)

        p_ef2 = round(1.0 * l, 2)
        r_ef2 = round(p_ef2 / ct, 2) if ct != 0 else float("inf")

        feeder_ef_txt += (
            f"FEEDER Q{i+1}: Load={l}A, CT={ct}\n"
            f" - S1 (IDMT): Pickup={p_ef}A ({r_ef1}*In), TMS=0.025, Time={t_ef}s\n"
            f" - S2 (DT):   Pickup={p_ef2}A ({r_ef2}*In), Time=0.0s\n\n"
        )

    # HV load
    hv_load = total_load / (hv_v / lv_v)

    if q4_ct < total_load:
        ct_alerts.append(f"ALERT: Q4 Incomer CT ({q4_ct}A) is less than Total Load ({total_load}A)")
    if q5_ct < hv_load:
        ct_alerts.append(f"ALERT: Q5 HV CT ({q5_ct}A) is less than HV Load ({round(hv_load,2)}A)")

    # Transformer overload
    if total_load > flc_lv:
        alerts.append(f"CRITICAL ALERT: TRANSFORMER OVERLOAD ({total_load}A > {flc_lv}A)")

    alerts.extend(ct_alerts)

    head = f"FLC LV: {flc_lv}A | FLC HV: {flc_hv}A | Short Circuit: {isc_lv}A\n" + "=" * 60 + "\n"

    # Incomer + HV coordination blocks
    coord_data = [
        ("INCOMER Q4 (LV)", q4_ct, if_lv, 1, round(0.9 * isc_lv, 2), cti_ms, max_t_oc, max_t_ef),
        ("HV SIDE Q5 (HV)", q5_ct, if_hv, hv_v / lv_v, round(if_hv, 2), cti_ms * 2, max_t_oc + cti_s, max_t_ef + cti_s),
    ]

    incomer_oc_txt = ""
    incomer_ef_txt = ""

    for name, ct_v, fault, scale, s3, dt_ms, t_prev_oc, t_prev_ef in coord_data:
        l_cur = total_load / scale

        t_req_oc = round(t_prev_oc + cti_s, 3)
        t_req_ef = round(t_prev_ef + cti_s, 3)

        # OC incomer
        p_oc = round(1.1 * l_cur, 2)
        r1 = round(p_oc / ct_v, 2) if ct_v != 0 else float("inf")
        tms_oc = round(t_req_oc / (0.14 / (math.pow(max(1.05, fault / max(p_oc, 1e-9)), 0.02) - 1)), 3)

        p2 = round(3 * l_cur, 2)
        r2 = round(p2 / ct_v, 2) if ct_v != 0 else float("inf")
        r3 = round(s3 / ct_v, 2) if ct_v != 0 else float("inf")

        incomer_oc_txt += (
            f"{name}: Load={round(l_cur,2)}A, CT={ct_v}\n"
            f" - S1 (IDMT): Pickup={p_oc}A ({r1}*In), TMS={tms_oc}, Time={t_req_oc}s\n"
            f" - S2 (DT):   Pickup={p2}A ({r2}*In), Time={dt_ms/1000}s\n"
            f" - S3 (DT):   Pickup={s3}A ({r3}*In), Time=0.0s\n\n"
        )

        # EF incomer
        p_ef = round(0.15 * l_cur, 2)
        r_ef1 = round(p_ef / ct_v, 2) if ct_v != 0 else float("inf")
        tms_ef = round(t_req_ef / (0.14 / (math.pow(max(1.05, fault / max(p_ef, 1e-9)), 0.02) - 1)), 3)

        p_ef2 = round(1.0 * l_cur, 2)
        r_ef2 = round(p_ef2 / ct_v, 2) if ct_v != 0 else float("inf")
        r_ef3 = round(s3 / ct_v, 2) if ct_v != 0 else float("inf")

        incomer_ef_txt += (
            f"{name}: Load={round(l_cur,2)}A, CT={ct_v}\n"
            f" - S1 (IDMT): Pickup={p_ef}A ({r_ef1}*In), TMS={tms_ef}, Time={t_req_ef}s\n"
            f" - S2 (DT):   Pickup={p_ef2}A ({r_ef2}*In), Time={dt_ms/1000}s\n"
            f" - S3 (DT):   Pickup={s3}A ({r_ef3}*In), Time=0.0s\n\n"
        )

    oc_report = head + feeder_oc_txt + incomer_oc_txt
    ef_report = head + feeder_ef_txt + incomer_ef_txt
    return oc_report, ef_report, alerts

# ===================== Session State =====================
if "grid_state" not in st.session_state:
    st.session_state.grid_state = default_state()

state = st.session_state.grid_state

# ===================== Header (Tkinter-like) =====================
top = st.columns([6.2, 1.0], gap="small")
with top[0]:
    st.markdown("<div class='tk_header'>Nepal Electricity Authority (NEA) Grid Protection Coordination Tool</div>", unsafe_allow_html=True)
with top[1]:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=95)

st.markdown("<hr>", unsafe_allow_html=True)

# ===================== Main Layout =====================
left, right = st.columns([1.05, 1.95], gap="small")

# -------- LEFT PANEL: Inputs + Feeder Table + Buttons --------
with left:
    st.markdown("<div class='tk_left'>", unsafe_allow_html=True)

    st.markdown("<div class='tk_small'>Transformer & System Data (Inputs)</div>", unsafe_allow_html=True)

    # compact 2-row grid like Tkinter style
    r1 = st.columns(3, gap="small")
    state["mva"] = r1[0].text_input("MVA", value=state["mva"])
    state["hv"]  = r1[1].text_input("HV (kV)", value=state["hv"])
    state["lv"]  = r1[2].text_input("LV (kV)", value=state["lv"])

    r2 = st.columns(3, gap="small")
    state["z"]    = r2[0].text_input("Z %", value=state["z"])
    state["cti"]  = r2[1].text_input("CTI (ms)", value=state["cti"])
    state["q4ct"] = r2[2].text_input("Q4 CT", value=state["q4ct"])

    r3 = st.columns(3, gap="small")
    state["q5ct"] = r3[0].text_input("Q5 CT", value=state["q5ct"])
    state["num_feeders"] = r3[1].text_input("No. of Feeders", value=state["num_feeders"])
    update_rows = r3[2].button("Update Rows", use_container_width=True)

    # Update feeder list length (Tkinter Update Rows)
    if update_rows:
        try:
            n = int(float(state["num_feeders"]))
            if n < 0:
                n = 0
        except Exception:
            n = 0

        feeders = state.get("feeders", [])
        while len(feeders) < n:
            feeders.append({"load": "0", "ct": "0"})
        feeders = feeders[:n]
        state["feeders"] = feeders
        st.session_state.grid_state = state
        st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<div class='tk_small'>Feeder Configuration</div>", unsafe_allow_html=True)

    # Ensure feeders list exists
    try:
        nfeed_now = int(float(state["num_feeders"]))
        if nfeed_now < 0:
            nfeed_now = 0
    except Exception:
        nfeed_now = 0

    feeders = state.get("feeders", [])
    while len(feeders) < nfeed_now:
        feeders.append({"load": "0", "ct": "0"})
    feeders = feeders[:nfeed_now]
    state["feeders"] = feeders

    # feeder table (compact)
    total_load = 0.0
    h = st.columns([0.55, 1.0, 1.0], gap="small")
    h[0].markdown("**Feeder**")
    h[1].markdown("**Load (A)**")
    h[2].markdown("**CT (A)**")

    for i in range(nfeed_now):
        row = feeders[i]
        c = st.columns([0.55, 1.0, 1.0], gap="small")
        c[0].write(f"Q{i+1}")
        row["load"] = c[1].text_input("", value=row.get("load", "0"), key=f"load_{i}")
        row["ct"]   = c[2].text_input("", value=row.get("ct", "0"), key=f"ct_{i}")

        total_load += safe_float(row["load"]) or 0.0

    st.markdown(f"<div class='alert_red'>Total Connected Load: {round(total_load,2)} A</div>", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # Buttons row like Tkinter
    b = st.columns([1.15, 1.15, 1.7], gap="small")
    preload = b[0].button("Preload Default Data", use_container_width=True)
    reset   = b[1].button("Reset", use_container_width=True)
    run     = b[2].button("RUN CALCULATION", type="primary", use_container_width=True)

    if preload:
        st.session_state.grid_state = default_state()
        st.rerun()

    if reset:
        st.session_state.grid_state = blank_state()
        st.rerun()

    st.markdown("**By Protection and Automation Division, GOD**")
    st.markdown("</div>", unsafe_allow_html=True)

# -------- RIGHT PANEL: Reports side-by-side (OC | EF) --------
with right:
    st.markdown("<div class='tk_right'>", unsafe_allow_html=True)
    st.markdown("<div class='tk_small'>Reports (Side-by-side like Tkinter)</div>", unsafe_allow_html=True)

    # Alerts at top of right panel
    if state.get("last_alerts"):
        for a in state["last_alerts"]:
            st.error(a)

    # When run, compute and store reports
    if "run" in locals() and run:
        try:
            oc_report, ef_report, alerts = calculate(state)
            state["last_oc"] = oc_report
            state["last_ef"] = ef_report
            state["last_alerts"] = alerts
            st.session_state.grid_state = state
            st.rerun()
        except Exception as e:
            st.error(f"Invalid Inputs: {e}")

    # Side-by-side text areas
    rcols = st.columns(2, gap="small")
    with rcols[0]:
        st.markdown("**Overcurrent (Phase)**")
        st.text_area("", value=state.get("last_oc", ""), height=540, key="oc_box")
    with rcols[1]:
        st.markdown("**Earth Fault (Neutral)**")
        st.text_area("", value=state.get("last_ef", ""), height=540, key="ef_box")

    st.markdown("<hr>", unsafe_allow_html=True)

    # Download Tabulated CSV (like Tkinter save_csv)
    def make_tabulated_csv(oc_text: str, ef_text: str) -> bytes:
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["EQUIPMENT", "FAULT TYPE", "STAGE", "PICKUP (A)", "RATIO (*In)", "TMS/DELAY", "TIME (s)"])

        def parse_report(text: str, fault_type: str):
            curr_equipment = ""
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue

                # Detect equipment line: "FEEDER Q1: ..." or "INCOMER Q4 (LV): ..."
                if ":" in line and ("FEEDER" in line or "INCOMER" in line or "HV SIDE" in line):
                    curr_equipment = line.split(":")[0].strip()

                # Detect stage line: "- S1 (IDMT): Pickup=..., ..."
                if line.startswith("- S"):
                    # Stage name (before colon)
                    stage = line.split(":")[0].replace("-", "").strip()
                    # After colon
                    rhs = line.split(":", 1)[1].strip()

                    # Try extract Pickup=xxxA (ratio)
                    pickup_val = ""
                    ratio_val = ""
                    tms_delay = ""
                    time_val = ""

                    parts = [p.strip() for p in rhs.split(",")]

                    # Pickup
                    for p in parts:
                        if p.startswith("Pickup="):
                            pickup_raw = p.split("=", 1)[1].strip()  # "123A (0.3*In)"
                            if "(" in pickup_raw and "*)" not in pickup_raw:
                                pickup_val = pickup_raw.split("(")[0].replace("A", "").strip()
                                ratio_val = pickup_raw.split("(")[1].replace(")", "").replace("*In", "").strip()
                            else:
                                pickup_val = pickup_raw.replace("A", "").strip()

                        if p.startswith("TMS=") or "TMS=" in p:
                            tms_delay = p.split("=", 1)[1].strip()

                        if p.startswith("Time=") or "Time=" in p:
                            time_val = p.split("=", 1)[1].replace("s", "").strip()

                    w.writerow([curr_equipment, fault_type, stage, pickup_val, ratio_val, tms_delay, time_val])

        if oc_text:
            parse_report(oc_text, "Overcurrent")
        if ef_text:
            parse_report(ef_text, "Earth Fault")

        return buf.getvalue().encode("utf-8")

    oc_text = state.get("last_oc", "")
    ef_text = state.get("last_ef", "")
    if oc_text or ef_text:
        st.download_button(
            "Save Tabulated CSV",
            data=make_tabulated_csv(oc_text, ef_text),
            file_name="NEA_Tabulated_Report.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.info("Run calculation to enable CSV export.")

    st.markdown("</div>", unsafe_allow_html=True)
