import os
import io
import csv
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# =========================
# CONFIG (per-page)
# =========================
st.set_page_config(page_title="NEA Protection Coordination Tool (TCC)", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))         # .../pages
ROOT_DIR = os.path.dirname(BASE_DIR)                          # repo root
LOGO_PATH = os.path.join(ROOT_DIR, "logo.jpg")
SLD_PATH = os.path.join(ROOT_DIR, "sld.png")

# =========================
# CONSTANTS (same as Tkinter)
# =========================
CTI_Q1_Q4 = 0.150
CTI_Q1_Q5 = 0.300
CTI_Q4_Q5 = 0.150

CURVES = ["Standard Inverse", "Very Inverse", "Extremely Inverse"]

# =========================
# CSS: Tkinter clone look
# =========================
st.markdown(
    """
<style>
/* Hide Streamlit chrome inside the app */
#MainMenu {display:none !important;}
header {display:none !important;}
footer {display:none !important;}
[data-testid="stSidebar"] {display:none !important;}
[data-testid="stToolbar"] {display:none !important;}
[data-testid="stDecoration"] {display:none !important;}

/* Backgrounds like Tkinter */
html, body, [data-testid="stAppViewContainer"] { background: #e6e6e6 !important; }
.block-container { padding-top: 8px !important; padding-bottom: 10px !important; }

/* Panels */
.leftPanel {
    background:#e6e6e6;
    padding: 10px 12px;
    border-radius: 6px;
}
.rightPanel {
    background:#ffffff;
    padding: 10px 12px;
    border-radius: 6px;
    border: 1px solid #d0d0d0;
}

/* LabelFrame clone */
.lf {
    border: 1px solid #bcbcbc;
    border-radius: 6px;
    padding: 10px 10px 8px 10px;
    margin-bottom: 10px;
    background: #f2f2f2;
}
.lfTitle {
    font-weight: 800;
    font-size: 14px;
    margin: -2px 0 8px 0;
}

/* Report box like Tkinter (black background, white text) */
.reportBox {
    background:#000000;
    color:#ffffff;
    padding: 10px;
    border-radius: 6px;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    white-space: pre-wrap;
    line-height: 1.35;
    border: 1px solid #202020;
}
.ok { color: #2ecc71; font-weight: 800; }
.bad { color: #ff4d4d; font-weight: 800; }

/* Make Streamlit inputs tighter like a grid */
div[data-testid="stNumberInput"] input,
div[data-testid="stTextInput"] input {
    height: 36px !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# =========================
# STATE (same as Tkinter fields)
# =========================
def _init_state():
    if "tcc_inited" in st.session_state:
        return

    st.session_state.t_mva = "16.6"
    st.session_state.t_hv = "33"
    st.session_state.t_lv = "11"
    st.session_state.t_z = "10"
    st.session_state.fault_a = "7900"

    # 5 relays: Q1..Q5
    st.session_state.relays = []
    defaults = [
        [220, 0.025, 600, 0.0, 0, 0.0],
        [275, 0.025, 750, 0.0, 0, 0.0],
        [330, 0.025, 900, 0.0, 0, 0.0],
        [825, 0.07, 2250, 0.15, 8000, 0.0],
        [275, 0.12, 750, 0.3, 2666.67, 0.0],
    ]
    for i in range(5):
        st.session_state.relays.append(
            {
                "idmt": False,
                "pick": str(defaults[i][0]),
                "tms": str(defaults[i][1]),
                "dt1": False,
                "p1": str(defaults[i][2]),
                "t1": str(defaults[i][3]),
                "dt2": False,
                "p2": str(defaults[i][4]),
                "t2": str(defaults[i][5]),
                "curve": "Standard Inverse",
            }
        )

    st.session_state.last_plot = None   # (fig, report_text, trip_times, flc, isc, fault_used)
    st.session_state.tcc_inited = True


def new_project_reset():
    st.session_state.t_mva = ""
    st.session_state.t_hv = ""
    st.session_state.t_lv = ""
    st.session_state.t_z = ""
    st.session_state.fault_a = ""
    for i in range(5):
        r = st.session_state.relays[i]
        r["idmt"] = False
        r["dt1"] = False
        r["dt2"] = False
        r["pick"] = ""
        r["tms"] = ""
        r["p1"] = ""
        r["t1"] = ""
        r["p2"] = ""
        r["t2"] = ""
        r["curve"] = "Standard Inverse"
    st.session_state.last_plot = None


def prefill_defaults():
    st.session_state.t_mva = "16.6"
    st.session_state.t_hv = "33"
    st.session_state.t_lv = "11"
    st.session_state.t_z = "10"
    st.session_state.fault_a = "7900"

    defaults = [
        [220, 0.025, 600, 0.0, 0, 0.0],
        [275, 0.025, 750, 0.0, 0, 0.0],
        [330, 0.025, 900, 0.0, 0, 0.0],
        [825, 0.07, 2250, 0.15, 8000, 0.0],
        [275, 0.12, 750, 0.3, 2666.67, 0.0],
    ]
    for i in range(5):
        r = st.session_state.relays[i]
        r["pick"] = str(defaults[i][0])
        r["tms"] = str(defaults[i][1])
        r["p1"] = str(defaults[i][2])
        r["t1"] = str(defaults[i][3])
        r["p2"] = str(defaults[i][4])
        r["t2"] = str(defaults[i][5])


_init_state()

# =========================
# LOGIC (same as Tkinter)
# =========================
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


def transformer_calculations():
    try:
        MVA = float(st.session_state.t_mva)
        LV = float(st.session_state.t_lv)
        HV = float(st.session_state.t_hv)
        Z = float(st.session_state.t_z)
        FLC_LV = (MVA * 1000) / (np.sqrt(3) * LV)
        Isc_LV = FLC_LV / (Z / 100)
        HV_factor = HV / LV
        return FLC_LV, Isc_LV, HV_factor
    except Exception:
        return None, None, 1


def build_report(trip_times, FLC_LV, Isc_LV, fault_current):
    lines = []
    lines.append("Coordination Report")
    lines.append("=" * 20)
    if FLC_LV:
        lines.append(f"LV FLC: {FLC_LV:.3f} A | LV Isc: {Isc_LV:.3f} A")
    if fault_current:
        lines.append(f"Fault Current: {fault_current:.3f} A")
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

    # HTML-ish report for Streamlit (to keep green/red)
    html_lines = []
    html_lines.append("Coordination Report\n" + "=" * 20 + "\n")
    if FLC_LV:
        html_lines.append(f"LV FLC: {FLC_LV:.3f} A | LV Isc: {Isc_LV:.3f} A\n")
    if fault_current:
        html_lines.append(f"Fault Current: {fault_current:.3f} A\n\n")
    for q in sorted(trip_times.keys()):
        html_lines.append(f"{q} Trip: {trip_times[q]:.3f} s\n")
    html_lines.append("\nCoordination Results:\n")

    for d, u, c in checks:
        if d in trip_times and u in trip_times:
            m = trip_times[u] - trip_times[d]
            ok = m >= c
            tag = "ok" if ok else "bad"
            html_lines.append(f"{d}->{u}: {m:.3f}s <span class='{tag}'>{'OK' if ok else 'NOT OK'}</span>\n")

    # plain text (for PDF/CSV)
    for d, u, c in checks:
        if d in trip_times and u in trip_times:
            m = trip_times[u] - trip_times[d]
            lines.append(f"{d}->{u}: {m:.3f}s {'OK' if m >= c else 'NOT OK'}")

    return "\n".join(lines), "".join(html_lines)


def plot_curves_and_report():
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111)

    ax.set_title("Time-Current Characteristics", fontsize=14, fontweight="bold")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Current (A)", fontsize=12)
    ax.set_ylabel("Time (s)", fontsize=12)
    ax.grid(True, which="both", linestyle="--", alpha=0.7)

    currents = np.logspace(1, 5, 800)
    FLC_LV, Isc_LV, HV_factor = transformer_calculations()

    # fault current
    try:
        fault_current = float(st.session_state.fault_a)
    except Exception:
        fault_current = None

    # clamp fault to Isc (same warning logic; Streamlit shows warning)
    fault_used = fault_current
    if Isc_LV and fault_current and fault_current > Isc_LV:
        st.warning("Warning: Fault current exceeds LV short circuit current. It has been limited to LV Isc.")
        fault_used = Isc_LV

    trip_times = {}
    colors = ["blue", "green", "red", "purple", "orange"]

    for i in range(5):
        r = st.session_state.relays[i]
        # required numeric fields
        try:
            Ip = float(r["pick"])
            TMS = float(r["tms"])
            curve = r["curve"]
        except Exception:
            continue

        current_scaling = HV_factor if i == 4 else 1
        merged_curve = []

        for I in currents:
            I_scaled = I / current_scaling
            times = []

            # IDMT
            if r["idmt"]:
                t_idmt = iec_curve(I_scaled, Ip, TMS, curve)
                if not np.isnan(t_idmt):
                    times.append(t_idmt)

            # DT1
            if r["dt1"]:
                try:
                    if I_scaled >= float(r["p1"]):
                        times.append(float(r["t1"]))
                except Exception:
                    pass

            # DT2 (only for Q4/Q5 in your Tkinter: i >= 3)
            if i >= 3 and r["dt2"]:
                try:
                    if I_scaled >= float(r["p2"]):
                        times.append(float(r["t2"]))
                except Exception:
                    pass

            merged_curve.append(min(times) if times else np.nan)

        merged_curve = np.array(merged_curve)
        ax.plot(currents, merged_curve, color=colors[i], linewidth=2.5, label=f"Q{i+1}")

        # intersection at fault
        if fault_used:
            I_fault_scaled = fault_used / current_scaling
            intersection_times = []

            if r["idmt"]:
                t_f = iec_curve(I_fault_scaled, Ip, TMS, curve)
                if not np.isnan(t_f):
                    intersection_times.append(t_f)

            if r["dt1"]:
                try:
                    if I_fault_scaled >= float(r["p1"]):
                        intersection_times.append(float(r["t1"]))
                except Exception:
                    pass

            if i >= 3 and r["dt2"]:
                try:
                    if I_fault_scaled >= float(r["p2"]):
                        intersection_times.append(float(r["t2"]))
                except Exception:
                    pass

            if intersection_times:
                t_res = min(intersection_times)
                trip_times[f"Q{i+1}"] = round(float(t_res), 3)
                ax.plot(fault_used, t_res, "o", color=colors[i])
                ax.text(fault_used, t_res, f"{t_res:.3f}s", fontsize=9)

    if fault_used:
        ax.axvline(fault_used, linestyle="dotted", color="black", linewidth=2, label="Fault Level")

    ax.legend()

    report_plain, report_html = build_report(trip_times, FLC_LV, Isc_LV, fault_used)
    return fig, report_plain, report_html, trip_times, FLC_LV, Isc_LV, fault_used


def make_pdf_bytes(fig, report_plain):
    # Create PDF in memory (no file dialog in Streamlit)
    buf = io.BytesIO()
    with PdfPages(buf) as pdf:
        pdf.savefig(fig)

        fig_rep, ax_rep = plt.subplots(figsize=(11, 8.5))
        ax_rep.axis("off")
        ax_rep.text(
            0.5, 0.95, "Relay Settings & Coordination Report",
            fontsize=16, weight="bold", ha="center"
        )

        headers = ["Relay", "IDMT", "Pick", "TMS", "DT1", "P1", "T1", "DT2", "P2", "T2", "Curve"]
        rows = []
        for i in range(5):
            r = st.session_state.relays[i]
            rows.append([
                f"Q{i+1}",
                "ON" if r["idmt"] else "OFF",
                f"{float(r['pick']):.3f}" if r["pick"] else "",
                f"{float(r['tms']):.3f}" if r["tms"] else "",
                "ON" if r["dt1"] else "OFF",
                f"{float(r['p1']):.3f}" if r["p1"] else "",
                f"{float(r['t1']):.3f}" if r["t1"] else "",
                "ON" if r["dt2"] else "OFF",
                f"{float(r['p2']):.3f}" if r["p2"] else "",
                f"{float(r['t2']):.3f}" if r["t2"] else "",
                r["curve"],
            ])

        table = ax_rep.table(
            cellText=rows,
            colLabels=headers,
            loc="upper center",
            cellLoc="center",
            colLoc="center",
        )
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 1.3)

        # report text
        ax_rep.text(0.02, 0.25, report_plain, fontsize=10, family="monospace", va="top")
        pdf.savefig(fig_rep)
        plt.close(fig_rep)

    buf.seek(0)
    return buf.getvalue()


def make_csv_bytes():
    buf = io.StringIO()
    writer = csv.writer(buf)

    writer.writerow(["NEA PROTECTION TOOL REPORT"])
    writer.writerow([])
    writer.writerow(["--- Transformer Data ---"])
    writer.writerow(["Rating (MVA)", st.session_state.t_mva])
    writer.writerow(["HV Voltage (kV)", st.session_state.t_hv])
    writer.writerow(["LV Voltage (kV)", st.session_state.t_lv])
    writer.writerow(["Impedance (%)", st.session_state.t_z])

    flc, isc, _ = transformer_calculations()
    writer.writerow(["FLC (LV)", f"{flc:.3f} A" if flc else "-"])
    writer.writerow(["Isc (LV)", f"{isc:.3f} A" if isc else "-"])
    writer.writerow([])
    writer.writerow(["--- Relay Settings ---"])
    writer.writerow(["Relay", "IDMT", "Pickup", "TMS", "DT1", "P1", "T1", "DT2", "P2", "T2", "Curve"])

    for i in range(5):
        r = st.session_state.relays[i]
        writer.writerow([
            f"Q{i+1}",
            1 if r["idmt"] else 0,
            r["pick"],
            r["tms"],
            1 if r["dt1"] else 0,
            r["p1"],
            r["t1"],
            1 if r["dt2"] else 0,
            r["p2"],
            r["t2"],
            r["curve"],
        ])

    return buf.getvalue().encode("utf-8")


# =========================
# "FILE MENU" (Tkinter-like)
# =========================
menu_c1, menu_c2, menu_c3, menu_c4, menu_c5, menu_c6 = st.columns([1.8, 1.8, 1.8, 2.2, 2.2, 6])
with menu_c1:
    if st.button("New Project (Reset All)", use_container_width=True):
        new_project_reset()
        st.rerun()
with menu_c2:
    if st.button("Prefill Defaults", use_container_width=True):
        prefill_defaults()
        st.rerun()
with menu_c3:
    plot_clicked = st.button("Plot Coordination", type="primary", use_container_width=True)
with menu_c4:
    save_pdf_clicked = st.button("Save Report (PDF)", use_container_width=True)
with menu_c5:
    export_csv_clicked = st.button("Export to Excel (CSV)", use_container_width=True)

st.write("")

# =========================
# MAIN LAYOUT (Tkinter: left gray, right white)
# =========================
left_col, right_col = st.columns([1.05, 2.2], gap="large")

# -------- LEFT PANEL --------
with left_col:
    st.markdown("<div class='leftPanel'>", unsafe_allow_html=True)

    # Transformer Data + Logo (same line)
    topL, topR = st.columns([3.2, 1])
    with topL:
        st.markdown("<div class='lf'><div class='lfTitle'>Transformer Data</div>", unsafe_allow_html=True)

        st.session_state.t_mva = st.text_input("Rating (MVA)", value=st.session_state.t_mva)
        st.session_state.t_hv = st.text_input("HV (kV)", value=st.session_state.t_hv)
        st.session_state.t_lv = st.text_input("LV (kV)", value=st.session_state.t_lv)
        st.session_state.t_z = st.text_input("Impedance (%)", value=st.session_state.t_z)

        flc, isc, _ = transformer_calculations()
        st.markdown(f"<b>FLC (LV) = {flc:.3f} A</b>" if flc else "<b>FLC (LV) = -</b>", unsafe_allow_html=True)
        st.markdown(f"<b>Isc (LV) = {isc:.3f} A</b>" if isc else "<b>Isc (LV) = -</b>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with topR:
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=110)

    # Fault Data
    st.markdown("<div class='lf'><div class='lfTitle'>Fault Data</div>", unsafe_allow_html=True)
    st.session_state.fault_a = st.text_input("Fault (A)", value=st.session_state.fault_a)
    st.markdown("</div>", unsafe_allow_html=True)

    # Relay Settings (grid like Tkinter)
    st.markdown("<div class='lf'><div class='lfTitle'>Relay Settings</div>", unsafe_allow_html=True)

    hdr = st.columns([0.9, 0.9, 1.0, 1.0, 0.9, 1.0, 1.0, 0.9, 1.2, 1.0, 1.6])
    headers = ["Relay", "IDMT", "Pick", "TMS", "DT1", "P1", "T1", "DT2", "P2", "T2", "Curve"]
    for c, h in zip(hdr, headers):
        c.markdown(f"**{h}**")

    for i in range(5):
        r = st.session_state.relays[i]
        row = st.columns([0.9, 0.9, 1.0, 1.0, 0.9, 1.0, 1.0, 0.9, 1.2, 1.0, 1.6])

        row[0].markdown(f"**Q{i+1}**")
        r["idmt"] = row[1].checkbox("", value=r["idmt"], key=f"idmt_{i}")
        r["pick"] = row[2].text_input("", value=r["pick"], key=f"pick_{i}")
        r["tms"] = row[3].text_input("", value=r["tms"], key=f"tms_{i}")
        r["dt1"] = row[4].checkbox("", value=r["dt1"], key=f"dt1_{i}")
        r["p1"] = row[5].text_input("", value=r["p1"], key=f"p1_{i}")
        r["t1"] = row[6].text_input("", value=r["t1"], key=f"t1_{i}")
        r["dt2"] = row[7].checkbox("", value=r["dt2"], key=f"dt2_{i}")
        r["p2"] = row[8].text_input("", value=r["p2"], key=f"p2_{i}")
        r["t2"] = row[9].text_input("", value=r["t2"], key=f"t2_{i}")
        r["curve"] = row[10].selectbox("", CURVES, index=CURVES.index(r["curve"]), key=f"curve_{i}")

    st.markdown("</div>", unsafe_allow_html=True)

    # SLD image (same as Tkinter left panel)
    if os.path.exists(SLD_PATH):
        st.image(SLD_PATH, width=240)

    st.markdown(
        "<div style='color:red;font-weight:800;margin-top:6px;'>Protection and Automation Division, GOD</div>",
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)

# -------- RIGHT PANEL --------
with right_col:
    st.markdown("<div class='rightPanel'>", unsafe_allow_html=True)

    st.markdown("<div class='lf'><div class='lfTitle'>Plot + Report (same as right panel in Tkinter)</div>", unsafe_allow_html=True)
    st.info("Click Plot Coordination to display the graph and report (same workflow as Tkinter).")

    # Plot on click
    if plot_clicked:
        fig, report_plain, report_html, trip_times, flc, isc, fault_used = plot_curves_and_report()
        st.session_state.last_plot = (fig, report_plain, report_html, trip_times, flc, isc, fault_used)

    if st.session_state.last_plot is not None:
        fig, report_plain, report_html, trip_times, flc, isc, fault_used = st.session_state.last_plot
        st.pyplot(fig, use_container_width=True)

        st.markdown(f"<div class='reportBox'>{report_html}</div>", unsafe_allow_html=True)

        # downloads
        if save_pdf_clicked:
            pdf_bytes = make_pdf_bytes(fig, report_plain)
            st.download_button(
                "Download PDF",
                data=pdf_bytes,
                file_name="NEA_TCC_Report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

        if export_csv_clicked:
            csv_bytes = make_csv_bytes()
            st.download_button(
                "Download CSV",
                data=csv_bytes,
                file_name="NEA_TCC_Report.csv",
                mime="text/csv",
                use_container_width=True,
            )
    else:
        # no plot yet; allow export buttons but show guidance
        if save_pdf_clicked or export_csv_clicked:
            st.warning("Please click Plot Coordination first (same as Tkinter) so the report/plot are generated.")

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
