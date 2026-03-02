import streamlit as st
from PIL import Image
from pathlib import Path

st.set_page_config(
    page_title="NEA Master Protection Tool",
    layout="wide",
    initial_sidebar_state="collapsed",
)

def inject_global_css():
    st.markdown(
        """
        <style>
        /* Hide Streamlit sidebar (left panel) */
        [data-testid="stSidebar"] {display:none !important;}
        [data-testid="stSidebarNav"] {display:none !important;}

        /* Reduce top padding a bit */
        .block-container {padding-top: 1.2rem;}

        /* Make buttons look like attractive tabs */
        .stButton > button {
            width: 100%;
            height: 54px;
            border-radius: 14px;
            border: 1px solid rgba(0,0,0,0.08);
            font-size: 16px;
            font-weight: 700;
            color: white;
            background: linear-gradient(135deg, #0b5bd3 0%, #0ea5e9 100%);
            box-shadow: 0 8px 20px rgba(11, 91, 211, 0.15);
        }
        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 10px 24px rgba(11, 91, 211, 0.22);
        }

        /* Secondary tab style */
        .tab2 .stButton > button {
            background: linear-gradient(135deg, #0f766e 0%, #22c55e 100%);
            box-shadow: 0 8px 20px rgba(15, 118, 110, 0.15);
        }
        .tab3 .stButton > button {
            background: linear-gradient(135deg, #7c3aed 0%, #ec4899 100%);
            box-shadow: 0 8px 20px rgba(124, 58, 237, 0.15);
        }
        .tab4 .stButton > button {
            background: linear-gradient(135deg, #ea580c 0%, #f59e0b 100%);
            box-shadow: 0 8px 20px rgba(234, 88, 12, 0.15);
        }

        /* Nice section title */
        .nea-card {
            border: 1px solid rgba(0,0,0,0.08);
            border-radius: 18px;
            padding: 18px;
            background: #ffffff;
            box-shadow: 0 8px 26px rgba(0,0,0,0.06);
        }
        </style>
        """,
        unsafe_allow_html=True
    )

inject_global_css()

logo_path = Path(__file__).parent / "logo.jpg"

# Header
c1, c2 = st.columns([1, 4], vertical_alignment="center")
with c1:
    if logo_path.exists():
        st.image(Image.open(logo_path), use_container_width=True)
with c2:
    st.markdown("<h1 style='margin-bottom:0.2rem;'>NEA Master Protection Tool</h1>", unsafe_allow_html=True)
    st.markdown(
        "<div style='color:#4b5563;font-weight:600;'>Select a tool below. (Sidebar hidden — navigation is here)</div>",
        unsafe_allow_html=True,
    )

st.markdown("<hr/>", unsafe_allow_html=True)

st.markdown("<div class='nea-card'>", unsafe_allow_html=True)
st.subheader("Open a tool")

a, b = st.columns(2, gap="large")

with a:
    # Blue
    if st.button("⚡ TCC Plot Tool (Q1–Q5)", use_container_width=True):
        st.switch_page("pages/2_GUI_Final5_TCC.py")

    # Orange
    st.markdown("<div class='tab4'>", unsafe_allow_html=True)
    if st.button("📘 Theory", use_container_width=True):
        st.switch_page("pages/4_Theory.py")
    st.markdown("</div>", unsafe_allow_html=True)

with b:
    # Green
    st.markdown("<div class='tab2'>", unsafe_allow_html=True)
    if st.button("🧮 OC/EF Grid Tool", use_container_width=True):
        st.switch_page("pages/3_OC_EF_GOD.py")
    st.markdown("</div>", unsafe_allow_html=True)

    # Purple/Pink
    st.markdown("<div class='tab3'>", unsafe_allow_html=True)
    if st.button("🛠️ Working", use_container_width=True):
        st.switch_page("pages/5_Working.py")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
