# oc_ef_tool.py

import streamlit as st
from oc_ef_engine import calculate_oc_ef


def run_oc_ef_tool():

    st.header("OC / EF Protection Coordination Tool")

    # ---------------- Transformer Section ----------------
    st.subheader("Transformer Data")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        mva = st.number_input("MVA", value=16.6)

    with col2:
        hv = st.number_input("HV (kV)", value=33.0)

    with col3:
        lv = st.number_input("LV (kV)", value=11.0)

    with col4:
        z = st.number_input("Impedance (%)", value=10.0)

    cti_ms = st.number_input("CTI (ms)", value=300)

    st.markdown("---")

    # ---------------- Incomer CT ----------------
    st.subheader("Incomer CT Settings")

    col5, col6 = st.columns(2)

    with col5:
        q4_ct = st.number_input("Q4 LV Incomer CT (A)", value=1200.0)

    with col6:
        q5_ct = st.number_input("Q5 HV CT (A)", value=600.0)

    st.markdown("---")

    # ---------------- Feeder Inputs ----------------
    st.subheader("Feeder Data")

    feeder_count = st.number_input(
        "Number of Feeders",
        min_value=1,
        max_value=20,
        value=3
    )

    feeder_data = []

    for i in range(int(feeder_count)):

        st.markdown(f"### Feeder Q{i+1}")

        c1, c2 = st.columns(2)

        with c1:
            load = st.number_input(
                f"Load Q{i+1} (A)",
                value=200.0,
                key=f"load_{i}"
            )

        with c2:
            ct = st.number_input(
                f"CT Q{i+1} (A)",
                value=300.0,
                key=f"ct_{i}"
            )

        feeder_data.append({
            "load": load,
            "ct": ct
        })

    st.markdown("---")

    # ---------------- Run Button ----------------
    if st.button("Generate OC / EF Report"):

        result = calculate_oc_ef(
            mva,
            hv,
            lv,
            z,
            cti_ms,
            q4_ct,
            q5_ct,
            feeder_data
        )

        if "error" in result:
            st.error(result["error"])
            return

        # ---------------- Header ----------------
        st.markdown("## System Summary")
        st.text(result["header"])

        # ---------------- Overload Alert ----------------
        if result["overload"]:
            st.error(result["overload"])

        # ---------------- CT Alerts ----------------
        if result["ct_alerts"]:
            for alert in result["ct_alerts"]:
                st.warning(alert)

        # ---------------- OC Report ----------------
        st.markdown("## Overcurrent (OC) Settings")
        st.text(result["oc_report"])

        # ---------------- EF Report ----------------
        st.markdown("## Earth Fault (EF) Settings")
        st.text(result["ef_report"])
