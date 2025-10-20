# TFML Agentic AI — Luxe Console (Full App with Upgraded Tenders + Seeded EOIs)
# -----------------------------------------------------------------------------
# - Tabs visibility fixed (light + dark)
# - Executive Dashboard unchanged (already improved previously)
# - Tenders page overhauled: Filters, List/Kanban/Calendar, bulk actions, inline actions
# - Seeder: 6 placeholder tenders + auto-generated EOIs
# - Safe notices (no key= on status messages)

import os
import json
import time
from datetime import datetime, timedelta, date
from pathlib import Path
import sqlite3
import streamlit as st
import pandas as pd
import altair as alt
from docx import Document
from PIL import Image
import requests  # Placeholder for external API

# ======================================
# PATHS AND CONFIG
# ======================================
try:
    BASE_DIR = Path(__file__).resolve().parent
except NameError:
    BASE_DIR = Path.cwd()

ASSETS = BASE_DIR / "assets"
LOGS = BASE_DIR / "logs"
EOIS = BASE_DIR / "eois"
TENDERS_DB = LOGS / "tenders.db"
LOGO_PATH = ASSETS / "tfml_logo.png"

EOIS.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)

# Theme
ACCENT = "#E60F18"      # TFML Red
CARD = "#FFFFFF"        # White for cards
TEXT = "#000000"        # Black text
MUTED = "#555555"       # Muted gray
APP_BG_LIGHT = "#F9F9F9"
APP_BG_DARK = "#1E1E1E"
CARD_DARK = "#2A2A2A"

st.set_page_config(
    page_title="TFML Agentic AI — Luxe Console",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ======================================
# CSS (tabs fix + dark mode + cards)
# ======================================
st.markdown(f"""
<style>
/* Base */
.stApp {{
    background: {APP_BG_LIGHT};
    color: {TEXT};
}}
.block-container {{ padding-top: 1rem; }}

/* Header */
.header {{
    display:flex;
    align-items:center;
    gap:14px;
    padding: 6px 0 14px 0;
    border-bottom:1px solid #ddd;
}}
.header .title {{
    font-weight:900;
    font-size:26px;
    color: {ACCENT};
    letter-spacing:.2px;
}}

/* Cards & KPIs */
.kpi {{
    background: {CARD};
    border: 1px solid #ddd;
    border-radius: 14px;
    padding: 16px;
    color: {TEXT};
}}
.kpi .label {{
    color: {MUTED};
    font-size:.78rem;
    text-transform:uppercase;
    letter-spacing:1px;
}}
.kpi .value {{
    font-size:1.8rem;
    font-weight:800;
    color: {ACCENT};
}}
.card {{
    background: {CARD};
    border:1px solid #ddd;
    border-radius: 14px;
    padding: 16px;
    color: {TEXT};
}}
.pill {{
    display:inline-block;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: .75rem;
    font-weight: 700;
    background: #eee;
    color: {ACCENT};
    border: 1px solid {ACCENT};
}}

/* Tabs — explicit styling to ensure readability */
.stTabs [role="tablist"] {{
    gap: 8px !important;
    border-bottom: 0;
    margin-bottom: 0.5rem;
}}
.stTabs [role="tab"] {{
    padding: 10px 16px !important;
    border: 1px solid #ddd !important;
    background: #fff !important;
    color: #000 !important;
    border-top-left-radius: 10px !important;
    border-top-right-radius: 10px !important;
    font-weight: 700 !important;
    opacity: 1 !important;
}}
.stTabs [role="tab"][aria-selected="true"] {{
    background: {ACCENT} !important;
    color: #fff !important;
    border-color: {ACCENT} !important;
}}

/* Dark Mode */
.dark-mode .stApp {{
    background: {APP_BG_DARK};
    color: #FFFFFF;
}}
.dark-mode .kpi {{
    background: {CARD_DARK};
    border-color: #444;
    color: #FFFFFF;
}}
.dark-mode .kpi .value {{ color: #FFFFFF; }}
.dark-mode .card {{
    background: {CARD_DARK};
    border-color: #444;
    color: #FFFFFF;
}}
.dark-mode .header .title {{ color: #FFFFFF; }}
.dark-mode .pill {{
    background: #444;
    color: #FFFFFF;
    border-color: #FFFFFF;
}}

/* Tabs in dark mode */
.dark-mode .stTabs [role="tab"] {{
    background: {CARD_DARK} !important;
    border-color: #444 !important;
    color: #fff !important;
}}
.dark-mode .stTabs [role="tab"][aria-selected="true"] {{
    background: {ACCENT} !important;
    border-color: {ACCENT} !important;
    color: #fff !important;
}}

@media (max-width: 600px) {{
    .kpi {{ padding: 10px; }}
    .kpi .value {{ font-size: 1.4rem; }}
    .header .title {{ font-size: 20px; }}
}}
</style>
""", unsafe_allow_html=True)

# ======================================
# DATABASE
# ======================================
def init_db():
    conn = sqlite3.connect(TENDERS_DB)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS tenders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        org TEXT,
        sector TEXT,
        deadline TEXT,
        description TEXT,
        status TEXT,
        score REAL,
        assignee TEXT,
        drafts TEXT
    )
    """)
    conn.commit()
    conn.close()

def load_rows():
    try:
        conn = sqlite3.connect(TENDERS_DB)
        c = conn.cursor()
        c.execute("SELECT * FROM tenders")
        rows = [
            {
                "id": r[0], "title": r[1], "org": r[2], "sector": r[3],
                "deadline": r[4], "description": r[5], "status": r[6],
                "score": r[7], "assignee": r[8],
                "drafts": json.loads(r[9]) if r[9] else []
            }
            for r in c.fetchall()
        ]
        conn.close()
        return rows
    except Exception as e:
        st.error(f"Error loading tenders: {e}")
        return []

def save_row(tender):
    try:
        conn = sqlite3.connect(TENDERS_DB)
        c = conn.cursor()
        c.execute("""
        INSERT OR REPLACE INTO tenders (id, title, org, sector, deadline, description, status, score, assignee, drafts)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tender.get("id"), tender.get("title"), tender.get("org"), tender.get("sector"),
            tender.get("deadline"), tender.get("description"), tender.get("status"),
            tender.get("score", 0.0), tender.get("assignee", ""), json.dumps(tender.get("drafts", []))
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Error saving tender: {e}")

def delete_row(tender_id):
    try:
        conn = sqlite3.connect(TENDERS_DB)
        c = conn.cursor()
        c.execute("DELETE FROM tenders WHERE id = ?", (tender_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Error deleting tender: {e}")

# Initialize DB
init_db()

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

def write_docx(tender, doc_kind="EOI", version=1):
    try:
        safe_title = tender.get("title", "Untitled")[:60].replace(" ", "_")
        fname = f"{safe_title}_{doc_kind}_v{version}.docx"
        fpath = EOIS / fname
        doc = Document()
        doc.add_heading(f"{doc_kind} Draft (v{version})", level=1)
        body = EOI_TMPL.format(
            recipient=tender.get("recipient", st.session_state.get("default_recipient", "Procurement Team")),
            title=tender.get("title", "Untitled"),
            sector_desc=tender.get("sector", "Facilities Management").lower(),
            summary=tender.get("description", "—"),
        )
        for line in body.split("\n"):
            doc.add_paragraph(line)
        doc.save(fpath)
        return str(fpath)
    except Exception as e:
        st.error(f"Error generating document: {e}")
        return None

# ======================================
# AI PLACEHOLDER
# ======================================
def ai_summarize(description):
    return f"Summary: {description[:180]}..."  # Replace with real AI call later

# ======================================
# UTILITIES
# ======================================
def _safe_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None

# ======================================
# SEEDER (6 placeholder tenders + generated EOIs)
# ======================================
def seed_sample_data_if_empty():
    rows_now = load_rows()
    if rows_now:
        return rows_now

    today = date.today()
    samples = [
        {
            "title": "IFMA Abuja Secretariat FM Services",
            "org": "IFMA Nigeria",
            "sector": "Facilities Management",
            "deadline": (today + timedelta(days=6)).strftime("%Y-%m-%d"),
            "description": "Provision of integrated FM services (hard + soft) for IFMA Secretariat building in Abuja, including planned preventive maintenance, SLA reporting, and helpdesk.",
            "status": "Draft",
            "assignee": "bids@tfml.ng",
        },
        {
            "title": "AATC HQ Janitorial & Waste Management",
            "org": "Afreximbank AATC",
            "sector": "Facilities Management",
            "deadline": (today + timedelta(days=12)).strftime("%Y-%m-%d"),
            "description": "Comprehensive janitorial, pest control, and waste management services for AATC HQ office complex with quarterly deep-clean and ISO-aligned documentation.",
            "status": "Submitted",
            "assignee": "enoch@tfml.ng",
        },
        {
            "title": "Wuse District Streetlighting Retrofit",
            "org": "FCTA",
            "sector": "Energy",
            "deadline": (today + timedelta(days=3)).strftime("%Y-%m-%d"),
            "description": "LED retrofit and solar hybridization for Wuse district arterial roads, including energy audit and post-implementation M&V.",
            "status": "Pending",
            "assignee": "femi@tfml.ng",
        },
        {
            "title": "MTN Regional Hub M&E Maintenance",
            "org": "MTN Nigeria",
            "sector": "Construction",
            "deadline": (today + timedelta(days=20)).strftime("%Y-%m-%d"),
            "description": "HVAC, power distribution, fire systems and generator maintenance for MTN regional hub; 24/7 response; CMMS-based reporting.",
            "status": "Draft",
            "assignee": "greg@tfml.ng",
        },
        {
            "title": "Airport Concourse Cleaning & Consumables",
            "org": "FAAN",
            "sector": "Facilities Management",
            "deadline": (today + timedelta(days=9)).strftime("%Y-%m-%d"),
            "description": "Terminal concourse cleaning, restrooms, and traveler touchpoints with IoT counters and predictive replenishment for consumables.",
            "status": "Submitted",
            "assignee": "bids@tfml.ng",
        },
        {
            "title": "Data Centre Critical Environment FM",
            "org": "NIBSS",
            "sector": "Facilities Management",
            "deadline": (today + timedelta(days=1)).strftime("%Y-%m-%d"),
            "description": "Tier-III data centre operations: chilled water, precision cooling, UPS, fire suppression; 15-min incident response; trained critical environment techs.",
            "status": "Draft",
            "assignee": "ops@tfml.ng",
        },
    ]

    rows_seeded = []
    for i, s in enumerate(samples, start=1):
        tender = {
            "id": i,
            "title": s["title"],
            "org": s["org"],
            "sector": s["sector"],
            "deadline": s["deadline"],
            "description": s["description"],
            "status": s["status"],
            "score": 0.0,
            "assignee": s["assignee"],
            "drafts": []
        }
        save_row(tender)
        # Generate 1 EOI draft for each seeded tender to give 'real' feel
        path = write_docx(tender, "EOI", version=1)
        if path:
            tender["drafts"] = [{"type": "EOI", "file": path, "version": 1}]
            save_row(tender)
        rows_seeded.append(tender)

    return load_rows()

# ======================================
# EMAIL PLACEHOLDER
# ======================================
def send_email(recipient, subject, body, attachment_path):
    st.success(f"Email sent to {recipient} with attachment {attachment_path}")

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
        st.markdown(f"<span style='color:{ACCENT};opacity:.9;'>It’s all about you… • one-click drafting • faster BD • higher win rate</span>", unsafe_allow_html=True)

# Render header BEFORE tabs
logo_header()

# ======================================
# LOAD DATA + NOTICES
# ======================================
rows = seed_sample_data_if_empty()

def render_deadline_notices(rows, days=3):
    today = datetime.today().date()
    soon = today + timedelta(days=days)
    for r in rows:
        d = _safe_date(r.get("deadline"))
        if d and d <= soon:
            title = r.get("title", "Untitled")
            st.warning(f"⚠️ Tender '{title}' is due on {d.strftime('%Y-%m-%d')}!")

render_deadline_notices(rows, days=3)

# ======================================
# DASHBOARD HELPERS (unchanged from your improved version)
# ======================================
def compute_dashboard_metrics(rows):
    today = datetime.today().date()
    in_7 = today + timedelta(days=7)
    in_3 = today + timedelta(days=3)

    total = len(rows)
    deadlines = [(_safe_date(r.get("deadline")), r) for r in rows]
    overdue = [r for d, r in deadlines if d and d < today and r.get("status") not in ("Awarded", "Won", "Lost")]
    due3 = [r for d, r in deadlines if d and today <= d <= in_3]
    due7 = [r for d, r in deadlines if d and today <= d <= in_7]
    drafts = [r for r in rows if r.get("status") == "Draft"]
    inflight = [r for r in rows if r.get("status") in ("Submitted", "Pending")]
    awarded = [r for r in rows if r.get("status") in ("Awarded", "Won")]
    decided = [r for r in rows if r.get("status") in ("Awarded", "Won", "Lost")]

    win_rate = round((len(awarded) / len(decided) * 100.0), 1) if decided else 0.0

    # Assignee workload
    by_assignee = {}
    for r in rows:
        a = (r.get("assignee") or "Unassigned").strip() or "Unassigned"
        by_assignee[a] = by_assignee.get(a, 0) + 1

    # Upcoming 30-day deadline load
    next30 = []
    for d, r in deadlines:
        if d and today <= d <= (today + timedelta(days=30)):
            next30.append(d)
    df_next30 = (
        pd.Series(next30, name="date")
        .value_counts()
        .rename_axis("date")
        .reset_index(name="tenders")
        .sort_values("date")
        if next30 else pd.DataFrame(columns=["date", "tenders"])
    )

    # Activity feed from drafts
    feed = []
    for r in rows:
        for d in r.get("drafts", []):
            feed.append({
                "when": os.path.getmtime(d.get("file")) if d.get("file") and os.path.exists(d["file"]) else time.time(),
                "tender": r.get("title", "Untitled"),
                "type": d.get("type", "Doc"),
                "file": os.path.basename(d.get("file") or ""),
                "version": d.get("version", 1),
                "status": r.get("status", "")
            })
    feed_df = pd.DataFrame(feed)
    if not feed_df.empty:
        feed_df["when"] = pd.to_datetime(feed_df["when"], unit="s")
        feed_df = feed_df.sort_values("when", ascending=False)

    return {
        "total": total,
        "overdue": len(overdue),
        "due3": len(due3),
        "due7": len(due7),
        "drafts": len(drafts),
        "inflight": len(inflight),
        "awarded": len(awarded),
        "win_rate": win_rate,
        "overdue_list": overdue,
        "soon_list": sorted([r for r in rows if _safe_date(r.get("deadline"))], key=lambda x: _safe_date(x["deadline"]))[:10],
        "assignee_counts": by_assignee,
        "deadline_30": df_next30,
        "activity": feed_df
    }

# ======================================
# TABS
# ======================================
tab_dash, tab_tenders, tab_drafts, tab_settings = st.tabs(["Dashboard", "Tenders", "Drafts", "Settings"])

# ======================================
# DASHBOARD (kept from your improved version)
# ======================================
with tab_dash:
    st.markdown("#### Executive Overview")
    m = compute_dashboard_metrics(rows)

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.markdown(f"<div class='kpi'><div class='label'>Total</div><div class='value'>{m['total']}</div><div class='sub'>All notices</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='kpi'><div class='label'>Overdue</div><div class='value'>{m['overdue']}</div><div class='sub'>Past deadline</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='kpi'><div class='label'>Due in 3 days</div><div class='value'>{m['due3']}</div><div class='sub'>Immediate action</div></div>", unsafe_allow_html=True)
    with c4:
        st.markdown(f"<div class='kpi'><div class='label'>Due in 7 days</div><div class='value'>{m['due7']}</div><div class='sub'>Upcoming</div></div>", unsafe_allow_html=True)
    with c5:
        st.markdown(f"<div class='kpi'><div class='label'>In Flight</div><div class='value'>{m['inflight']}</div><div class='sub'>Submitted/Pending</div></div>", unsafe_allow_html=True)
    with c6:
        st.markdown(f"<div class='kpi'><div class='label'>Win rate</div><div class='value'>{m['win_rate']}%</div><div class='sub'>Awards: {m['awarded']}</div></div>", unsafe_allow_html=True)

    st.markdown("---")

    left, right = st.columns([0.6, 0.4])

    with left:
        if rows:
            df = pd.DataFrame(rows)
            df["deadline_dt"] = pd.to_datetime(df["deadline"], errors="coerce")

            st.markdown("##### Tenders by Sector")
            sector_chart = alt.Chart(df).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
                x=alt.X('sector:N', sort='-y', title=''),
                y=alt.Y('count():Q', title='Tenders'),
                tooltip=['sector', 'count()'],
                color=alt.Color('sector:N', scale=alt.Scale(scheme='category10'), legend=None)
            ).properties(height=220, background='transparent')
            st.altair_chart(sector_chart, use_container_width=True)

            st.markdown("##### Pipeline Status")
            df_status = df.copy()
            if "status" not in df_status.columns:
                df_status["status"] = "Draft"
            donut = alt.Chart(df_status).mark_arc(innerRadius=70).encode(
                theta=alt.Theta("count():Q"),
                color=alt.Color("status:N", scale=alt.Scale(scheme='category10')),
                tooltip=["status", "count()"]
            ).properties(height=240)
            st.altair_chart(donut, use_container_width=True)

            st.markdown("##### Deadline Load (Next 30 Days)")
            if not compute_dashboard_metrics(rows)["deadline_30"].empty:
                area = alt.Chart(compute_dashboard_metrics(rows)["deadline_30"]).mark_area(opacity=0.6).encode(
                    x=alt.X("date:T", title="Date"),
                    y=alt.Y("tenders:Q", title="Count"),
                    tooltip=["date:T", "tenders:Q"]
                ).properties(height=220)
                st.altair_chart(area, use_container_width=True)
            else:
                st.info("No deadlines in the next 30 days.")
        else:
            st.info("No tenders yet. Add a few to unlock insights.")

    with right:
        st.markdown("##### Smart Alerts")
        if m["overdue"] > 0:
            st.error(f"{m['overdue']} tender(s) are overdue. Prioritise these now.")
        elif m["due3"] > 0:
            st.warning(f"{m['due3']} tender(s) due in 3 days.")
        elif m["due7"] > 0:
            st.warning(f"{m['due7']} tender(s) due in 7 days.")
        else:
            st.success("All clear. No urgent deadlines.")

        st.markdown("##### Workload by Assignee")
        ass_df = pd.DataFrame([{"Assignee": k, "Tenders": v} for k, v in m["assignee_counts"].items()])
        if not ass_df.empty:
            bar = alt.Chart(ass_df).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
                x=alt.X("Assignee:N", sort='-y', title=''),
                y=alt.Y("Tenders:Q", title="Count"),
                tooltip=["Assignee", "Tenders"]
            ).properties(height=220)
            st.altair_chart(bar, use_container_width=True)
        else:
            st.info("No assignments yet.")

        st.markdown("##### Top Upcoming Deadlines")
        soon = []
        for r in m["soon_list"]:
            d = _safe_date(r.get("deadline"))
            soon.append({
                "Deadline": d.strftime("%Y-%m-%d") if d else "",
                "Title": r.get("title", ""),
                "Status": r.get("status", ""),
                "Assignee": r.get("assignee", "")
            })
        if soon:
            st.dataframe(pd.DataFrame(soon).head(10), use_container_width=True, hide_index=True)
        else:
            st.info("No upcoming deadlines found.")

    st.markdown("---")

    st.markdown("#### Activity Feed")
    if not m["activity"].empty:
        af = m["activity"][["when", "tender", "type", "version", "file", "status"]].rename(columns={
            "when": "Time",
            "tender": "Tender",
            "type": "Doc",
            "version": "v",
            "file": "File",
            "status": "Status"
        })
        st.dataframe(af.head(15), use_container_width=True, hide_index=True)
    else:
        st.caption("No document activity yet. Generate an EOI to see activity here.")

# ======================================
# TENDERS (Overhauled)
# ======================================
with tab_tenders:
    st.markdown("### Manage Tenders")

    # ---------- Filters Bar ----------
    colf1, colf2, colf3, colf4 = st.columns([0.35, 0.2, 0.25, 0.2])
    with colf1:
        search = st.text_input("Search title or buyer", placeholder="e.g., 'airport' or 'FAAN'")
    with colf2:
        all_statuses = ["Draft", "Submitted", "Pending", "Awarded", "Won", "Lost"]
        status_filter = st.multiselect("Status", all_statuses, default=["Draft", "Submitted", "Pending"])
    with colf3:
        sectors = sorted({r.get("sector", "") for r in rows if r.get("sector")}) or ["Facilities Management", "Construction", "Energy", "Other"]
        sector_filter = st.multiselect("Sector", sectors, default=sectors)
    with colf4:
        today = datetime.today().date()
        start_default = today - timedelta(days=14)
        end_default = today + timedelta(days=60)
        start_date = st.date_input("From", start_default)
        end_date = st.date_input("To", end_default)

    # Natural language quick filter
    nl_query = st.text_input("Ask about tenders (e.g., 'Show tenders due this week')", placeholder="Type a natural language query")
    def process_natural_language_query(query, rows):
        if not query:
            return rows
        q = query.lower().strip()
        if "due this week" in q:
            end = today + timedelta(days=7)
            return [r for r in rows if _safe_date(r.get("deadline")) and _safe_date(r["deadline"]) <= end]
        if "overdue" in q:
            return [r for r in rows if _safe_date(r.get("deadline")) and _safe_date(r["deadline"]) < today]
        return rows

    filtered_rows = process_natural_language_query(nl_query, rows)

    # Apply filters
    def _match(r):
        t = (r.get("title","") + " " + r.get("org","")).lower()
        d = _safe_date(r.get("deadline"))
        in_range = (d is None) or (start_date <= d <= end_date)
        return (search.lower() in t) and (r.get("status") in status_filter) and (r.get("sector") in sector_filter) and in_range

    filtered_rows = [r for r in filtered_rows if _match(r)]

    # ---------- Bulk actions ----------
    st.markdown("#### Bulk Actions")
    colb1, colb2, colb3, colb4 = st.columns([0.25, 0.25, 0.25, 0.25])
    with colb1:
        bulk_status = st.selectbox("Set status for selected", all_statuses, index=0)
    with colb2:
        run_bulk_status = st.button("Apply Status to Selected")
    with colb3:
        run_bulk_eoi = st.button("Generate EOI for Selected")
    with colb4:
        export_csv = st.button("Export Filtered as CSV")

    # Selection model
    selected_ids = set()
    # Sub-tabs
    sub_list, sub_kanban, sub_calendar = st.tabs(["List", "Kanban", "Calendar"])

    # Helper to save selection
    def checkbox_id(label, tender_id):
        return st.checkbox(label, key=f"sel_{tender_id}")

    # -------- LIST VIEW --------
    with sub_list:
        if filtered_rows:
            # Stats row
            by_assignee = {}
            for r in filtered_rows:
                a = (r.get("assignee") or "Unassigned").strip() or "Unassigned"
                by_assignee[a] = by_assignee.get(a, 0) + 1
            if by_assignee:
                chips = " ".join([f"<span class='pill'>{a}: {n}</span>" for a, n in by_assignee.items()])
                st.markdown(chips, unsafe_allow_html=True)

            st.write("")  # spacing

            # Table-like expanders with controls
            for r in filtered_rows:
                row_cols = st.columns([0.04, 0.56, 0.2, 0.2])
                with row_cols[0]:
                    if checkbox_id("", r["id"]):
                        selected_ids.add(r["id"])
                with row_cols[1]:
                    st.markdown(f"**{r['title']}**  \n_{r['org']}_")
                with row_cols[2]:
                    st.markdown(f"**Deadline:** {r['deadline']}  \n**Status:** {r['status']}")
                with row_cols[3]:
                    st.markdown(f"**Sector:** {r['sector']}  \n**Assignee:** {r.get('assignee','')}")

                with st.expander("Details / Actions"):
                    st.write(f"**AI Summary:** {ai_summarize(r.get('description',''))}")

                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        if st.button("Generate EOI", key=f"eoi_{r['id']}"):
                            with st.spinner("Generating EOI..."):
                                path = write_docx(r, "EOI", version=len(r.get("drafts", [])) + 1)
                                if path:
                                    r["drafts"] = r.get("drafts", []) + [{"type": "EOI", "file": path, "version": len(r.get("drafts", [])) + 1}]
                                    save_row(r)
                                    st.success(f"Generated draft: {os.path.basename(path)}")
                                    with open(path, "rb") as f:
                                        st.download_button("📥 Download", f, file_name=os.path.basename(path), key=f"dl_{r['id']}_{len(r['drafts'])}")
                    with c2:
                        # Quick status
                        new_status = st.selectbox("Update Status", all_statuses, index=all_statuses.index(r.get("status","Draft")), key=f"ust_{r['id']}")
                        if new_status != r.get("status"):
                            r["status"] = new_status
                            save_row(r)
                            st.info("Status updated.")
                    with c3:
                        # Quick score
                        new_score = st.slider("Fit Score", 0.0, 100.0, float(r.get("score") or 0.0), 1.0, key=f"scr_{r['id']}")
                        if new_score != r.get("score"):
                            r["score"] = float(new_score)
                            save_row(r)
                    with c4:
                        if st.button("Delete", key=f"del_{r['id']}"):
                            delete_row(r["id"])
                            st.success("Tender deleted.")
                            try:
                                st.rerun()
                            except Exception:
                                st.experimental_rerun()
        else:
            st.info("No tenders match the filters.")

    # -------- KANBAN VIEW --------
    with sub_kanban:
        cols = st.columns(5)
        lanes = [
            ("Draft", cols[0]),
            ("Submitted", cols[1]),
            ("Pending", cols[2]),
            ("Won", cols[3]),
            ("Lost", cols[4]),
        ]
        for status, col in lanes:
            with col:
                st.markdown(f"**{status}**")
                lane_items = [r for r in filtered_rows if r.get("status") == status]
                if not lane_items:
                    st.caption("—")
                for r in lane_items:
                    st.markdown(
                        f"<div class='card'><strong>{r['title']}</strong><br>"
                        f"<span class='pill'>{r['sector']}</span> "
                        f"<span class='pill'>Due: {r['deadline']}</span><br>"
                        f"<small>{r.get('org','')}</small></div>",
                        unsafe_allow_html=True
                    )
                    # quick buttons
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("EOI", key=f"kan_eoi_{r['id']}"):
                            path = write_docx(r, "EOI", version=len(r.get("drafts", [])) + 1)
                            if path:
                                r["drafts"] = r.get("drafts", []) + [{"type": "EOI", "file": path, "version": len(r.get("drafts", [])) + 1}]
                                save_row(r)
                                st.success("EOI generated.")
                    with c2:
                        nxt_opts = [s for s in ["Draft","Submitted","Pending","Won","Lost"] if s != status]
                        nxt = st.selectbox("Move to", nxt_opts, key=f"kan_mv_{r['id']}")
                        if st.button("Move", key=f"kan_btn_{r['id']}"):
                            r["status"] = nxt
                            save_row(r)
                            st.info(f"Moved to {nxt}")
                            try:
                                st.rerun()
                            except Exception:
                                st.experimental_rerun()

    # -------- CALENDAR VIEW --------
    with sub_calendar:
        if filtered_rows:
            dfc = pd.DataFrame(filtered_rows)
            dfc["deadline_dt"] = pd.to_datetime(dfc["deadline"], errors="coerce")
            cal = alt.Chart(dfc.dropna(subset=["deadline_dt"])).mark_circle(size=110).encode(
                x=alt.X("deadline_dt:T", title="Deadline"),
                y=alt.Y("sector:N", title="Sector"),
                color=alt.Color("status:N", scale=alt.Scale(scheme="category10")),
                tooltip=["title", "org", "deadline", "status", "assignee"]
            ).properties(height=320)
            st.altair_chart(cal, use_container_width=True)
        else:
            st.info("Nothing to plot.")

    # ---------- Execute Bulk Actions ----------
    if run_bulk_status or run_bulk_eoi or export_csv:
        # Determine selection from the checkboxes in List view (stored in session)
        selected_ids = {int(k.split("_")[-1]) for k, v in st.session_state.items() if k.startswith("sel_") and v}
        if not selected_ids and (run_bulk_status or run_bulk_eoi):
            st.warning("Select at least one tender in List view first.")
        else:
            if run_bulk_status:
                for r in rows:
                    if r["id"] in selected_ids:
                        r["status"] = bulk_status
                        save_row(r)
                st.success(f"Updated status to '{bulk_status}' for {len(selected_ids)} tender(s).")
            if run_bulk_eoi:
                cnt = 0
                for r in rows:
                    if r["id"] in selected_ids:
                        path = write_docx(r, "EOI", version=len(r.get("drafts", [])) + 1)
                        if path:
                            r["drafts"] = r.get("drafts", []) + [{"type": "EOI", "file": path, "version": len(r.get("drafts", [])) + 1}]
                            save_row(r)
                            cnt += 1
                st.success(f"Generated EOIs for {cnt} tender(s).")
            if export_csv:
                dfexp = pd.DataFrame(filtered_rows)
                st.download_button("Download CSV", dfexp.to_csv(index=False).encode("utf-8"), file_name="tenders_filtered.csv", mime="text/csv")

    st.markdown("---")

    # ---------- Add New Tender ----------
    st.markdown("### Add Tender")
    with st.form("add_tender_form"):
        c1, c2 = st.columns(2)
        with c1:
            title = st.text_input("Tender Title")
            org = st.text_input("Organization")
            sector = st.selectbox("Sector", ["Facilities Management", "Construction", "Energy", "Other"])
        with c2:
            deadline_dt = st.date_input("Deadline", value=datetime.today().date() + timedelta(days=14))
            status = st.selectbox("Status", all_statuses, index=0)
            assignee = st.text_input("Assignee Email", value="bids@tfml.ng")
        description = st.text_area("Description")
        submit_new = st.form_submit_button("Add Tender")
        if submit_new:
            new_id = max([r.get("id", 0) for r in rows], default=0) + 1
            tender = {
                "id": new_id, "title": title, "org": org, "sector": sector,
                "deadline": deadline_dt.strftime("%Y-%m-%d"), "description": description,
                "status": status, "score": 0.0, "assignee": assignee, "drafts": []
            }
            rows.append(tender)
            save_row(tender)
            st.success("Tender added!")

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
                "Version": d.get("version"),
                "Status": r.get("status", "Draft"),
                "Deadline": r.get("deadline")
            })
    if not lib:
        st.info("No drafts yet.")
    else:
        df_lib = pd.DataFrame(lib)
        st.dataframe(df_lib, use_container_width=True, hide_index=True)
        for draft in lib:
            if st.button(f"Email {draft['File']}", key=f"email_{draft['File']}"):
                send_email(st.session_state.get("bid_email", "bids@tfml.ng"),
                           f"EOI: {draft['Tender']}",
                           "Please review the attached EOI.",
                           draft['File'])
                st.success(f"Email sent for {draft['File']}")

# ======================================
# SETTINGS
# ======================================
with tab_settings:
    st.markdown("### Settings")
    st.session_state["default_recipient"] = st.text_input("Default Recipient", value=st.session_state.get("default_recipient", "Procurement Team"))
    st.session_state["bid_email"] = st.text_input("Bid Office Email", value=st.session_state.get("bid_email", "bids@tfml.ng"))
    st.session_state["bid_phone"] = st.text_input("Bid Office Phone", value=st.session_state.get("bid_phone", "+234-XXX-XXXX"))
    theme = st.selectbox("Theme", ["Light", "Dark"])
    if theme == "Dark":
        st.markdown("<script>document.body.classList.add('dark-mode');</script>", unsafe_allow_html=True)
    else:
        st.markdown("<script>document.body.classList.remove('dark-mode');</script>", unsafe_allow_html=True)
    st.caption("Changes save automatically when generating drafts.")
