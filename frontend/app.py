import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st
import pandas as pd
import altair as alt
from PIL import Image
from docx import Document

# ======================================
# BRAND / LAYOUT
# ======================================
ACCENT = "#E60F18"       # TFML red
INK = "#0B0B0B"          # page bg (also in config.toml)
CARD = "#111315"
GRAY = "#8A8F98"

st.set_page_config(
    page_title="TFML Agentic AI — Luxe Console",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Paths (app is in /frontend)
BASE_DIR = Path(__file__).resolve().parent.parent   # project root
ASSETS = BASE_DIR / "assets"
LOGS = BASE_DIR / "logs"
EOIS = BASE_DIR / "eois"
TENDERS_JSON = LOGS / "tenders.json"
LOGO_PATH = ASSETS / "tfml_logo.png"

EOIS.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)

# ======================================
# GLOBAL CSS (luxury)
# ======================================
st.markdown(f"""
<style>
.stApp {{
  background: radial-gradient(1200px 800px at 20% -10%, rgba(230,15,24,0.08), transparent 60%),
              radial-gradient(900px 600px at 120% 10%, rgba(255,255,255,0.03), transparent 60%);
}}
.block-container {{ padding-top: 1.2rem; }}

.header {{
  display:flex; align-items:center; gap:14px; padding: 6px 0 14px 0; 
  border-bottom:1px solid rgba(255,255,255,0.06);
}}
.header .title {{ font-weight:900; font-size:26px; color:#fff; letter-spacing:.2px; }}
.header .tag  {{ color:{GRAY}; font-size:13px; margin-top:-6px; }}

.kpi {{
  background: linear-gradient(180deg, #151617 0%, #0D0E10 100%);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 18px; padding: 16px 18px; color: #fff;
  box-shadow: 0 20px 60px rgba(0,0,0,.35);
}}
.kpi .label {{ color:{GRAY}; font-size:.78rem; text-transform:uppercase; letter-spacing:1px; }}
.kpi .value {{ font-size:1.8rem; font-weight:800; }}
.kpi .sub   {{ color:{GRAY}; font-size:.78rem; }}

.pill {{ display:inline-block; padding: 2px 10px; border-radius: 999px; font-size: .75rem; font-weight: 700;
        background: #1d1f22; color: #f4f4f5; border: 1px solid #2a2a2e; }}
.pill.red {{ background: rgba(230,15,24,.12); color: #ff5c6a; border-color: rgba(230,15,24,.35); }}

.card {{ background: {CARD}; border:1px solid #1f1f1f; border-radius: 18px; padding: 18px; }}
.link a {{ color: #9ecbff; text-decoration:none; }}

.badge {{ display:inline-block; padding:3px 8px; border-radius:20px; font-size:11px; font-weight:700;
         color:#fff; background:{ACCENT}; margin-right:6px; }}

.btn {{
  background:{ACCENT}; color:#fff; padding:9px 14px; border-radius:12px; border:none; font-weight:800;
}}
.btn.ghost {{ background:transparent; border:1px solid #2a2a2a; color:#f3f3f3; }}
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

PROPOSAL_TMPL = """{org_name} — {doc_type} RESPONSE

Title: {title}
Buyer: {buyer}
Deadline: {deadline}

Executive Summary:
{exec_summary}

Methodology & Approach:
{approach}

Relevant Experience:
{relevant_experience}

Compliance & Certifications:
{compliance}

Team & Governance:
{team}

Contact:
{contact_name} | {contact_email} | {contact_phone}
"""

def write_docx(tender, doc_kind="EOI"):
    """Create a .docx draft in /eois for any doc type (EOI/Proposal/RFP/RFQ)."""
    safe_title = tender.get("title","Untitled")[:60].replace(" ", "_")
    fname = f"{safe_title}_{doc_kind}.docx"
    fpath = EOIS / fname

    doc = Document()
    if doc_kind.upper() == "EOI":
        recipient = tender.get("recipient", "Procurement Team")
        sector_desc = tender.get("sector","Facilities Management").lower()
        summary = tender.get("description","—")
        body = EOI_TMPL.format(
            recipient=recipient, title=tender.get("title","Untitled"),
            sector_desc=sector_desc, summary=summary
        )
        doc.add_heading("Expression of Interest", level=1)
        for line in body.split("\n"):
            doc.add_paragraph(line)
    else:
        # Proposal / RFP / RFQ template uses a richer structure
        body = PROPOSAL_TMPL.format(
            org_name="TFML",
            doc_type=doc_kind.upper(),
            title=tender.get("title","Untitled"),
            buyer=tender.get("org","—"),
            deadline=tender.get("deadline","—"),
            exec_summary=tender.get("exec_summary","Tailored summary to buyer goals and constraints."),
            approach=tender.get("approach","Outlined delivery plan covering scope, SLAs, HSE, quality."),
            relevant_experience=tender.get("relevant_experience","3–5 case studies aligned to buyer sector."),
            compliance=tender.get("compliance","ISO 41001 alignment, HSE policy, insurances, tax compliance."),
            team=tender.get("team","Key staff structure with roles and responsibilities."),
            contact_name=tender.get("contact_name","TFML Bid Office"),
            contact_email=tender.get("contact_email","bids@tfml.ng"),
            contact_phone=tender.get("contact_phone","+234-XXX-XXXX"),
        )
        doc.add_heading(f"{doc_kind.upper()} Draft", level=1)
        for part in body.split("\n\n"):
            if ":" in part.split("\n")[0]:
                # section with heading-like first line
                first, *rest = part.split("\n")
                doc.add_heading(first.strip(), level=2)
                doc.add_paragraph("\n".join(rest))
            else:
                doc.add_paragraph(part)

    doc.save(fpath)
    return str(fpath)

# ======================================
# UTILS
# ======================================
STATUS_COLORS = {"Draft":"red","Pending":"ghost","Submitted":"ghost","Won":"","Rejected":"ghost"}
def pill(status):
    style = STATUS_COLORS.get(status, "ghost")
    return f"<span class='pill {style}'>{status}</span>"

def logo_header():
    cols = st.columns([0.09, 0.91])
    with cols[0]:
        if LOGO_PATH.exists():
            st.image(Image.open(LOGO_PATH), use_container_width=True)
        else:
            st.markdown(f"**TFML**")
    with cols[1]:
        st.markdown(f"<div class='header'><div class='title'>Agentic AI Console</div></div>", unsafe_allow_html=True)
        st.caption("It’s all about you… • one-click drafting • faster BD • higher win rate")

# ======================================
# SIDEBAR (quick actions)
# ======================================
with st.sidebar:
    st.markdown("### Actions")
    mine_now = st.button("🔎 Mine new tenders (stub)")
    bulk_generate = st.button("⚡ Generate drafts for selected")
    st.markdown("---")
    st.caption("© TFML • OE Group")

# ======================================
# DATA LOAD (with optional stub mining)
# ======================================
rows = load_rows()

# stub: simulate mining by appending a sample tender
if mine_now:
    sample = {
        "id": f"TN-{int(time.time())}",
        "title": "Integrated FM Services — Lagos Operations",
        "org": "BlueWave Properties",
        "country": "Nigeria",
        "sector": "FM",
        "doc_type": "RFP",
        "deadline": (datetime.today()+timedelta(days=6)).strftime("%Y-%m-%d"),
        "score": 0.78,
        "description": "Comprehensive IFM for multi-site office estates. HSE & ISO alignment required.",
        "link": "https://example.com/bluewave-rfp"
    }
    rows.append(sample)
    save_rows(rows)
    st.toast("Mined 1 new tender (demo). Connect real miner to go live.", icon="🔎")

# ======================================
# HEADER
# ======================================
logo_header()

# ======================================
# NAV TABS
# ======================================
tab_dash, tab_tenders, tab_drafts, tab_orgs, tab_settings = st.tabs(
    ["Dashboard", "Tenders", "Drafts", "Organizations", "Settings"]
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
            x=alt.X('sector:N', sort='-y', axis=alt.Axis(labelColor='white', title='')),
            y=alt.Y('count():Q', axis=alt.Axis(labelColor='white', title='Tenders')),
            color=alt.value(ACCENT)
        ).properties(height=260, background='transparent')
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No tenders yet. Click **Mine new tenders** or add to logs/tenders.json.")

# ======================================
# TENDERS
# ======================================
with tab_tenders:
    st.markdown("### Tenders")
    left, right = st.columns([0.65, 0.35])

    with left:
        search = st.text_input("Search", placeholder="Title, buyer, sector…")
        colf1, colf2, colf3 = st.columns(3)
        with colf1:
            f_sector = st.selectbox("Sector", ["All"] + sorted(list({r.get("sector","-") for r in rows})))
        with colf2:
            f_type = st.selectbox("Doc type", ["All","EOI","Proposal","RFP","RFQ"])
        with colf3:
            sort_by = st.selectbox("Sort by", ["Deadline","Score","Title"])

        view = rows
        if search:
            q = search.lower()
            view = [r for r in view if q in r.get("title","").lower() or q in r.get("description","").lower() or q in r.get("org","").lower()]
        if f_sector != "All":
            view = [r for r in view if r.get("sector")==f_sector]
        if f_type != "All":
            view = [r for r in view if r.get("doc_type","").upper()==f_type.upper()]

        # Sorting
        if sort_by == "Deadline":
            def _key(r):
                try:
                    return datetime.strptime(r.get("deadline","3000-01-01"), "%Y-%m-%d")
                except:
                    return datetime(3000,1,1)
            view = sorted(view, key=_key)
        elif sort_by == "Score":
            view = sorted(view, key=lambda r: r.get("score",0), reverse=True)
        else:
            view = sorted(view, key=lambda r: r.get("title",""))

        # Multi-select table for bulk draft
        if view:
            df_view = pd.DataFrame(view)
            sel = st.data_editor(
                df_view[["id","title","org","sector","doc_type","deadline","score"]],
                hide_index=True,
                use_container_width=True,
                column_config={"score": st.column_config.NumberColumn(format="%.2f")},
                disabled=True,
                key="tender_table"
            )
        else:
            st.info("No tenders match your filters.")
            sel = pd.DataFrame()

    with right:
        st.markdown("#### Draft response (one-click)")
        doc_choice = st.selectbox("Draft type", ["EOI","Proposal","RFP","RFQ"], index=0)
        go = st.button("✍️ Generate draft for highlighted rows")
        if go:
            # Which rows? Use filtered view (sel) indices back to rows by id
            selected_ids = sel["id"].tolist() if not sel.empty else []
            selected = [r for r in view if r.get("id") in selected_ids] if selected_ids else view[:1]  # default: first row
            created = []
            for r in selected:
                path = write_docx(r, doc_kind=doc_choice)
                r.setdefault("drafts", []).append({"type":doc_choice, "file":path, "ts":time.time()})
                r["status"] = r.get("status") or "Draft"
                created.append(Path(path).name)
            save_rows(rows)
            if created:
                st.success(f"Generated: {', '.join(created)}")
            else:
                st.warning("No rows selected.")

        st.markdown("#### Quick info")
        st.caption("• EOI/Proposal/RFP/RFQ drafts are customized with buyer/org fields.\n• Hook this button to your backend LLM chain for richer text.")

    st.markdown("---")
    st.caption("Tip: bulk-select in the table, pick a draft type → **Generate**.")

# ======================================
# DRAFTS (Library / Kanban-lite)
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
        st.info("No drafts yet. Generate from **Tenders**.")
    else:
        df_lib = pd.DataFrame(lib)
        st.dataframe(df_lib, use_container_width=True, hide_index=True)
        for rec in lib:
            with st.expander(f"{rec['Type']} • {rec['Tender']}"):
                fpath = rec["File"]
                if fpath and os.path.exists(fpath):
                    with open(fpath, "rb") as f:
                        st.download_button("📥 Download .docx", f, file_name=os.path.basename(fpath))
                st.caption(f"Buyer: {rec['Buyer']} • Deadline: {rec['Deadline']} • Status: {rec['Status']}")

# ======================================
# ORGANIZATIONS (Lead sourcing)
# ======================================
with tab_orgs:
    st.markdown("### Organizations (Prospects)")
    # Minimal, in-memory list (replace with your DB later)
    orgs_store = st.session_state.setdefault("orgs_store", [
        {"name":"Afreximbank","sector":"Financial Services","country":"Nigeria","website":"https://afreximbank.com","prospect_score":0.92},
        {"name":"MTN Nigeria","sector":"Telecom","country":"Nigeria","website":"https://mtn.ng","prospect_score":0.81},
    ])

    # Add new prospect
    with st.popover("➕ Add organization"):
        c1,c2 = st.columns(2)
        with c1:
            oname = st.text_input("Name")
            osec = st.text_input("Sector")
            ocountry = st.text_input("Country", value="Nigeria")
        with c2:
            oweb = st.text_input("Website", value="https://")
            oscore = st.number_input("Prospect score", min_value=0.0, max_value=1.0, value=0.65, step=0.01)
        if st.button("Save organization"):
            if oname:
                orgs_store.append({"name":oname,"sector":osec,"country":ocountry,"website":oweb,"prospect_score":oscore})
                st.success("Organization added.")
            else:
                st.warning("Name is required.")

    st.dataframe(pd.DataFrame(orgs_store), use_container_width=True, hide_index=True)

    st.markdown("#### Source new prospects (stub)")
    st.caption("This button would call your sourcing agent to find orgs by sector/region and enrich their profiles.")
    if st.button("🌍 Source organizations now"):
        st.toast("Sourcing started (demo). Connect real agent in backend.", icon="🌐")

# ======================================
# SETTINGS
# ======================================
with tab_settings:
    st.markdown("### Settings")
    st.write("Configure defaults for draft content and contacts.")
    st.text_input("Default recipient", value="Procurement Team")
    st.text_input("Bid Office Email", value="bids@tfml.ng")
    st.text_input("Bid Office Phone", value="+234-XXX-XXXX")
    st.caption("Saving occurs when you generate or update drafts.")
