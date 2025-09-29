import streamlit as st
import pandas as pd
import altair as alt
import json
import os
from datetime import datetime, timedelta
from docx import Document

# =============================
# THEME & BRAND (OE Group: red/black/white)
# =============================
ACCENT = "#E50914"       # luxe red
INK = "#0B0B0B"          # rich black
PAPER = "#FFFFFF"        # clean white
INK_SOFT = "#141414"
GRAY = "#8A8A8A"
CARD = "#111214"

st.set_page_config(
    page_title="TFML Agentic AI — Luxe Console",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Global CSS for luxury look
st.markdown(f"""
    <style>
        :root {{ --accent: {ACCENT}; --ink: {INK}; --paper: {PAPER}; --card: {CARD}; --gray: {GRAY}; }}
        .stApp {{ background: radial-gradient(1200px 700px at 20% -10%, #1a1a1a 0%, #0b0b0b 60%) fixed; }}
        .block-container {{ padding: 2.2rem 3rem 4rem; }}
        h1, h2, h3, h4, h5 {{ color: var(--paper); letter-spacing: .2px; }}
        .headline {{
            font-size: 2.2rem; font-weight: 800; color: var(--paper); margin: .3rem 0 1.2rem;
        }}
        .subtle {{ color: #cfcfcf; font-size: .95rem; }}
        .kpi {{
            background: linear-gradient(180deg, #151515 0%, #0f0f0f 100%);
            border: 1px solid #1f1f1f; border-radius: 18px; padding: 16px 18px; color: var(--paper);
            box-shadow: 0 2px 0 rgba(255,255,255,.05) inset, 0 20px 60px rgba(0,0,0,.35);
        }}
        .kpi .label {{ color: #bdbdbd; font-size: .8rem; }}
        .kpi .value {{ font-size: 1.8rem; font-weight: 700; }}
        .pill {{
            display:inline-block; padding: 2px 10px; border-radius: 999px; font-size: .75rem; font-weight: 600;
            background: #1d1d1f; color: #f4f4f5; border: 1px solid #2a2a2e;
        }}
        .pill.red {{ background: rgba(229,9,20,.12); color: #ff5c6a; border-color: rgba(229,9,20,.35); }}
        .btn {{
            background: var(--accent); color: white; padding: 8px 14px; border-radius: 12px; border: none; font-weight: 700;
        }}
        .btn.ghost {{ background: transparent; border: 1px solid #2a2a2a; color: #f3f3f3; }}
        .card {{ background: var(--card); border:1px solid #1f1f1f; border-radius: 18px; padding: 18px; }}
        .muted {{ color: #c9c9c9; }}
        .link a {{ color: #9ecbff; text-decoration:none; }}
        .danger {{ color:#ff6b6b; }}
    </style>
""", unsafe_allow_html=True)

# =============================
# DATA LAYER
# =============================
DATA_PATH = os.path.join("..", "logs", "tenders.json")
EOI_DIR = os.path.join("..", "eois")
os.makedirs(EOI_DIR, exist_ok=True)

def load_tenders():
    try:
        with open(DATA_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_tenders(rows):
    with open(DATA_PATH, "w") as f:
        json.dump(rows, f, indent=2)

# =============================
# EOI GENERATOR (templated)
# =============================
EOI_TMPL = """
Dear {recipient},

Total Facilities Management Limited (TFML) is pleased to express interest in the tender titled "{title}". With a strong track record delivering {sector_desc}, our team is positioned to meet your outcomes on quality, compliance and timelines.

Scope alignment (summary):
{summary}

TFML offers certified personnel, SLAs, HSE compliance and proven delivery for public and private estates nationwide. We welcome the opportunity to submit full technical and financial proposals upon request.

Sincerely,
TFML Bid Office
"""

def write_eoi_docx(tender):
    fname = f"{tender['title'][:60].replace(' ', '_')}.docx"
    fpath = os.path.join(EOI_DIR, fname)
    # generate text
    recipient = tender.get("recipient", "Procurement Team")
    sector_desc = tender.get("sector", "Facilities Management").lower()
    summary = tender.get("description", "—")
    body = EOI_TMPL.format(recipient=recipient, title=tender['title'], sector_desc=sector_desc, summary=summary)
    doc = Document()
    doc.add_heading("Expression of Interest", level=1)
    for line in body.split("\n"):
        doc.add_paragraph(line)
    doc.save(fpath)
    return fpath

# =============================
# HELPERS
# =============================
STATUS_COLORS = {
    "Draft": "red",
    "Pending": "ghost",
    "Sent": "ghost",
    "Won": "",
}

def status_pill(status):
    style = STATUS_COLORS.get(status, "ghost")
    return f"<span class='pill {style}'>{status}</span>"

# =============================
# SIDEBAR NAV
# =============================
with st.sidebar:
    st.image("https://dummyimage.com/600x140/0b0b0b/ffffff&text=TFML+×+OE+Group", use_column_width=True)
    st.markdown("<div class='subtle'>Agentic Console</div>", unsafe_allow_html=True)
    page = st.radio("", ["Dashboard", "Tenders", "EOIs", "Outreach", "Settings"], index=0)
    st.markdown("---")
    search = st.text_input("Quick search", placeholder="Search title, sector, keyword…")
    st.caption("© TFML • Built for speed and clarity")

# Load data once
rows = load_tenders()

# Optional search filter
if search:
    q = search.lower()
    rows = [r for r in rows if q in r.get("title", "").lower() or q in r.get("description", "").lower()]

# =============================
# DASHBOARD
# =============================
if page == "Dashboard":
    st.markdown("<div class='headline'>TFML Agentic AI Console</div>", unsafe_allow_html=True)
    # KPIs
    total = len(rows)
    due7 = sum(1 for r in rows if r.get("deadline") and r["deadline"] >= str(datetime.today().date()) and datetime.strptime(r["deadline"], "%Y-%m-%d").date() <= datetime.today().date() + timedelta(days=7))
    drafts = sum(1 for r in rows if r.get("status") == "Draft")
    sent = sum(1 for r in rows if r.get("status") in ("Sent","Submitted","Pending"))

    c1, c2, c3, c4 = st.columns(4)
    for c, label, val in (
        (c1, "Open tenders", total),
        (c2, "Due in 7 days", due7),
        (c3, "Drafts ready", drafts),
        (c4, "In flight", sent),
    ):
        with c:
            st.markdown(f"<div class='kpi'><div class='label'>{label}</div><div class='value'>{val}</div></div>", unsafe_allow_html=True)

    # Simple bar by sector
    if rows:
        df = pd.DataFrame(rows)
        chart = alt.Chart(df).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
            x=alt.X('sector:N', sort='-y', axis=alt.Axis(labelColor='white', title='')),
            y=alt.Y('count():Q', axis=alt.Axis(labelColor='white', title='Tenders')),
            color=alt.value(ACCENT)
        ).properties(height=260, background='transparent')
        st.markdown("### ")
        st.altair_chart(chart, use_container_width=True)

# =============================
# TENDERS LIST & ACTIONS
# =============================
if page == "Tenders":
    st.markdown("<div class='headline'>Tenders</div>", unsafe_allow_html=True)
    colf1, colf2, colf3 = st.columns([1,1,1])
    with colf1:
        f_sector = st.selectbox("Sector", ["All"] + sorted(list({r.get("sector","-") for r in rows})))
    with colf2:
        f_status = st.selectbox("Status", ["All", "Draft", "Pending", "Sent", "Won"])
    with colf3:
        sort_by = st.selectbox("Sort by", ["Deadline", "Score", "Title"])

    # apply filters
    view = rows
    if f_sector != "All":
        view = [r for r in view if r.get("sector") == f_sector]
    if f_status != "All":
        view = [r for r in view if r.get("status") == f_status]

    # sorting
    if sort_by == "Deadline":
        def _key(r):
            try:
                return datetime.strptime(r.get("deadline","3000-01-01"), "%Y-%m-%d")
            except: return datetime(3000,1,1)
        view = sorted(view, key=_key)
    elif sort_by == "Score":
        view = sorted(view, key=lambda r: r.get("score",0), reverse=True)
    else:
        view = sorted(view, key=lambda r: r.get("title",""))

    # render cards
    if not view:
        st.info("No tenders match your filters.")
    for i, t in enumerate(view):
        with st.container():
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            top = st.columns([6,2,2,2])
            with top[0]:
                st.markdown(f"**{t['title']}**  "+status_pill(t.get('status','Draft')), unsafe_allow_html=True)
                st.caption(t.get("description","—"))
                meta = []
                if t.get("sector"): meta.append(f"Sector: {t['sector']}")
                if t.get("deadline"): meta.append(f"Deadline: {t['deadline']}")
                if t.get("score") is not None: meta.append(f"Score: {t['score']}")
                st.markdown(" · ".join([f"<span class='muted'>{m}</span>" for m in meta]), unsafe_allow_html=True)
                if t.get("link"):
                    st.markdown(f"<div class='link'>🔗 <a href='{t['link']}' target='_blank'>Open tender</a></div>", unsafe_allow_html=True)
                if t.get("submission_link"):
                    st.markdown(f"<div class='link'>📬 <a href='{t['submission_link']}' target='_blank'>Submission portal</a></div>", unsafe_allow_html=True)
                if t.get("submission_email"):
                    st.markdown(f"<span class='muted'>📮 Submit to: <b>{t['submission_email']}</b></span>", unsafe_allow_html=True)

            with top[1]:
                if st.button("✍️ Generate EOI", key=f"gen_{i}"):
                    path = write_eoi_docx(t)
                    t["eoi"] = path
                    t["status"] = t.get("status") or "Draft"
                    save_tenders(rows)
                    st.success("EOI generated.")
            with top[2]:
                default = t.get("eoi") and os.path.exists(t["eoi"]) 
                if default:
                    with open(t["eoi"], "rb") as f:
                        st.download_button("📄 Download EOI", f, file_name=os.path.basename(t["eoi"]), mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", key=f"dl_{i}")
                else:
                    st.button("📄 Download EOI", key=f"dl_disabled_{i}", disabled=True)
            with top[3]:
                new_status = st.selectbox("Status", ["Draft","Pending","Sent","Won","Rejected"], index=["Draft","Pending","Sent","Won","Rejected"].index(t.get("status","Draft")), key=f"status_{i}")
                if new_status != t.get("status"):
                    t["status"] = new_status
                    save_tenders(rows)
                    st.toast("Status updated", icon="✅")
            st.markdown("</div>", unsafe_allow_html=True)

# =============================
# EOI LIBRARY
# =============================
if page == "EOIs":
    st.markdown("<div class='headline'>EOI Library</div>", unsafe_allow_html=True)
    eois = [r for r in rows if r.get("eoi")]
    if not eois:
        st.info("No EOIs yet. Generate from the Tenders tab.")
    else:
        df = pd.DataFrame([
            {"Title": r.get("title"), "Sector": r.get("sector"), "Deadline": r.get("deadline"), "Status": r.get("status"), "File": os.path.basename(r.get("eoi"))}
            for r in eois
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)
        for r in eois:
            with st.expander(f"{r['title']}"):
                with open(r["eoi"], "rb") as f:
                    st.download_button("Download .docx", f, file_name=os.path.basename(r["eoi"]))
                st.caption(r.get("description","—"))

# =============================
# OUTREACH (placeholder for emails)
# =============================
if page == "Outreach":
    st.markdown("<div class='headline'>Outreach</div>", unsafe_allow_html=True)
    st.write("Compose an email to the submission contact or export a cover letter.")
    subj = st.text_input("Subject", value="Expression of Interest — TFML")
    body = st.text_area("Email body", height=220, value="Dear Procurement Team,\n\nPlease find attached our Expression of Interest.\n\nRegards,\nTFML Bid Office")
    st.button("Send (wire-up SMTP later)")

# =============================
# SETTINGS
# =============================
if page == "Settings":
    st.markdown("<div class='headline'>Settings</div>", unsafe_allow_html=True)
    st.write("Configure defaults for EOI generation and display.")
    recip = st.text_input("Default recipient", value="Procurement Team")
    st.caption("Saving occurs automatically when you change statuses or generate EOIs.")
