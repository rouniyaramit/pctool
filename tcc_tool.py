# tcc_tool.py

import streamlit as st
import matplotlib.pyplot as plt
from tcc_engine import calculate_tcc


def run_tcc_tool():

    st.header("NEA Protection Coordination Tool (TCC)")

    # ---------------- Transformer Data ----------------
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

    st.markdown("---")
    st.subheader("Relay Settings")

    relay_settings = []

    for i in range(5):
        st.markdown(f"### Relay Q{i+1}")

        c1, c2, c3 = st.columns(3)
        with c1:
            pickup = st.number_input(
                f"Pickup Q{i+1}",
                value=200.0 if i < 3 else 800.0,
                key=f"pickup_{i}"
            )

        with c2:
            tms = st.number_input(
                f"TMS Q{i+1}",
                value=0.025 if i < 3 else 0.07,
                key=f"tms_{i}"
            )

        with c3:
            curve = st.selectbox(
                f"Curve Q{i+1}",
                ["Standard Inverse", "Very Inverse", "Extremely Inverse"],
                key=f"curve_{i}"
            )

        col_idmt, col_dt1, col_dt2 = st.columns(3)

        with col_idmt:
            idmt = st.checkbox("Enable IDMT", value=True, key=f"idmt_{i}")

        with col_dt1:
            dt1 = st.checkbox("Enable DT1", value=False, key=f"dt1_{i}")

        with col_dt2:
            dt2 = st.checkbox("Enable DT2 (Q4 & Q5 only)", value=False, key=f"dt2_{i}")

        col_p1, col_t1 = st.columns(2)
        with col_p1:
            dt1_pickup = st.number_input(
                "DT1 Pickup",
                value=600.0,
                key=f"dt1_pickup_{i}"
            )
        with col_t1:
            dt1_time = st.number_input(
                "DT1 Time (s)",
                value=0.0,
                key=f"dt1_time_{i}"
            )

        col_p2, col_t2 = st.columns(2)
        with col_p2:
            dt2_pickup = st.number_input(
                "DT2 Pickup",
                value=8000.0,
                key=f"dt2_pickup_{i}"
            )
        with col_t2:
            dt2_time = st.number_input(
                "DT2 Time (s)",
                value=0.0,
                key=f"dt2_time_{i}"
            )

        relay_settings.append({
            "pickup": pickup,
            "tms": tms,
            "curve": curve,
            "idmt": idmt,
            "dt1": dt1,
            "dt1_pickup": dt1_pickup,
            "dt1_time": dt1_time,
            "dt2": dt2,
            "dt2_pickup": dt2_pickup,
            "dt2_time": dt2_time,
        })

    # ---------------- Plot & Report ----------------
    if st.button("Plot Coordination"):

        result = calculate_tcc(
            MVA, LV, HV, Z,
            fault_current,
            relay_settings
        )

        fig, ax = plt.subplots(figsize=(10, 6))

        ax.set_title("Time-Current Characteristics")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("Current (A)")
        ax.set_ylabel("Time (s)")
        ax.grid(True, which="both", linestyle="--", alpha=0.7)

        colors = ["blue", "green", "red", "purple", "orange"]

        for i, curve in enumerate(result["curves"]):
            ax.plot(result["currents"], curve,
                    color=colors[i],
                    linewidth=2.5,
                    label=f"Q{i+1}")

        ax.axvline(result["fault_current"],
                   linestyle="dotted",
                   color="black",
                   linewidth=2,
                   label="Fault Level")

        ax.legend()
        st.pyplot(fig)

        # ---------------- Report Section ----------------
        st.markdown("## Coordination Report")
        st.write(
            f"LV FLC: {round(result['FLC_LV'],3)} A | "
            f"LV Isc: {round(result['Isc_LV'],3)} A"
        )
        st.write(f"Fault Current: {round(result['fault_current'],3)} A")

        st.markdown("### Trip Times")
        for q, t in result["trip_times"].items():
            st.write(f"{q} Trip: {t:.3f} s")

        st.markdown("### Coordination Results")

        for item in result["coordination"]:
            if item["status"] == "OK":
                st.success(
                    f"{item['downstream']} → {item['upstream']} : "
                    f"{item['margin']}s (OK)"
                )
            else:
                st.error(
                    f"{item['downstream']} → {item['upstream']} : "
                    f"{item['margin']}s (NOT OK)"
                )
