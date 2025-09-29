import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st
import pandas as pd
import altair as alt
from docx import Document
from PIL import Image

# ======================================
# BRAND / THEME
# ======================================
ACCENT = "#E60F18"       # TFML red
CARD = "#F5F5F5"
TEXT = "#000000"
MUTED = "#555555"

st.set_page_config(
    page_title="TFML Agentic AI — Luxe Console",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS = BASE_DIR / "assets"
LOGS = BASE_DIR / "logs"
EOIS = BASE_DIR / "eois"
TENDERS_JSON = LOGS / "tenders.json"
LOGO_PATH = ASSETS / "tfml_logo.png"

EOIS.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)

# ======================================
# GLOBAL CSS (light look)
# ======================================
st.markdown(f"""
<style>
.stApp {{
  background: #FFFFFF;
}}
.block-container {{ padding-top: 1rem; }}

.header {{
  display:flex; align-items:center; gap:14px; padding: 6px 0 14px 0; 
  border-bottom:1px solid #ddd;
}}
.header .title {{ font-weight:900; font-size:26px; color:{TEXT}; letter-spacing:.2px; }}
.header .tag  {{ color:{MUTED}; font-size:13px; margin-top:-6px; }}

.kpi {{
  background: linear-gradient(180deg, #FFFFFF 0%, #F5F5F5 100%);
  border: 1px solid #ddd;
  border-radius: 14px; padding: 16px; color: {TEXT};
}}
.kpi .label {{ color:{MUTED}; font-size:.78rem; text-transform:uppercase; letter-spacing:1px; }}
.kpi .value {{ font-size:1.8rem; font-weight:800; }}
.kpi .sub   {{ color:{MUTED}; font-size:.78rem; }}

.card {{ background: {CARD}; border:1px solid #ddd; border-radius: 14px; padding: 16px; }}

.pill {{
  display:inline-block; padding: 2px 10px; border-radius: 999px; font-size: .75rem; font-weight: 700;
  background: #eee; color: #333; border: 1px solid #ccc;
}}
.pill.red {{ background: rgba(230,15,24,.12); color: {ACCENT}; border-color: {ACCENT}; }}

.link a {{ color: {ACCENT}; text-decoration:none; font-weight:600; }}

.btn {{
  background:{ACCENT}; color:#fff; padding:9px 14px; border-radius:10px; border:none; font-weight:700;
}}
.btn.ghost {{ background:transparent; border:1px solid #ccc; color:{TEXT}; }}
</style>
""", unsafe_allow_html=True)

# ======================================
# DATA LAYER
# ======================================
def load_rows():
    if TENDERS_JSON.exists():
        try:
            with open(TENDERS_JSON, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_rows(rows):
    with open(TENDERS_JSON, "w") as f:
        json.dump(rows, f, indent=2)

# ======================================
# DOC GENERATION
# ======================================
EOI_TMPL = """Dear {recipient},

Total Facilities Management Limited (TFML) is pleased to express interest in the opportunity titled "{title}". With a strong track record delivering {sector_desc}, our team is positioned to meet your outcomes on quality, compliance and timelines.

Scope alignment (summary):
{summary}

TFML offers certified personnel, SLAs, HSE compliance and proven delivery for public and private estates nationwide. We welcome the opportunity to submit full technical and financial proposals upon request.

Sincerely,
TFML Bid Office
"""

def write_docx(tender, doc_kind="EOI"):
    safe_title = tender.get("title","Untitled")[:60].replace(" ", "_")
    fname = f"{safe_title}_{doc_kind}.docx"
    fpath = EOIS / fname

    doc = Document()
    doc.add_heading(f"{doc_kind} Draft", level=1)
    body = EOI_TMPL.format(
        recipient=tender.get("recipient","Procurement Team"),
        title=tender.get("title","Untitled"),
        sector_desc=tender.get("sector","Facilities Management").lower(),
        summary=tender.get("description","—"),
    )
    for line in body.split("\n"):
        doc.add_paragraph(line)

    doc.save(fpath)
    return str(fpath)

# ======================================
# HEADER
# ======================================
def logo_header():
    cols = st.columns([0.12, 0.88])
    with cols[0]:
        if LOGO_PATH.exists():
            st.image(Image.open(LOGO_PATH), use_container_width=True)
        else:
            st.write("**TFML**")
    with cols[1]:
        st.markdown(f"<div class='header'><div class='title'>Agentic AI Console</div></div>", unsafe_allow_html=True)
        st.caption("It’s all about you… • one-click drafting • faster BD • higher win rate")

# ======================================
# LOAD DATA
# ======================================
rows = load_rows()

# ======================================
# NAV TABS
# ======================================
tab_dash, tab_tenders, tab_drafts, tab_settings = st.tabs(
    ["Dashboard", "Tenders", "Drafts", "Settings"]
)

# ======================================
# DASHBOARD
# ======================================
with tab_dash:
    total = len(rows)
    due7 = sum(
        1 for r in rows
        if r.get("deadline") and
           datetime.strptime(r["deadline"], "%Y-%m-%d").date() >= datetime.today().date() and
           datetime.strptime(r["deadline"], "%Y-%m-%d").date() <= (datetime.today().date()+timedelta(days=7))
    )
    drafts = sum(1 for r in rows if r.get("status") == "Draft")
    submitted = sum(1 for r in rows if r.get("status") in ("Submitted","Pending"))

    c1,c2,c3,c4 = st.columns(4)
    for c, label, val, sub in (
        (c1,"Open tenders", total, "All active notices"),
        (c2,"Due in 7 days", due7, "Deadline pressure"),
        (c3,"Drafts ready", drafts, "Awaiting review"),
        (c4,"In flight", submitted, "Submitted or pending"),
    ):
        with c:
            st.markdown(f"<div class='kpi'><div class='label'>{label}</div><div class='value'>{val}</div><div class='sub'>{sub}</div></div>", unsafe_allow_html=True)

    if rows:
        df = pd.DataFrame(rows)
        st.markdown("##### Tenders by sector")
        chart = alt.Chart(df).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
            x=alt.X('sector:N', sort='-y', axis=alt.Axis(labelColor='black', title='')),
            y=alt.Y('count():Q', axis=alt.Axis(labelColor='black', title='Tenders')),
            color=alt.value(ACCENT)
        ).properties(height=260, background='transparent')
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No tenders yet.")

# ======================================
# TENDERS
# ======================================
with tab_tenders:
    st.markdown("### Tenders")
    df_view = pd.DataFrame(rows)

    # Ensure required columns exist
    required_cols = ["id","title","org","sector","doc_type","deadline","score"]
    for c in required_cols:
        if c not in df_view.columns:
            df_view[c] = ""

    if not df_view.empty:
        sel = st.data_editor(
            df_view[required_cols],
            hide_index=True,
            use_container_width=True,
            column_config={"score": st.column_config.NumberColumn(format="%.2f")},
            disabled=True,
            key="tender_table"
        )

        if st.button("✍️ Generate EOI for first tender"):
            tender = rows[0] if rows else {}
            if tender:
                path = write_docx(tender, "EOI")
                st.success(f"Generated draft: {os.path.basename(path)}")
                with open(path, "rb") as f:
                    st.download_button("📥 Download", f, file_name=os.path.basename(path))
    else:
        st.info("No tenders available.")

# ======================================
# DRAFTS
# ======================================
with tab_drafts:
    st.markdown("### Drafts Library")
    lib = []
    for r in rows:
        for d in r.get("drafts", []):
            lib.append({
                "Tender": r.get("title"),
                "Buyer": r.get("org"),
                "Type": d.get("type"),
                "File": d.get("file"),
                "Status": r.get("status","Draft"),
                "Deadline": r.get("deadline")
            })
    if not lib:
        st.info("No drafts yet.")
    else:
        df_lib = pd.DataFrame(lib)
        st.dataframe(df_lib, use_container_width=True, hide_index=True)

# ======================================
# SETTINGS
# ======================================
with tab_settings:
    st.markdown("### Settings")
    st.text_input("Default recipient", value="Procurement Team")
    st.text_input("Bid Office Email", value="bids@tfml.ng")
    st.text_input("Bid Office Phone", value="+234-XXX-XXXX")
    st.caption("Changes save automatically when generating drafts.")
