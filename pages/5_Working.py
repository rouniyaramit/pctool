import streamlit as st

st.set_page_config(page_title="NEA Protection Suite - Comprehensive User Manual", layout="wide")

st.markdown(
    """
    <style>
      .header {
        background:#003366; color:white; padding:22px;
        font-size:34px; font-weight:900; text-align:center;
        border-radius:8px;
      }
      .status {
        background:#003366; color:white; padding:8px;
        border-radius:6px; margin-top:14px;
      }
      .note {background:#fff3cd; padding:10px; border-radius:8px;}
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="header">OPERATIONAL WORKFLOW & USER GUIDE</div>', unsafe_allow_html=True)
st.write("")

tab1, tab2, tab3 = st.tabs([" 📈 TCC Plotter Guide ", " ⚡ OC/EF Grid Guide ", " 🛠️ Troubleshooting & Tips "])

tcc_txt = """
SECTION 1: TCC PLOTTER
This tool visualizes how your relays will react during a fault.

1.1 Input Field Definitions
• Pickup Current (Ip): The current level where the relay starts 'timing.' For a 400/1A CT, if you want it to trip at 400A, enter 400.
• TMS (Time Multiplier Settings): A decimal (usually 0.025 to 1.0). Lowering this moves the curve DOWN (faster trip).
• Curve Dropdown: Choose 'Standard Inverse' for most NEA feeders.

1.2 Coordination Workflow
1. Enter settings for Q1 (Feeder) first.
2. Ensure Q4 (LV Incomer) is set such that its curve stays ABOVE Q1 with at least a 0.15s gap.
3. Check the 'Enable' checkbox for IDMT/DT stages or they won't appear on the graph.

1.3 Understanding the Plot
The X-axis represents Current (Amps) and the Y-axis represents Time (Seconds). If curves intersect, you have a 'Race Condition' where both relays might trip simultaneously—this must be fixed by adjusting TMS.
""".strip()

grid_txt = """
SECTION 2: OC/EF GRID TOOL 
This tool automates the math for a whole substation based on transformer capacity.

2.1 Required Data Entry
• Transformer MVA: e.g., 16.6 or 24.
• % Impedance: Crucial for calculating Short Circuit (Isc). It is in the nameplate of the transformer. 
• CT Ratio: Enter the primary value (e.g., 400 for 400/1A).

2.2 The 'Calculate' Button Magic
When you click calculate, the program performs three checks:
1. Current Check: Is Total Feeder Load > Transformer FLC?
2. Grading Check: Is the Incomer TMS high enough to allow Feeders to clear first?
3. Earth Fault Sensitivity: Ensures EF pickup is low enough to detect high-impedance ground faults.

2.3 Exporting Results
The 'Generate PDF' button creates a formal document. Always review the 'Comments' section in the PDF for specific engineering warnings.The 'Save CSV' button creates a formal document in CSV too. 
""".strip()

trouble_txt = """
COMMON ISSUES & SOLUTIONS

Q: The Plot looks like a mess of lines.
A: Ensure your Current (Ip) values are in the correct order. Q1 should be the smallest, Q5 the largest.

Q: Why is a field highlighted in Red?
A: This is a Safety Interlock. It means your setting is physically dangerous for the equipment (e.g., trying to draw more current from low rating CT).

PRO-TIP: Use the 'Reset' button before starting a new substation calculation to clear old data from memory.
""".strip()

with tab1:
    st.text_area("", tcc_txt, height=520)

with tab2:
    st.text_area("", grid_txt, height=520)

with tab3:
    st.markdown('<div class="note">PRO-TIP: Use the Reset button before starting a new substation calculation to clear old data from memory.</div>', unsafe_allow_html=True)
    st.text_area("", trouble_txt, height=500)

st.markdown('<div class="status">NEA Protection & Automation Division - Kathmandu, Nepal</div>', unsafe_allow_html=True)
