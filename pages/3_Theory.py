import streamlit as st

st.set_page_config(page_title="Protection Theory", layout="wide")

st.title("NEA Protection Theory & Logic Manual")

tab1, tab2, tab3 = st.tabs(["TCC & Relay Curves", "Grid Coordination Logic", "Transformer & Fault Physics"])

with tab1:
    st.markdown(
        """
### 1. THE TIME-CURRENT CHARACTERISTIC (TCC)
The TCC plot is the primary tool for visualizing selectivity. It ensures that downstream relays trip faster than upstream ones for any fault current level.

### 2. IEC 60255 OPERATING FORMULA
All IDMT (Inverse Definite Minimum Time) calculations follow:
` t = TMS * [ k / ( (I / Ip)^alpha - 1 ) ]`

**Where**
- **t**: Operating time (s)
- **TMS**: Time Multiplier Setting
- **I**: Fault current
- **Ip**: Pickup current

### 3. STANDARD CURVE TYPES
- **Standard Inverse** (k=0.14, α=0.02)
- **Very Inverse** (k=13.5, α=1.0)
- **Extremely Inverse** (k=80.0, α=2.0)

### 4. COORDINATION TIME INTERVAL (CTI)
Typical NEA CTI: **150ms** (breaker + relay + safety margin).
"""
    )

with tab2:
    st.markdown(
        """
### 1. OVERCURRENT (OC) GRADING
- Stage 1 (IDMT): typically **1.1×** full load, **TMS ≥ 0.025**
- Stage 2 (DT): typically **3×** load current, **0.0s**
- Stage 3 (DT): instantaneous at ~**90%** transformer short-circuit level

### 2. EARTH FAULT (EF) LOGIC
- Stage 1 (IDMT): typically **0.15×** full load, **TMS ≥ 0.025**
- Stage 2 (DT): typically **1×** load current, **0.0s**
- Stage 3 (DT): instantaneous at ~**90%** transformer short-circuit level

### 3. SELECTIVITY HIERARCHY
**Feeders (Q1–Q3) → Incomer (Q4) → HV Side (Q5)** with CTI at each level.
"""
    )

with tab3:
    st.markdown(
        """
### 1. FULL LOAD CURRENT (FLC)
`FLC = (MVA * 1000) / (sqrt(3) * Voltage_kV)`

### 2. SHORT CIRCUIT CAPACITY (Isc)
`Isc = FLC / (Impedance% / 100)`

### 3. PROTECTION CONSTRAINTS
- Q4 above FLC (avoid nuisance) but below Isc (protect bus faults)
- If total load > FLC, issue overload warning to avoid insulation degradation
"""
    )

st.caption("By Protection and Automation Division, GOD")
