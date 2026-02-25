import streamlit as st
import numpy as np
import math
import matplotlib.pyplot as plt

st.set_page_config(page_title="NEA Protection Tool", layout="wide")

# ===============================
# HEADER
# ===============================
col1, col2 = st.columns([4,1])
with col1:
    st.title("NEA Protection & Coordination Tools")
    st.markdown("Protection and Automation Division, GOD")

with col2:
    try:
        st.image("logo.jpg", width=180)
    except:
        pass

st.markdown("---")

tool = st.sidebar.radio(
    "Select Tool",
    ["Protection Coordination (TCC)", "OC / EF Grid Coordination"]
)

# ============================================================
# TOOL 1 — PROTECTION COORDINATION (Converted from GUI_Final5)
# ============================================================

if tool == "Protection Coordination (TCC)":

    st.header("Transformer & Relay Coordination Tool")

    # Transformer Data
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        MVA = st.number_input("Rating (MVA)", value=16.6)
    with col2:
        HV = st.number_input("HV (kV)", value=33.0)
    with col3:
        LV = st.number_input("LV (kV)", value=11.0)
    with col4:
        Z = st.number_input("Impedance (%)", value=10.0)

    fault_current = st.number_input("Fault Current (A)", value=7900.0)

    # Transformer calculations
    FLC_LV = (MVA * 1000) / (np.sqrt(3) * LV)
    Isc_LV = FLC_LV / (Z / 100)

    st.info(f"FLC (LV): {round(FLC_LV,2)} A | Isc (LV): {round(Isc_LV,2)} A")

    st.markdown("### Relay Settings")

    relays = []

    for i in range(5):
        st.subheader(f"Relay Q{i+1}")
        col1, col2, col3 = st.columns(3)
        with col1:
            pickup = st.number_input(f"Pickup Q{i+1}", value=200.0, key=f"p{i}")
        with col2:
            tms = st.number_input(f"TMS Q{i+1}", value=0.025, key=f"t{i}")
        with col3:
            curve = st.selectbox(
                "Curve",
                ["Standard Inverse", "Very Inverse", "Extremely Inverse"],
                key=f"c{i}"
            )
        relays.append((pickup, tms, curve))

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

    if st.button("Plot Coordination Curve"):

        fig, ax = plt.subplots(figsize=(8,6))
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("Current (A)")
        ax.set_ylabel("Time (s)")
        ax.grid(True, which="both")

        currents = np.logspace(1, 5, 800)

        trip_times = {}

        for i, (pickup, tms, curve) in enumerate(relays):
            times = []
            for I in currents:
                times.append(iec_curve(I, pickup, tms, curve))
            ax.plot(currents, times, label=f"Q{i+1}")

            t_fault = iec_curve(fault_current, pickup, tms, curve)
            if not np.isnan(t_fault):
                trip_times[f"Q{i+1}"] = round(t_fault,3)
                ax.plot(fault_current, t_fault, 'o')

        ax.legend()
        st.pyplot(fig)

        st.markdown("### Coordination Report")
        for k, v in trip_times.items():
            st.write(f"{k} Trip Time: {v} s")

# ============================================================
# TOOL 2 — OC / EF GRID COORDINATION (Converted from OC_EF_GOD)
# ============================================================

elif tool == "OC / EF Grid Coordination":

    st.header("Grid Protection Coordination Tool")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        mva = st.number_input("MVA", value=16.6)
    with col2:
        hv = st.number_input("HV (kV)", value=33.0)
    with col3:
        lv = st.number_input("LV (kV)", value=11.0)
    with col4:
        z = st.number_input("Z %", value=10.0)

    cti = st.number_input("CTI (ms)", value=150.0)

    num_feeders = st.number_input("No. of Feeders", value=3, step=1)

    feeder_loads = []
    feeder_cts = []

    for i in range(int(num_feeders)):
        col1, col2 = st.columns(2)
        with col1:
            load = st.number_input(f"Q{i+1} Load (A)", value=200.0, key=f"l{i}")
        with col2:
            ct = st.number_input(f"Q{i+1} CT", value=400.0, key=f"ct{i}")
        feeder_loads.append(load)
        feeder_cts.append(ct)

    if st.button("Run Calculation"):

        flc_lv = (mva * 1000) / (math.sqrt(3) * lv)
        isc_lv = flc_lv / (z / 100)

        st.success(f"FLC LV: {round(flc_lv,2)} A | Short Circuit: {round(isc_lv,2)} A")

        total_load = sum(feeder_loads)

        if total_load > flc_lv:
            st.error("CRITICAL ALERT: Transformer Overload")

        for i in range(int(num_feeders)):
            st.write(f"Feeder Q{i+1}: Load={feeder_loads[i]} A | CT={feeder_cts[i]}")
