import streamlit as st
import math

def run_oc_ef_tool():

    st.header("OC / EF Grid Coordination Tool")

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
    feeders = st.number_input("No. of Feeders", value=3)

    loads = []
    cts = []

    for i in range(int(feeders)):
        c1, c2 = st.columns(2)
        with c1:
            load = st.number_input(f"Q{i+1} Load (A)", key=f"l{i}", value=200.0)
        with c2:
            ct = st.number_input(f"Q{i+1} CT", key=f"ct{i}", value=400.0)
        loads.append(load)
        cts.append(ct)

    if st.button("Run Calculation"):

        flc_lv = (mva * 1000) / (math.sqrt(3) * lv)
        isc_lv = flc_lv / (z / 100)

        st.success(f"FLC LV: {round(flc_lv,2)} A | Short Circuit: {round(isc_lv,2)} A")

        total_load = sum(loads)

        if total_load > flc_lv:
            st.error("CRITICAL ALERT: Transformer Overload")

        for i in range(int(feeders)):
            st.write(f"Feeder Q{i+1}: Load={loads[i]} A | CT={cts[i]}")
