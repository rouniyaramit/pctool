import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from io import BytesIO

# --- Page Configuration ---
st.set_page_config(page_title="EE Vector Lab", layout="wide", initial_sidebar_state="expanded")

# Custom CSS to mimic your dark terminal theme
st.markdown("""
    <style>
    .main { background-color: #1a1a1a; color: #00ffcc; }
    stMetric { background-color: #262626; border-radius: 10px; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ Electrical Engineering Vector Lab")
st.write("Input magnitudes and angles to visualize phasors and calculate system totals.")

# --- Sidebar Inputs ---
st.sidebar.header("Vector Configuration")
if st.sidebar.button("Reset to Balanced 3-Phase"):
    st.session_state.rows = [
        {"name": "Va", "mode": "Polar", "v1": 230.0, "v2": 0.0},
        {"name": "Vb", "mode": "Polar", "v1": 230.0, "v2": 120.0},
        {"name": "Vc", "mode": "Polar", "v1": 230.0, "v2": -120.0}
    ]
elif 'rows' not in st.session_state:
    st.session_state.rows = [{"name": "V1", "mode": "Polar", "v1": 0.0, "v2": 0.0}]

def add_row():
    st.session_state.rows.append({"name": f"V{len(st.session_state.rows)+1}", "mode": "Polar", "v1": 0.0, "v2": 0.0})

st.sidebar.button("➕ Add Vector", on_click=add_row)

# --- Data Processing ---
processed_data = []
complex_nums = []

for i, row in enumerate(st.session_state.rows):
    with st.sidebar.expander(f"Vector: {row['name']}", expanded=True):
        col_n, col_m = st.columns(2)
        row['name'] = col_n.text_input("Label", value=row['name'], key=f"name_{i}")
        row['mode'] = col_m.selectbox("Type", ["Polar", "Rect"], index=0 if row['mode'] == "Polar" else 1, key=f"mode_{i}")
        
        col_v1, col_v2 = st.columns(2)
        label1 = "Mag" if row['mode'] == "Polar" else "Real (Re)"
        label2 = "Angle (°)" if row['mode'] == "Polar" else "Imag (j)"
        row['v1'] = col_v1.number_input(label1, value=float(row['v1']), key=f"v1_{i}")
        row['v2'] = col_v2.number_input(label2, value=float(row['v2']), key=f"v2_{i}")

        # Math logic from your original script
        if row['mode'] == "Polar":
            rad = np.radians(row['v2'])
            c_num = row['v1'] * (np.cos(rad) + 1j * np.sin(rad))
        else:
            c_num = complex(row['v1'], row['v2'])
        
        if abs(c_num) > 0:
            complex_nums.append(c_num)
            processed_data.append({
                "Label": row['name'],
                "Polar": f"{np.abs(c_num):.2f} ∠{np.degrees(np.angle(c_num)):.1f}°",
                "Rectangular": f"{c_num.real:.2f} + j{c_num.imag:.2f}",
                "Admittance": f"{abs(1/c_num):.4f} ∠{-np.degrees(np.angle(c_num)):.1f}°" if abs(c_num) != 0 else "0"
            })

# --- Visualization ---
col_graph, col_stats = st.columns([2, 1])

with col_graph:
    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(8, 8))
    fig.patch.set_facecolor('#1a1a1a')
    ax.set_facecolor('#222')
    ax.tick_params(colors='white')
    ax.grid(color='#444', linestyle='--')

    colors = plt.cm.plasma(np.linspace(0, 1, len(complex_nums)))
    for i, c in enumerate(complex_nums):
        ax.annotate('', xy=(np.angle(c), np.abs(c)), xytext=(0, 0),
                    arrowprops=dict(arrowstyle="->", color=colors[i], lw=2.5))
        ax.text(np.angle(c), np.abs(c), f" {st.session_state.rows[i]['name']}", color="white", fontweight='bold')

    if complex_nums:
        total = sum(complex_nums)
        ax.annotate('', xy=(np.angle(total), np.abs(total)), xytext=(0, 0),
                    arrowprops=dict(arrowstyle="fancy", color="white", alpha=0.4))
    
    st.pyplot(fig)

with col_stats:
    st.subheader("System Summary")
    if complex_nums:
        total = sum(complex_nums)
        st.metric("Vector Sum (Mag)", f"{np.abs(total):.3f}")
        st.metric("Phase Angle", f"{np.degrees(np.angle(total)):.2f}°")
        st.code(f"Sum: {total.real:.2f} + j({total.imag:.2f})")
    
    st.dataframe(pd.DataFrame(processed_data), use_container_width=True)
    
    # CSV Export
    if processed_data:
        df = pd.DataFrame(processed_data)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Results (CSV)", data=csv, file_name="vector_results.csv", mime="text/csv")