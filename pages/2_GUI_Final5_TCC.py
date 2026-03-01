import io
import os
import csv
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# ---- Assets ----
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_PATH = os.path.join(BASE_DIR, "logo.png")
SLD_PATH  = os.path.join(BASE_DIR, "sld.png")

# ---- CTI (same values) ----
CTI_Q1_Q4 = 0.150
CTI_Q1_Q5 = 0.300
CTI_Q4_Q5 = 0.150

# ---- Tkinter Clone CSS ----
st.set_page_config(page_title="GUI Final5 TCC", layout="wide")
st.markdown("""
<style>
[data-testid="stSidebar"] {display:none !important;}
.block-container {padding-top: 6px !important; padding-left: 14px !important; padding-right: 14px !important;}
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
.tk_small {font-size: 13px; font-weight: 600;}
/* Compact inputs */
label {font-size: 13px !important; font-weight: 700 !important;}
div[data-testid="stVerticalBlock"] {gap: 0.35rem !important;}
/* Report text box like Tkinter Text widget (black) */
textarea {
    background:#000 !important;
    color:#fff !important;
    font-family: Consolas, monospace !important;
    font-size: 14px !important;
}
/* Bold buttons */
div.stButton > button {
    height: 38px !important;
    font-weight: 900 !important;
    border-radius: 6px !important;
}
</style>
""", unsafe_allow_html=True)

# ---- IEC curve (same) ----
def iec_curve(I: float, Ip: float, TMS: float, curve: str) -> float:
    if I <= Ip:
        return np.nan
    curves = {
        "Standard Inverse": (0.14, 0.02),
        "Very Inverse": (13.5, 1),
        "Extremely Inverse": (80, 2),
    }
    k, alpha = curves[curve]
    M = I / Ip
    return TMS * (k / ((M ** alpha) - 1))

def transformer_calculations(MVA: float, LV: float, HV: float, Z: float) -> Tuple[float, float, float]:
    flc_lv = (MVA * 1000) / (np.sqrt(3) * LV)
    isc_lv = flc_lv / (Z / 100)
    hv_factor = HV / LV
    return flc_lv, isc_lv, hv_factor

def safe_float(x) -> Optional[float]:
    try:
        s = str(x).strip()
        if s == "":
            return None
        return float(s)
    except Exception:
        return None

@dataclass
class RelayRow:
    idmt: bool
    pickup: float
    tms: float
    dt1: bool
    dt1_pickup: float
    dt1_time: float
    dt2: bool
    dt2_pickup: float
    dt2_time: float
    curve: str

def prefill_state():
    return {
        "mva": "16.6",
        "hv": "33",
        "lv": "11",
        "z": "10",
        "fault": "7900",
        "relays": [
            {"idmt": True, "pickup": 220, "tms": 0.025, "dt1": True, "dt1_pickup": 600, "dt1_time": 0.0, "dt2": True, "dt2_pickup": 0, "dt2_time": 0.0, "curve": "Standard Inverse"},
            {"idmt": True, "pickup": 275, "tms": 0.025, "dt1": True, "dt1_pickup": 750, "dt1_time": 0.0, "dt2": True, "dt2_pickup": 0, "dt2_time": 0.0, "curve": "Standard Inverse"},
            {"idmt": True, "pickup": 330, "tms": 0.025, "dt1": True, "dt1_pickup": 900, "dt1_time": 0.0, "dt2": True, "dt2_pickup": 0, "dt2_time": 0.0, "curve": "Standard Inverse"},
            {"idmt": True, "pickup": 825, "tms": 0.07,  "dt1": True, "dt1_pickup": 2250,"dt1_time": 0.15,"dt2": True, "dt2_pickup": 8000,"dt2_time": 0.0, "curve": "Standard Inverse"},
            {"idmt": True, "pickup": 275, "tms": 0.12,  "dt1": True, "dt1_pickup": 750, "dt1_time": 0.3, "dt2": True, "dt2_pickup": 2666.67,"dt2_time": 0.0, "curve": "Standard Inverse"},
        ],
    }

def new_project_state():
    return {
        "mva": "", "hv": "", "lv": "", "z": "", "fault": "",
        "relays": [
            {"idmt": False, "pickup": 0.0, "tms": 0.0, "dt1": False, "dt1_pickup": 0.0, "dt1_time": 0.0,
             "dt2": False, "dt2_pickup": 0.0, "dt2_time": 0.0, "curve": "Standard Inverse"}
            for _ in range(5)
        ],
    }

def build_report(trip_times: Dict[str, float], flc_lv: float, isc_lv: float, fault_used: Optional[float]) -> str:
    lines = []
    lines.append("Coordination Report")
    lines.append("=" * 20)
    lines.append(f"LV FLC: {flc_lv:.3f} A | LV Isc: {isc_lv:.3f} A")
    if fault_used is not None:
        lines.append(f"Fault Current: {fault_used:.3f} A")
    lines.append("")
    for q in sorted(trip_times.keys()):
        lines.append(f"{q} Trip: {trip_times[q]:.3f} s")
    lines.append("")
    lines.append("Coordination Results:")

    checks = [
        ("Q1", "Q4", CTI_Q1_Q4), ("Q2", "Q4", CTI_Q1_Q4), ("Q3", "Q4", CTI_Q1_Q4),
        ("Q1", "Q5", CTI_Q1_Q5), ("Q2", "Q5", CTI_Q1_Q5), ("Q3", "Q5", CTI_Q1_Q5),
        ("Q4", "Q5", CTI_Q4_Q5),
    ]
    for d, u, c in checks:
        if d in trip_times and u in trip_times:
            m = trip_times[u] - trip_times[d]
            lines.append(f"{d}->{u}: {m:.3f}s {'OK' if m >= c else 'NOT OK'}")
    return "\n".join(lines)

def plot_curves(relays: List[RelayRow], mva: float, hv: float, lv: float, z: float, fault_current: Optional[float]):
    currents = np.logspace(1, 5, 800)
    flc_lv, isc_lv, hv_factor = transformer_calculations(mva, lv, hv, z)

    fault_used = fault_current
    if fault_used is not None and fault_used > isc_lv:
        fault_used = isc_lv  # same cap behavior

    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111)
    ax.set_title("Time-Current Characteristics", fontsize=14, fontweight="bold")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Current (A)")
    ax.set_ylabel("Time (s)")
    ax.grid(True, which="both", linestyle="--", alpha=0.7)

    colors = ["blue", "green", "red", "purple", "orange"]
    trip_times: Dict[str, float] = {}

    for i in range(5):
        r = relays[i]
        scale = hv_factor if i == 4 else 1.0

        merged = []
        for I in currents:
            Is = I / scale
            times = []
            if r.idmt:
                t = iec_curve(Is, r.pickup, r.tms, r.curve)
                if not np.isnan(t):
                    times.append(t)
            if r.dt1 and Is >= r.dt1_pickup:
                times.append(r.dt1_time)
            if i >= 3 and r.dt2 and Is >= r.dt2_pickup:
                times.append(r.dt2_time)
            merged.append(min(times) if times else np.nan)

        merged = np.array(merged)
        ax.plot(currents, merged, color=colors[i], linewidth=2.5, label=f"Q{i+1}")

        if fault_used is not None:
            Isf = fault_used / scale
            cand = []

            if r.idmt:
                tf = iec_curve(Isf, r.pickup, r.tms, r.curve)
                if not np.isnan(tf):
                    cand.append(tf)
            if r.dt1 and Isf >= r.dt1_pickup:
                cand.append(r.dt1_time)
            if i >= 3 and r.dt2 and Isf >= r.dt2_pickup:
                cand.append(r.dt2_time)

            if cand:
                t_res = float(min(cand))
                trip_times[f"Q{i+1}"] = round(t_res, 3)
                ax.plot(fault_used, t_res, "o", color=colors[i])
                ax.text(fault_used, t_res, f"{t_res:.3f}s", fontsize=9)

    if fault_used is not None:
        ax.axvline(fault_used, linestyle="dotted", color="black", linewidth=2, label="Fault Level")

    ax.legend()
    fig.tight_layout()
    return fig, trip_times, flc_lv, isc_lv, fault_used


# ------------------- HEADER (Tkinter top region) -------------------
top = st.columns([6, 1.4], gap="small")
with top[0]:
    st.markdown("<div class='tk_header'>NEA Protection Coordination Tool (TCC)</div>", unsafe_allow_html=True)
with top[1]:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=95)

# Session state
if "tcc_state" not in st.session_state:
    st.session_state.tcc_state = prefill_state()
state = st.session_state.tcc_state

# "Menu" row like Tkinter File menu
m1, m2, m3, m4 = st.columns([1.1, 1.1, 1.4, 5.4], gap="small")
with m1:
    if st.button("New Project", use_container_width=True):
        st.session_state.tcc_state = new_project_state()
        st.rerun()
with m2:
    if st.button("Prefill Data", use_container_width=True):
        st.session_state.tcc_state = prefill_state()
        st.rerun()
with m3:
    run_plot = st.button("Plot Coordination", type="primary", use_container_width=True)

st.markdown("<hr style='margin:6px 0 10px 0;'>", unsafe_allow_html=True)

# ------------------- MAIN WINDOW (Left controls + Right plot/report) -------------------
left, right = st.columns([1.05, 1.55], gap="small")

# ---------- LEFT PANEL ----------
with left:
    st.markdown("<div class='tk_left'>", unsafe_allow_html=True)

    st.markdown("<div class='tk_small'>Transformer Data</div>", unsafe_allow_html=True)
    state["mva"] = st.text_input("Rating (MVA)", value=state["mva"])
    state["hv"]  = st.text_input("HV (kV)", value=state["hv"])
    state["lv"]  = st.text_input("LV (kV)", value=state["lv"])
    state["z"]   = st.text_input("Impedance (%)", value=state["z"])

    mva = safe_float(state["mva"])
    hv  = safe_float(state["hv"])
    lv  = safe_float(state["lv"])
    z   = safe_float(state["z"])

    flc_lv = isc_lv = None
    if None not in (mva, hv, lv, z):
        flc_lv, isc_lv, _ = transformer_calculations(mva, lv, hv, z)
        st.markdown(f"**FLC (LV) = {flc_lv:.3f} A**")
        st.markdown(f"**Isc (LV) = {isc_lv:.3f} A**")
    else:
        st.markdown("**FLC (LV) = -**")
        st.markdown("**Isc (LV) = -**")

    st.markdown("<div class='tk_small' style='margin-top:10px;'>Fault Data</div>", unsafe_allow_html=True)
    state["fault"] = st.text_input("Fault (A)", value=state["fault"])
    fault = safe_float(state["fault"])

    st.markdown("<div class='tk_small' style='margin-top:10px;'>Relay Settings</div>", unsafe_allow_html=True)

    headers = ["Relay","IDMT","Pick","TMS","DT1","P1","T1","DT2","P2","T2","Curve"]
    hc = st.columns([0.6,0.55,0.75,0.65,0.55,0.75,0.65,0.55,0.8,0.65,1.3], gap="small")
    for i,h in enumerate(headers):
        hc[i].markdown(f"**{h}**")

    curves = ["Standard Inverse", "Very Inverse", "Extremely Inverse"]
    relay_rows: List[RelayRow] = []

    for i in range(5):
        r = state["relays"][i]
        c = st.columns([0.6,0.55,0.75,0.65,0.55,0.75,0.65,0.55,0.8,0.65,1.3], gap="small")

        c[0].write(f"Q{i+1}")
        r["idmt"] = c[1].checkbox("", value=bool(r["idmt"]), key=f"idmt_{i}")
        r["pickup"] = c[2].number_input("", value=float(r["pickup"]), key=f"pick_{i}")
        r["tms"] = c[3].number_input("", value=float(r["tms"]), step=0.001, format="%.3f", key=f"tms_{i}")
        r["dt1"] = c[4].checkbox("", value=bool(r["dt1"]), key=f"dt1_{i}")
        r["dt1_pickup"] = c[5].number_input("", value=float(r["dt1_pickup"]), key=f"p1_{i}")
        r["dt1_time"] = c[6].number_input("", value=float(r["dt1_time"]), step=0.01, format="%.3f", key=f"t1_{i}")
        r["dt2"] = c[7].checkbox("", value=bool(r["dt2"]), key=f"dt2_{i}")
        r["dt2_pickup"] = c[8].number_input("", value=float(r["dt2_pickup"]), key=f"p2_{i}")
        r["dt2_time"] = c[9].number_input("", value=float(r["dt2_time"]), step=0.01, format="%.3f", key=f"t2_{i}")
        r["curve"] = c[10].selectbox("", curves, index=curves.index(r["curve"]) if r["curve"] in curves else 0, key=f"curve_{i}")

        relay_rows.append(
            RelayRow(
                idmt=bool(r["idmt"]),
                pickup=float(r["pickup"]),
                tms=float(r["tms"]),
                dt1=bool(r["dt1"]),
                dt1_pickup=float(r["dt1_pickup"]),
                dt1_time=float(r["dt1_time"]),
                dt2=bool(r["dt2"]),
                dt2_pickup=float(r["dt2_pickup"]),
                dt2_time=float(r["dt2_time"]),
                curve=str(r["curve"]),
            )
        )

    if os.path.exists(SLD_PATH):
        st.image(SLD_PATH, width=250)

    st.markdown("**Protection and Automation Division, GOD**")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------- RIGHT PANEL ----------
with right:
    st.markdown("<div class='tk_right'>", unsafe_allow_html=True)
    st.markdown("<div class='tk_small'>Plot + Report (same as right panel in Tkinter)</div>", unsafe_allow_html=True)

    if not run_plot:
        st.info("Click **Plot Coordination** to display the graph and report (same workflow as Tkinter).")
        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()

    if None in (mva, hv, lv, z):
        st.error("Transformer inputs invalid. Please enter numeric values.")
        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()

    flc, isc, _ = transformer_calculations(mva, lv, hv, z)
    if fault is not None and fault > isc:
        st.warning("Fault current exceeds LV short circuit current. It will be capped to Isc (same as Tkinter).")

    fig, trip_times, flc_lv2, isc_lv2, fault_used = plot_curves(relay_rows, mva, hv, lv, z, fault)
    st.pyplot(fig, clear_figure=True)

    report = build_report(trip_times, flc_lv2, isc_lv2, fault_used)
    st.text_area("Coordination Report", value=report, height=250)

    st.markdown("<hr style='margin:8px 0 8px 0;'>", unsafe_allow_html=True)
    st.markdown("<div class='tk_small'>Save / Export</div>", unsafe_allow_html=True)

    # PDF save (plot + report page)
    pdf_buf = io.BytesIO()
    with PdfPages(pdf_buf) as pdf:
        pdf.savefig(fig)
        fig_rep, ax = plt.subplots(figsize=(11, 8.5))
        ax.axis("off")
        ax.text(0.5, 0.95, "Relay Settings & Coordination Report", fontsize=16, weight="bold", ha="center")
        ax.text(0.05, 0.90, report, fontsize=10, family="monospace", va="top")
        pdf.savefig(fig_rep)
        plt.close(fig_rep)
    pdf_buf.seek(0)

    st.download_button("Save Report (PDF)", data=pdf_buf.getvalue(), file_name="NEA_TCC_Report.pdf", mime="application/pdf")

    # CSV export (Excel)
    csv_buf = io.StringIO()
    w = csv.writer(csv_buf)
    w.writerow(["Relay","IDMT","Pickup","TMS","DT1","P1","T1","DT2","P2","T2","Curve"])
    for i, rr in enumerate(relay_rows):
        w.writerow([f"Q{i+1}", int(rr.idmt), rr.pickup, rr.tms, int(rr.dt1), rr.dt1_pickup, rr.dt1_time,
                    int(rr.dt2), rr.dt2_pickup, rr.dt2_time, rr.curve])
    st.download_button("Export to Excel (CSV)", data=csv_buf.getvalue().encode("utf-8"),
                       file_name="NEA_TCC_Export.csv", mime="text/csv")

    st.markdown("</div>", unsafe_allow_html=True)
