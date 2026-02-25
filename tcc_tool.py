import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from utils import iec_curve, transformer_calculations

CTI_Q1_Q4 = 0.150
CTI_Q1_Q5 = 0.300
CTI_Q4_Q5 = 0.150

def run_tcc_tool():

    st.header("Protection Coordination Tool (TCC)")

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

    FLC_LV, Isc_LV = transformer_calculations(MVA, LV, Z)
    st.info(f"FLC (LV): {round(FLC_LV,2)} A | Isc (LV): {round(Isc_LV,2)} A")

    st.markdown("## Relay Settings")

    relays = []
    for i in range(5):
        st.subheader(f"Relay Q{i+1}")
        c1, c2, c3 = st.columns(3)
        with c1:
            pickup = st.number_input("Pickup", key=f"p{i}", value=200.0)
        with c2:
            tms = st.number_input("TMS", key=f"t{i}", value=0.025)
        with c3:
            curve = st.selectbox("Curve",
                                 ["Standard Inverse","Very Inverse","Extremely Inverse"],
                                 key=f"c{i}")
        relays.append((pickup, tms, curve))

    if st.button("Plot Coordination Curve"):

        fig, ax = plt.subplots(figsize=(8,6))
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("Current (A)")
        ax.set_ylabel("Time (s)")
        ax.grid(True, which="both")

        currents = np.logspace(1,5,800)
        trip_times = {}

        for i, (pickup, tms, curve) in enumerate(relays):
            times = [iec_curve(I, pickup, tms, curve) for I in currents]
            ax.plot(currents, times, label=f"Q{i+1}")

            t_fault = iec_curve(fault_current, pickup, tms, curve)
            if not np.isnan(t_fault):
                trip_times[f"Q{i+1}"] = round(t_fault,3)
                ax.plot(fault_current, t_fault, 'o')

        ax.legend()
        st.pyplot(fig)

        st.markdown("### Coordination Report")
        for q, t in trip_times.items():
            st.write(f"{q} Trip: {t} s")
