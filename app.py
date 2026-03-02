import streamlit as st
from PIL import Image
from pathlib import Path

st.set_page_config(
    page_title="NEA Master Protection Tool",
    layout="wide",
    initial_sidebar_state="collapsed",
)

def inject_css():
    st.markdown(
        """
        <style>
        /* Hide Streamlit sidebar (left panel) */
        [data-testid="stSidebar"] {display:none !important;}
        [data-testid="stSidebarNav"] {display:none !important;}

        /* Reduce top padding and remove extra whitespace */
        .block-container {padding-top: 0.8rem; padding-bottom: 0.5rem;}

        /* Remove any extra horizontal separators that look like a bar */
        hr {display:none !important;}

        /* Smaller logo container (half-ish) */
        .logo-wrap{
            width: 140px;   /* was ~260 */
            max-width: 140px;
        }

        /* Card container */
        .card{
            border: 1px solid rgba(0,0,0,0.08);
            border-radius: 18px;
            padding: 18px 18px 8px 18px;
            background: #ffffff;
            box-shadow: 0 8px 26px rgba(0,0,0,0.06);
        }

        /* Uniform tile button base */
        .tile .stButton > button{
            width: 100%;
            height: 64px;
            border-radius: 16px;
            border: 1px solid rgba(0,0,0,0.10);
            font-size: 16px;
            font-weight: 800;
            color: white;
            margin: 0 !important;
            box-shadow: 0 8px 20px rgba(2, 132, 199, 0.18);
        }
        .tile .stButton > button:hover{
            transform: translateY(-1px);
            box-shadow: 0 10px 24px rgba(2, 132, 199, 0.28);
        }

        /* 4 blue shades */
        .blue1 .stButton > button{background: linear-gradient(135deg, #0b5bd3 0%, #0ea5e9 100%);} /* deep → sky */
        .blue2 .stButton > button{background: linear-gradient(135deg, #1d4ed8 0%, #38bdf8 100%);} /* royal → light */
        .blue3 .stButton > button{background: linear-gradient(135deg, #0369a1 0%, #22d3ee 100%);} /* teal-blue */
        .blue4 .stButton > button{background: linear-gradient(135deg, #2563eb 0%, #60a5fa 100%);} /* medium → pale */

        </style>
        """,
        unsafe_allow_html=True
    )

inject_css()

logo_path = Path(__file__).parent / "logo.jpg"

# --- Header row (logo + title) ---
left, right = st.columns([1.0, 5.0], vertical_alignment="center")

with left:
    if logo_path.exists():
        img = Image.open(logo_path)
        st.markdown("<div class='logo-wrap'>", unsafe_allow_html=True)
        st.image(img, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown(
        "<h1 style='margin-bottom:0.1rem;'>NEA Master Protection Tool</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<div style='color:#4b5563;font-weight:600;margin-top:0.2rem;'>Select a tool below. (Navigation is here)</div>",
        unsafe_allow_html=True
    )

# --- Buttons in a true 2x2 grid (equal layout) ---
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.subheader("Open a tool")

r1c1, r1c2 = st.columns(2, gap="large")
with r1c1:
    st.markdown("<div class='tile blue1'>", unsafe_allow_html=True)
    if st.button("⚡  TCC Plot Tool (Q1–Q5)", use_container_width=True):
        st.switch_page("pages/2_GUI_Final5_TCC.py")
    st.markdown("</div>", unsafe_allow_html=True)

with r1c2:
    st.markdown("<div class='tile blue2'>", unsafe_allow_html=True)
    if st.button("🧮  OC/EF Grid Tool", use_container_width=True):
        st.switch_page("pages/3_OC_EF_GOD.py")
    st.markdown("</div>", unsafe_allow_html=True)

r2c1, r2c2 = st.columns(2, gap="large")
with r2c1:
    st.markdown("<div class='tile blue3'>", unsafe_allow_html=True)
    if st.button("📘  Theory", use_container_width=True):
        st.switch_page("pages/4_Theory.py")
    st.markdown("</div>", unsafe_allow_html=True)

with r2c2:
    st.markdown("<div class='tile blue4'>", unsafe_allow_html=True)
    if st.button("🛠️  Working", use_container_width=True):
        st.switch_page("pages/5_Working.py")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
