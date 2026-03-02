import streamlit as st
from pathlib import Path
from PIL import Image, ImageOps

st.set_page_config(
    page_title="NEA Master Protection Tool",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -------------------- CSS --------------------
st.markdown(
    """
    <style>
    /* Hide Streamlit sidebar completely */
    [data-testid="stSidebar"] {display:none !important;}
    [data-testid="stSidebarNav"] {display:none !important;}

    /* Make page spacing nicer + move content down a bit */
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 1.0rem;
        max-width: 1200px;
    }

    /* Remove any horizontal rule lines */
    hr {display:none !important;}

    /* Header wrapper */
    .nea-header {
        margin-top: 8px;
        margin-bottom: 18px;
    }

    /* Card container */
    .nea-card{
        border: 1px solid rgba(0,0,0,0.08);
        border-radius: 18px;
        padding: 18px 18px 22px 18px;
        background: #ffffff;
        box-shadow: 0 10px 30px rgba(0,0,0,0.06);
    }

    /* Tiles grid */
    .tiles{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 18px;
        margin-top: 16px;
    }

    /* Tile base */
    .tile{
        display:flex;
        align-items:center;
        justify-content:center;
        height: 96px;
        border-radius: 18px;

        /* FORCE WHITE text always */
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

    /* Also force white for visited/hover/active states (links sometimes become dark) */
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

    /* Mobile */
    @media (max-width: 900px){
        .tiles{ grid-template-columns: 1fr; }
        .tile{ height: 86px; font-size: 20px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------- NAV (query param) --------------------
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

# -------------------- LOGO (NO CROP GUARANTEE) --------------------
# Your repo has logo.jpg in root
logo_path = Path(__file__).parent / "logo.jpg"

def load_logo_no_crop(path: Path, target_px: int = 170) -> Image.Image | None:
    """
    Ensures the logo is ALWAYS fully visible:
    - adds padding around it
    - uses contain() (never crops)
    - returns an RGBA image safe for st.image
    """
    if not path.exists():
        return None

    img = Image.open(path).convert("RGBA")

    # Add generous padding so edges never appear clipped
    img = ImageOps.expand(img, border=18, fill=(255, 255, 255, 255))

    # Resize to fit inside a square WITHOUT cropping
    img = ImageOps.contain(img, (target_px, target_px))

    return img

# -------------------- HEADER (moved down) --------------------
st.markdown("<div class='nea-header'>", unsafe_allow_html=True)

c1, c2 = st.columns([1.2, 5.0], vertical_alignment="center")

with c1:
    logo = load_logo_no_crop(logo_path, target_px=170)
    if logo is not None:
        # Fixed width prevents Streamlit responsive scaling that can clip in some layouts
        st.image(logo, width=170)
    else:
        st.error("logo.jpg not found in repo root.")

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
