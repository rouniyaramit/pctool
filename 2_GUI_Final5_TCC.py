import io
import os
import csv
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# ============ Paths ============
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_PATH = os.path.join(BASE_DIR, "logo.jpg")
SLD_PATH = os.path.join(BASE_DIR, "sld.png")

# ============ CTI VALUES (same) ============
CTI_Q1_Q4 = 0.150
CTI_Q1_Q5 = 0.300
CTI_Q4_Q5 = 0.150

# ============ IEC CURVE (same) ============
def iec_curve(I, Ip, TMS, curve):
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

def transformer_calculations(MVA: float, LV: float, HV: float, Z: float):
    FLC_LV = (MVA * 1000) / (np.sqrt(3) * LV)
    Isc_LV = FLC_LV / (Z / 100)
    HV_factor = HV / LV
    return FLC_LV, Isc_LV, HV_factor

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

def prefill_defaults_state():
    # EXACT defaults from GUI_Final5.py prefill_data()
    return {
        "mva": "16.6",
        "hv": "33",
        "lv": "11",
        "z": "10",
        "fault": "7900",
        "relays": [
            {"idmt": True, "pickup": 220, "tms": 0.025, "dt1": True, "dt1_pickup": 600, "dt1_time": 0.0,
             "dt2": True, "dt2_pickup": 0, "dt2_time": 0.0, "curve": "Standard Inverse"},
            {"idmt": True, "pickup": 275, "tms": 0.025, "dt1": True, "dt1_pickup": 750, "dt1_time": 0.0,
             "dt2": True, "dt2_pickup": 0, "dt2_time": 0.0, "curve": "Standard Inverse"},
            {"idmt": True, "pickup": 330, "tms": 0.025, "dt1": True, "dt1_pickup": 900, "dt1_time": 0.0,
             "dt2": True, "dt2_pickup": 0, "dt2_time": 0.0, "curve": "Standard Inverse"},
            {"idmt": True, "pickup": 825, "tms": 0.07, "dt1": True, "dt1_pickup": 2250, "dt1_time": 0.15,
             "dt2": True, "dt2_pickup": 8000, "dt2_time": 0.0, "curve": "Standard Inverse"},
            {"idmt": True, "pickup": 275, "tms": 0.12, "dt1": True, "dt1_pickup": 750, "dt1_time": 0.3,
             "dt2": True, "dt2_pickup": 2666.67, "dt2_time": 0.0, "curve": "Standard Inverse"},
        ],
    }

def new_project_state():
    # Matches Tkinter new_project(): clears all + disables checkboxes
    return {
        "mva": "",
        "hv": "",
        "lv": "",
        "z": "",
        "fault": "",
        "relays": [
            {"idmt": False, "pickup": 0.0, "tms": 0.0, "dt1": False, "dt1_pickup": 0.0, "dt1_time": 0.0,
             "dt2": False, "dt2_pickup": 0.0, "dt2_time": 0.0, "curve": "Standard Inverse"}
            for _ in range(5)
        ],
    }

def build_report(trip_times, FLC_LV, Isc_LV, fault_current):
    report = []
    report.append("Coordination Report")
    report.append("=" * 20)
    if FLC_LV is not None:
        report.append(f"LV FLC: {FLC_LV:.3f} A | LV Isc: {Isc_LV:.3f} A")
    if fault_current:
        report.append(f"Fault Current: {fault_current:.3f} A")
        report.append("")
    for q in sorted(trip_times.keys()):
        report.append(f"{q} Trip: {trip_times[q]:.3f} s")
    report.append("")
    report.append("Coordination Results:")
    checks = [
        ("Q1", "Q4", CTI_Q1_Q4), ("Q2", "Q4", CTI_Q1_Q4), ("Q3", "Q4", CTI_Q1_Q4),
        ("Q1", "Q5", CTI_Q1_Q5), ("Q2", "Q5", CTI_Q1_Q5), ("Q3", "Q5", CTI_Q1_Q5),
        ("Q4", "Q5", CTI_Q4_Q5),
    ]
    for d, u, c in checks:
        if d in trip_times and u in trip_times:
            m = trip_times[u] - trip_times[d]
            report.append(f"{d}->{u}: {m:.3f}s {'OK' if m >= c else 'NOT OK'}")
    return "\n".join(report)

def plot_curves(relays: List[RelayRow], MVA, HV, LV, Z, fault_current):
    currents = np.logspace(1, 5, 800)
    FLC_LV, Isc_LV, HV_factor = transformer_calculations(MVA, LV, HV, Z)

    # Tkinter warning + cap
    fault_used = fault_current
    if Isc_LV and fault_used and fault_used > Isc_LV:
        fault_used = Isc_LV

    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111)
    ax.set_title("Time-Current Characteristics", fontsize=14, fontweight="bold")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Current (A)", fontsize=12)
    ax.set_ylabel("Time (s)", fontsize=12)
    ax.grid(True, which="both", linestyle="--", alpha=0.7)

    trip_times: Dict[str, float] = {}
    colors = ["blue", "green", "red", "purple", "orange"]

    for i in range(5):
        r = relays[i]
        current_scaling = HV_factor if i == 4 else 1.0

        merged_curve = []
        for I in currents:
            I_scaled = I / current_scaling
            times = []
            if r.idmt:
                t_idmt = iec_curve(I_scaled, r.pickup, r.tms, r.curve)
                if not np.isnan(t_idmt):
                    times.append(t_idmt)
            if r.dt1:
                if I_scaled >= r.dt1_pickup:
                    times.append(r.dt1_time)
            if i >= 3 and r.dt2:
                if I_scaled >= r.dt2_pickup:
                    times.append(r.dt2_time)
            merged_curve.append(min(times) if times else np.nan)

        merged_curve = np.array(merged_curve)
        ax.plot(currents, merged_curve, color=colors[i], linewidth=2.5, label=f"Q{i+1}")

        if fault_used:
            I_fault_scaled = fault_used / current_scaling
            intersection_times = []

            if r.idmt:
                t_f = iec_curve(I_fault_scaled, r.pickup, r.tms, r.curve)
                if not np.isnan(t_f):
                    intersection_times.append(t_f)
            if r.dt1 and I_fault_scaled >= r.dt1_pickup:
                intersection_times.append(r.dt1_time)
            if i >= 3 and r.dt2 and I_fault_scaled >= r.dt2_pickup:
                intersection_times.append(r.dt2_time)

            if intersection_times:
                t_res = min(intersection_times)
                trip_times[f"Q{i+1}"] = round(t_res, 3)
                ax.plot(fault_used, t_res, "o", color=colors[i])
                ax.text(fault_used, t_res, f"{t_res:.3f}s", fontsize=9)

    if fault_used:
        ax.axvline(fault_used, linestyle="dotted", color="black", linewidth=2, label="Fault Level")

    ax.legend()
    fig.tight_layout()
    return fig, trip_times, FLC_LV, Isc_LV, fault_used


# ================== UI (Tkinter-like layout) ==================
st.set_page_config(page_title="NEA Protection Coordination Tool", layout="wide")

st.markdown(
    """
    <style>
      .block-container {padding-top: 10px;}
      .leftpane {
        background:#e6e6e6;
        border-radius:10px;
        padding:12px;
      }
      .rightpane {
        background:#ffffff;
        border-radius:10px;
        padding:12px;
      }
      /* Make a black report box like Tkinter Text widget */
      textarea[aria-label="Coordination Report Box"] {
        background: #000000 !important;
        color: #ffffff !important;
        font-family: Arial, sans-serif !important;
        font-size: 16px !important;
      }
      .reddev {color:red; font-weight:800;}
    </style>
    """,
    unsafe_allow_html=True
)

# Session state
if "tcc_state" not in st.session_state:
    st.session_state.tcc_state = prefill_defaults_state()

state = st.session_state.tcc_state

# ----- "Menu bar" replacement (File menu) -----
with st.expander("File", expanded=False):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("New Project (Reset All)"):
            st.session_state.tcc_state = new_project_state()
            st.rerun()
    with c2:
        if st.button("Prefill Defaults"):
            st.session_state.tcc_state = prefill_defaults_state()
            st.rerun()
    with c3:
        st.caption("Save Report (PDF) shown after plotting")
    with c4:
        st.caption("Export to Excel (CSV) shown after plotting")

# ----- Main two-panel layout like Tkinter -----
left, right = st.columns([1, 2.2], gap="large")

with left:
    st.markdown('<div class="leftpane">', unsafe_allow_html=True)

    # Top transformer frame + logo right (like Tkinter)
    top_tf, top_logo = st.columns([2, 1])
    with top_tf:
        st.subheader("Transformer Data")
        state["mva"] = st.text_input("Rating (MVA)", value=state["mva"])
        state["hv"] = st.text_input("HV (kV)", value=state["hv"])
        state["lv"] = st.text_input("LV (kV)", value=state["lv"])
        state["z"] = st.text_input("Impedance (%)", value=state["z"])
    with top_logo:
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=100)

    MVA = safe_float(state["mva"])
    HV = safe_float(state["hv"])
    LV = safe_float(state["lv"])
    Z = safe_float(state["z"])

    if None not in (MVA, HV, LV, Z):
        FLC_LV, Isc_LV, _ = transformer_calculations(MVA, LV, HV, Z)
        st.markdown(f"**FLC (LV) = {FLC_LV:.3f} A**", help="Same as Tkinter label_flc")
        st.markdown(f"**Isc (LV) = {Isc_LV:.3f} A**", help="Same as Tkinter label_isc")
    else:
        st.markdown("**FLC (LV) = -**")
        st.markdown("**Isc (LV) = -**")

    st.subheader("Fault Data")
    state["fault"] = st.text_input("Fault (A)", value=state["fault"])
    fault_current = safe_float(state["fault"])

    st.subheader("Relay Settings")
    headers = ["Relay", "IDMT", "Pick", "TMS", "DT1", "P1", "T1", "DT2", "P2", "T2", "Curve"]
    hcols = st.columns([0.7, 0.7, 0.8, 0.8, 0.7, 0.8, 0.8, 0.7, 0.9, 0.8, 1.4])
    for i, h in enumerate(headers):
        hcols[i].markdown(f"**{h}**")

    curves = ["Standard Inverse", "Very Inverse", "Extremely Inverse"]
    relay_rows: List[RelayRow] = []

    for i in range(5):
        r = state["relays"][i]
        cols = st.columns([0.7, 0.7, 0.8, 0.8, 0.7, 0.8, 0.8, 0.7, 0.9, 0.8, 1.4])

        cols[0].markdown(f"Q{i+1}")
        r["idmt"] = cols[1].checkbox("", value=bool(r["idmt"]), key=f"idmt_{i}")
        r["pickup"] = cols[2].number_input("", value=float(r["pickup"]), key=f"pick_{i}")
        r["tms"] = cols[3].number_input("", value=float(r["tms"]), step=0.001, format="%.3f", key=f"tms_{i}")
        r["dt1"] = cols[4].checkbox("", value=bool(r["dt1"]), key=f"dt1_{i}")
        r["dt1_pickup"] = cols[5].number_input("", value=float(r["dt1_pickup"]), key=f"p1_{i}")
        r["dt1_time"] = cols[6].number_input("", value=float(r["dt1_time"]), step=0.01, format="%.3f", key=f"t1_{i}")
        r["dt2"] = cols[7].checkbox("", value=bool(r["dt2"]), key=f"dt2_{i}")
        r["dt2_pickup"] = cols[8].number_input("", value=float(r["dt2_pickup"]), key=f"p2_{i}")
        r["dt2_time"] = cols[9].number_input("", value=float(r["dt2_time"]), step=0.01, format="%.3f", key=f"t2_{i}")
        r["curve"] = cols[10].selectbox("", curves, index=curves.index(r["curve"]) if r["curve"] in curves else 0, key=f"curve_{i}")

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

    run_plot = st.button("Plot Coordination", use_container_width=True)

    # SLD like Tkinter (left bottom)
    if os.path.exists(SLD_PATH):
        st.image(SLD_PATH, width=240)

    st.markdown('<div class="reddev">Protection and Automation Division, GOD</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="rightpane">', unsafe_allow_html=True)

    st.subheader("Plot + Report (same as right panel in Tkinter)")

    if run_plot:
        if None in (MVA, HV, LV, Z):
            st.error("Transformer inputs invalid (must be numeric).")
            st.stop()

        FLC_LV, Isc_LV, _ = transformer_calculations(MVA, LV, HV, Z)
        if Isc_LV and fault_current and fault_current > Isc_LV:
            st.warning("Warning: Fault current exceeds LV short circuit current. (Capped to Isc as Tkinter does.)")

        fig, trip_times, flc, isc, fault_used = plot_curves(relay_rows, MVA, HV, LV, Z, fault_current)
        st.pyplot(fig, clear_figure=True)

        report_text = build_report(trip_times, flc, isc, fault_used)

        # Black report box like Tkinter
        st.text_area("Coordination Report Box", value=report_text, height=260)

        # --- Save Report (PDF) + Export CSV buttons shown after plotting (like Tkinter menu items) ---
        st.divider()
        st.subheader("Save / Export")

        # PDF (plot + report table page like Tkinter save_pdf())
        pdf_buf = io.BytesIO()
        with PdfPages(pdf_buf) as pdf:
            pdf.savefig(fig)

            fig_rep, ax_rep = plt.subplots(figsize=(11, 8.5))
            ax_rep.axis("off")
            ax_rep.text(0.5, 0.95, "Relay Settings & Coordination Report", fontsize=16, weight="bold", ha="center")

            headers = ["Relay", "IDMT", "Pick", "TMS", "DT1", "P1", "T1", "DT2", "P2", "T2"]
            rows = []
            for i in range(5):
                rr = relay_rows[i]
                rows.append([
                    f"Q{i+1}",
                    "ON" if rr.idmt else "OFF",
                    f"{rr.pickup:.3f}",
                    f"{rr.tms:.3f}",
                    "ON" if rr.dt1 else "OFF",
                    f"{rr.dt1_pickup:.3f}",
                    f"{rr.dt1_time:.3f}",
                    "ON" if rr.dt2 else "OFF",
                    f"{rr.dt2_pickup:.3f}",
                    f"{rr.dt2_time:.3f}",
                ])

            table = ax_rep.table(
                cellText=rows,
                colLabels=headers,
                loc="center",
                cellLoc="center",
                bbox=[0.05, 0.5, 0.9, 0.35],
            )
            table.auto_set_font_size(False)
            table.set_fontsize(10)

            ax_rep.text(0.05, 0.45, "Results Summary:", fontsize=12, weight="bold")
            ax_rep.text(0.05, 0.43, report_text, fontsize=10, family="monospace", va="top")
            pdf.savefig(fig_rep)
            plt.close(fig_rep)

        pdf_buf.seek(0)
        st.download_button("Save Report (PDF)", data=pdf_buf.getvalue(), file_name="NEA_TCC_Report.pdf", mime="application/pdf")

        # CSV export (same columns as Tkinter export_to_excel())
        csv_buf = io.StringIO()
        writer = csv.writer(csv_buf)
        writer.writerow(["NEA PROTECTION TOOL REPORT"])
        writer.writerow([])
        writer.writerow(["--- Transformer Data ---"])
        writer.writerow(["Rating (MVA)", state["mva"]])
        writer.writerow(["HV Voltage (kV)", state["hv"]])
        writer.writerow(["LV Voltage (kV)", state["lv"]])
        writer.writerow(["Impedance (%)", state["z"]])
        writer.writerow(["FLC (LV)", f"FLC (LV) = {flc:.3f} A" if flc else "FLC = -"])
        writer.writerow(["Isc (LV)", f"Isc (LV) = {isc:.3f} A" if isc else "Isc = -"])
        writer.writerow([])
        writer.writerow(["--- Relay Settings ---"])
        writer.writerow(["Relay", "IDMT", "Pickup", "TMS", "DT1", "P1", "T1", "DT2", "P2", "T2", "Curve"])
        for i in range(5):
            rr = relay_rows[i]
            writer.writerow([
                f"Q{i+1}",
                int(rr.idmt),
                rr.pickup,
                rr.tms,
                int(rr.dt1),
                rr.dt1_pickup,
                rr.dt1_time,
                int(rr.dt2),
                rr.dt2_pickup,
                rr.dt2_time,
                rr.curve
            ])

        st.download_button("Export to Excel (CSV)", data=csv_buf.getvalue().encode("utf-8"),
                           file_name="NEA_TCC_Export.csv", mime="text/csv")

    else:
        st.info("Click **Plot Coordination** to display the graph and report (same workflow as Tkinter).")

    st.markdown("</div>", unsafe_allow_html=True)
