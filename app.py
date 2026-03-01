import os
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="NEA Protection & Coordination Tools", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Prefer logo.jpg, fallback to logo.png
LOGO_JPG = os.path.join(BASE_DIR, "logo.jpg")
LOGO_PNG = os.path.join(BASE_DIR, "logo.png")
LOGO_PATH = LOGO_JPG if os.path.exists(LOGO_JPG) else LOGO_PNG

# -------------------- Kill Streamlit UI + EXE look --------------------
st.markdown("""
<style>
/* Hide Streamlit UI */
#MainMenu {display:none !important;}
footer {display:none !important;}
header {display:none !important;}
header[data-testid="stHeader"] {display:none !important;}
[data-testid="stToolbar"] {display:none !important;}
[data-testid="stDecoration"] {display:none !important;}
[data-testid="stAppToolbar"] {display:none !important;}
[data-testid="stTopNav"] {display:none !important;}
[data-testid="stStatusWidget"] {display:none !important;}
[data-testid="stSidebar"] {display:none !important;}

/* Remove padding that can create top gap */
.block-container {padding:0 !important; margin:0 !important;}
[data-testid="stAppViewContainer"] > .main {padding:0 !important; margin:0 !important;}
[data-testid="stAppViewContainer"] {padding:0 !important; margin:0 !important;}

/* Full background */
html, body, [data-testid="stAppViewContainer"] {
    background: #dcdcdc !important;
    overflow: hidden !important;
}

/* EXE window panel */
.window {
    width: 980px;
    max-width: 95%;
    margin: 18px auto;
    background: #efefef;
    border: 1px solid #b5b5b5;
    border-radius: 10px;
    padding: 20px 22px;
    box-shadow: 0 12px 26px rgba(0,0,0,0.25);
}

/* Title */
.title {
    text-align:center;
    font-size: 34px;
    font-weight: 900;
    margin-top: 10px;
    margin-bottom: 18px;
    color:#1f1f1f;
}

/* Buttons */
.tkbtn {
    display:block;
    width: 660px;
    max-width: 94%;
    margin: 14px auto;
    padding: 18px;
    font-size: 18px;
    font-weight: 900;
    color:white !important;
    text-decoration:none !important;
    text-align:center;
    border-radius:6px;
    border:1px solid rgba(0,0,0,0.2);
    box-shadow:0 3px 0 rgba(0,0,0,0.2);
    transition: filter 0.12s ease, transform 0.05s ease;
}
.tkbtn:hover {filter:brightness(1.08);}
.tkbtn:active {transform: translateY(1px);}

/* Colors */
.blue1{background:#0b74c7;}
.blue2{background:#0a63b5;}
.purp1{background:#4a35c8;}
.purp2{background:#36157d;}

/* Footer */
.footer{
    text-align:center;
    margin-top:28px;
    font-style:italic;
    color:#4b4b4b;
    font-size:14px;
    line-height:1.5;
}
</style>
""", unsafe_allow_html=True)

# -------------------- JS: remove that rounded white top bar --------------------
# This script looks for a "white rounded rectangle with shadow" near the top,
# then removes it. Works across Streamlit Cloud UI changes.
components.html(
    """
<script>
(function(){
  function removeTopBar(){
    const divs = Array.from(document.querySelectorAll('div'));
    for (const d of divs){
      const r = d.getBoundingClientRect();
      if (!r || r.width < 500 || r.height < 35 || r.height > 120) continue;
      if (r.top < -5 || r.top > 80) continue;   // near the top
      const cs = window.getComputedStyle(d);

      // Looks like that bar: white-ish background, rounded corners, has shadow, and minimal text
      const bg = cs.backgroundColor || "";
      const br = cs.borderRadius || "";
      const bs = cs.boxShadow || "";
      const hasShadow = bs && bs !== "none";
      const rounded = br && br !== "0px";
      const whiteish = bg.includes("255, 255, 255") || bg.includes("rgba(255, 255, 255");
      const almostNoText = (d.innerText || "").trim().length === 0;

      if (hasShadow && rounded && whiteish && almostNoText){
        d.remove();
        return true;
      }
    }
    return false;
  }

  // Try multiple times because Streamlit mounts UI after load
  let tries = 0;
  const timer = setInterval(() => {
    tries++;
    const done = removeTopBar();
    if (done || tries > 40) clearInterval(timer);
  }, 150);
})();
</script>
""",
    height=0,
)

# -------------------- Navigation via query param --------------------
page = st.query_params.get("page", None)
if page:
    mapping = {
        "tcc": "pages/2_GUI_Final5_TCC.py",
        "ocef": "pages/3_OC_EF_GOD.py",
        "theory": "pages/4_Theory.py",
        "working": "pages/5_Working.py",
    }
    target = mapping.get(page)
    if target:
        st.switch_page(target)

# -------------------- UI --------------------
st.markdown("<div class='window'>", unsafe_allow_html=True)

# Center logo
if os.path.exists(LOGO_PATH):
    c1, c2, c3 = st.columns([3, 1, 3])
    with c2:
        st.image(LOGO_PATH, width=150)
else:
    st.warning("Logo not found. Put logo.jpg (preferred) or logo.png in the root folder.")

# Title
st.markdown("<div class='title'>NEA Protection &amp; Coordination Tools</div>", unsafe_allow_html=True)

# Buttons
st.markdown("""
<a class='tkbtn blue1' href='?page=tcc'>Open Protection Coordination Tool (TCC Plot)</a>
<a class='tkbtn blue2' href='?page=ocef'>Open OC / EF Grid Coordination Tool</a>
<a class='tkbtn purp1' href='?page=theory'>Open Protection Theory Guide</a>
<a class='tkbtn purp2' href='?page=working'>Open Working Methodology / Manual</a>
""", unsafe_allow_html=True)

# Footer
st.markdown("""
<div class='footer'>
Protection and Automation Division, GOD<br/>
Nepal Electricity Authority
</div>
""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
