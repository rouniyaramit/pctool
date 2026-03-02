import streamlit as st
import pandas as pd
from engine.ocef_engine import SystemInputs, FeederInputs, compute_ocef

st.set_page_config(page_title="OC/EF Grid Tool", layout="wide")
st.title("OC/EF Grid Tool")
st.caption("Streamlit UI only. All calculations are in engine/ocef_engine.py")

with st.sidebar:
    st.header("System Inputs")
    mva = st.number_input("Transformer MVA", value=16.6, step=0.1, format="%.3f")
    hv = st.number_input("HV (kV)", value=33.0, step=0.1, format="%.3f")
    lv = st.number_input("LV (kV)", value=11.0, step=0.1, format="%.3f")
    z  = st.number_input("Impedance Z (%)", value=10.0, step=0.1, format="%.3f")
    cti = st.number_input("CTI (ms) (>=120)", value=150.0, step=10.0, format="%.1f")
    q4_ct = st.number_input("Q4 CT primary (A)", value=900.0, step=10.0, format="%.1f")
    q5_ct = st.number_input("Q5 CT primary (A)", value=300.0, step=10.0, format="%.1f")
    st.divider()
    nfeed = st.number_input("Number of feeders (Q1..)", value=3, min_value=1, max_value=12, step=1)

st.subheader("Feeder Inputs")
default_rows = [(200.0, 400.0), (250.0, 400.0), (300.0, 400.0)]

rows = []
for i in range(int(nfeed)):
    if i < len(default_rows):
        l0, c0 = default_rows[i]
    else:
        l0, c0 = (200.0, 400.0)
    rows.append({"Feeder": f"Q{i+1}", "Load (A)": l0, "CT (A)": c0})

df_in = st.data_editor(
    pd.DataFrame(rows),
    use_container_width=True,
    num_rows="fixed",
    hide_index=True,
)

if st.button("Calculate", type="primary"):
    sys = SystemInputs(mva=mva, hv_kv=hv, lv_kv=lv, z_pct=z, cti_ms=cti, q4_ct=q4_ct, q5_ct=q5_ct)
    feeders = [FeederInputs(load_a=float(r["Load (A)"]), ct_a=float(r["CT (A)"])) for _, r in df_in.iterrows()]

    try:
        res = compute_ocef(sys, feeders)
    except Exception as e:
        st.error(f"Invalid Inputs: {e}")
        st.stop()

    st.success("Calculation complete.")

    st.subheader("Summary")
    st.write(
        f"FLC LV: **{res.system.flc_lv} A** | FLC HV: **{res.system.flc_hv} A** | "
        f"Isc LV: **{res.system.isc_lv} A**"
    )
    st.write(f"Total Load: **{round(res.system.total_load,2)} A** | HV Load: **{round(res.system.hv_load,2)} A**")

    if res.critical_overload:
        st.error("CRITICAL ALERT: Transformer overload (Total Load > LV FLC).")

    if res.ct_alerts:
        st.warning("".join(res.ct_alerts))

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Overcurrent (OC) Report")
        st.text(res.oc_report_text)
        st.download_button("Download OC Report (txt)", res.oc_report_text.encode("utf-8"),
                           file_name="oc_report.txt", mime="text/plain", use_container_width=True)
    with c2:
        st.subheader("Earth Fault (EF) Report")
        st.text(res.ef_report_text)
        st.download_button("Download EF Report (txt)", res.ef_report_text.encode("utf-8"),
                           file_name="ef_report.txt", mime="text/plain", use_container_width=True)
