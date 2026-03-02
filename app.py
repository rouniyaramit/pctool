import streamlit as st
from pathlib import Path
from PIL import Image, ImageOps

st.set_page_config(
    page_title="NEA Master Protection Tool",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -------------------- CSS (HIDE CLOUD UI + DESIGN) --------------------
st.markdown(
    """
    <style>
    /* =========================================================
       HIDE STREAMLIT CLOUD UI (best-effort)
       ========================================================= */
    [data-testid="stToolbar"] {display: none !important;}
    [data-testid="stStatusWidget"] {display: none !important;}
    [data-testid="stAppDeployButton"] {display: none !important;}

    button[title="Manage app"] {display:none !important;}
    a[title="Manage app"] {display:none !important;}
    div[aria-label="Manage app"] {display:none !important;}
    button[aria-label="Manage app"] {display:none !important;}

    header {visibility: hidden !important;}
    header {height: 0px !important;}

    /* =========================================================
       HIDE SIDEBAR / NAV
       ========================================================= */
    section[data-testid="stSidebar"] {display:none !important;}
    div[data-testid="stSidebarNav"] {display:none !important;}
    button[kind="headerNoPadding"] {display:none !important;}

    /* =========================================================
       REMOVE BLANK ROUNDED BAR (BaseWeb input wrapper)
       ========================================================= */
    [data-baseweb="input"] {display:none !important;}
    [data-baseweb="textarea"] {display:none !important;}
    [data-testid="stTextInput"] {display:none !important;}
    [data-testid="stTextInputRootElement"] {display:none !important;}
    input[type="text"], input[type="search"], textarea {display:none !important;}

    /* =========================================================
       BACKGROUND + LAYOUT
       ========================================================= */
    .stApp {
        background: linear-gradient(180deg, #f3f4f6 0%, #eef2f7 60%, #f8fafc 100%) !important;
    }

    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 1.0rem;
        max-width: 1200px;
        min-height: 92vh; /* helps footer sit at the bottom */
    }

    hr {display:none !important;}

    .nea-header { margin-top: 10px; margin-bottom: 18px; }

    .nea-card{
        border: 1px solid rgba(0,0,0,0.10);
        border-radius: 18px;
        padding: 18px 18px 22px 18px;
        background: #ffffff;
        box-shadow: 0 12px 34px rgba(0,0,0,0.08);
    }

    .tiles{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 18px;
        margin-top: 16px;
    }

    .tile{
        display:flex;
        align-items:center;
        justify-content:center;
        height: 96px;
        border-radius: 18px;

        color: #ffffff !important;
        text-decoration: none !important;
        font-size: 22px;
        font-weight: 900;
        letter-spacing: 0.2px;

        border: 1px solid rgba(255,255,255,0.18);
        box-shadow: 0 16px 34px rgba(2,132,199,0.22);
        transition: transform 120ms ease, box-shadow 120ms ease, filter 120ms ease;
        user-select: none;
    }

    .tile:visited { color:#ffffff !important; }
    .tile:hover   { color:#ffffff !important; text-decoration:none !important; }
    .tile:active  { color:#ffffff !important; }

    .tile:hover{
        transform: translateY(-2px);
        box-shadow: 0 20px 44px rgba(2,132,199,0.32);
        filter: brightness(1.03);
    }

    /* 4 blue shades */
    .b1{ background: linear-gradient(135deg, #0b5bd3 0%, #0ea5e9 100%); }
    .b2{ background: linear-gradient(135deg, #1d4ed8 0%, #3b82f6 55%, #60a5fa 100%); }
    .b3{ background: linear-gradient(135deg, #075985 0%, #0284c7 55%, #38bdf8 100%); }
    .b4{ background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 55%, #0b5bd3 100%); }

    /* Footer style */
    .nea-footer{
        margin-top: 26px;
        padding: 14px 0 6px 0;
        text-align: center;
        color: #6b7280;
        font-style: italic;
        font-weight: 600;
        line-height: 1.35;
    }

    @media (max-width: 900px){
        .tiles{ grid-template-columns: 1fr; }
        .tile{ height: 86px; font-size: 20px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------- NAVIGATION (query parameter) --------------------
qp = st.query_params
go = qp.get("go", None)

if go == "tcc":
    st.query_params.clear()
    st.switch_page("pages/2_GUI_Final5_TCC.py")
elif go == "ocef":
    st.query_params.clear()
    st.switch_page("pages/3_OC_EF_GOD.py")
elif go == "theory":
    st.query_params.clear()
    st.switch_page("pages/4_Theory.py")
elif go == "working":
    st.query_params.clear()
    st.switch_page("pages/5_Working.py")

# -------------------- LOGO (no cropping) --------------------
logo_path = Path(__file__).parent / "logo.jpg"

def load_logo_no_crop(path: Path, target_px: int = 170):
    if not path.exists():
        return None
    img = Image.open(path).convert("RGBA")
    img = ImageOps.expand(img, border=18, fill=(255, 255, 255, 255))
    img = ImageOps.contain(img, (target_px, target_px))
    return img

# -------------------- HEADER --------------------
st.markdown("<div class='nea-header'>", unsafe_allow_html=True)

c1, c2 = st.columns([1.2, 5.0], vertical_alignment="center")

with c1:
    logo = load_logo_no_crop(logo_path, target_px=170)
    if logo is not None:
        st.image(logo, width=170)
    else:
        st.warning("logo.jpg not found in repo root")

with c2:
    st.markdown(
        "<h1 style='margin:0; font-size:46px; font-weight:900;'>NEA Master Protection Tool</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div style='margin-top:8px; color:#4b5563; font-weight:800; font-size:16px;'>Select a tool below. (Navigation is here)</div>",
        unsafe_allow_html=True,
    )

st.markdown("</div>", unsafe_allow_html=True)

# -------------------- MAIN CARD + TILES --------------------
st.markdown("<div class='nea-card'>", unsafe_allow_html=True)
st.markdown("<h3 style='margin:0; font-size:28px; font-weight:900;'>Open a tool</h3>", unsafe_allow_html=True)

st.markdown(
    """
    <div class="tiles">
        <a class="tile b1" href="?go=tcc">⚡&nbsp;&nbsp;TCC Plot Tool (Q1–Q5)</a>
        <a class="tile b2" href="?go=ocef">🧮&nbsp;&nbsp;OC/EF Grid Tool</a>
        <a class="tile b3" href="?go=theory">📘&nbsp;&nbsp;Theory</a>
        <a class="tile b4" href="?go=working">🛠️&nbsp;&nbsp;Working</a>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("</div>", unsafe_allow_html=True)

# -------------------- FOOTER (your lines) --------------------
st.markdown(
    """
    <div class="nea-footer">
        Protection and Automation Division, GOD<br/>
        Nepal Electricity Authority
    </div>
    """,
    unsafe_allow_html=True,
)
