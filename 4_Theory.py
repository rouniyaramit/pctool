import streamlit as st

st.set_page_config(page_title="NEA Protection Theory & Logic Manual", layout="wide")

st.markdown(
    """
    <style>
      .header {
        background:#004494; color:white; padding:18px;
        font-size:28px; font-weight:800; text-align:center;
        border-radius:8px;
      }
      .footer {color:#555; font-style:italic; font-size:14px; text-align:center; padding-top:10px;}
      textarea {background:white !important;}
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="header">Theoretical Foundation of Protection Coordination</div>', unsafe_allow_html=True)
st.write("")

tab1, tab2, tab3 = st.tabs([" TCC & Relay Curves ", " Grid Coordination Logic ", " Transformer & Fault Physics "])

tcc_content = """
1. THE TIME-CURRENT CHARACTERISTIC (TCC)
The TCC plot is the primary tool for visualizing selectivity. It ensures that downstream relays trip faster than upstream ones for any fault current level.

2. IEC 60255 OPERATING FORMULA
All IDMT (Inverse Definite Minimum Time) calculations in this tool follow the standard:
t = TMS * [ k / ( (I / Ip)^alpha - 1 ) ]

Where:
- t: Operating time in seconds.
- TMS: Time Multiplier Setting (shifts curve vertically).
- I: Fault current.
- Ip: Pickup current (starting point of curve).

3. STANDARD CURVE TYPES
- Standard Inverse (k=0.14, alpha=0.02): General distribution.
- Very Inverse (k=13.5, alpha=1.0): Good for long lines where fault current drops significantly.
- Extremely Inverse (k=80.0, alpha=2.0): Best for coordinating with fuses and handling cold-load pickup.

4. COORDINATION TIME INTERVAL (CTI)
To prevent simultaneous tripping, a margin (CTI) is required.
- Typical NEA CTI: 150ms.
- Breakdown: Breaker opening time (~60ms) + Relay processing (~30ms) + Safety Margin (~60ms).
""".strip()

grid_content = """
1. OVERCURRENT (OC) GRADING
- Stage 1 (IDMT): Usually set at 1.1x Full Load current with minimum TMS of 0.025.
- Stage 2 (Low-Set DT): Usually set at 3x Load current to catch heavy faults before they stress the system with DT of 0 sec.
- Stage 3 (High-Set DT): Instantaneous trip (0.0s) set at ~90% of the transformer short-circuit level. This is unccoordinated stage.

2. EARTH FAULT (EF) LOGIC
EF coordination is more sensitive because it ignores balanced 3-phase load.
- Stage 1 (IDMT): Usually set at 0.15x Full Load current with minimum TMS of 0.025.
- Stage 2 (Low-Set DT): Usually set at 1x Load current to catch heavy faults before they stress the system with DT of 0 sec.
- Stage 3 (High-Set DT): Instantaneous trip (0.0s) set at ~90% of the transformer short-circuit level. This is unccoordinated stage.

3. SELECTIVITY HIERARCHY
The tool enforces a strict "Bottom-Up" logic:
Feeders (Q1-Q3) -> Incomer (Q4) -> HV Side (Q5).
Ensuring CTI of 150ms at each level.
""".strip()

xfmr_content = """
1. FULL LOAD CURRENT (FLC)
The thermal limit of the transformer is calculated as:
FLC = (MVA * 1000) / (sqrt(3) * Voltage_kV)

2. SHORT CIRCUIT CAPACITY (Isc)
The maximum fault current the transformer can deliver:
Isc = FLC / (Impedance % / 100)

3. PROTECTION CONSTRAINTS
- The Incomer (Q4) must be set above the FLC to avoid tripping on full load but below the Isc to protect against busbar faults.
- Overload Protection: If Total Connected Load > Transformer FLC, a critical warning is issued to prevent long-term insulation degradation.
""".strip()

with tab1:
    st.text_area("", tcc_content, height=520)

with tab2:
    st.text_area("", grid_content, height=520)

with tab3:
    st.text_area("", xfmr_content, height=520)

st.markdown('<div class="footer">By Protection and Automation Division, GOD</div>', unsafe_allow_html=True)
