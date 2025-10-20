import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import streamlit as st
import pandas as pd
import altair as alt
from docx import Document
from PIL import Image
import requests  # For external API (placeholder)

# ======================================
# PATHS AND CONFIG
# ======================================
BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS = BASE_DIR / "assets"
LOGS = BASE_DIR / "logs"
EOIS = BASE_DIR / "eois"
TENDERS_DB = LOGS / "tenders.db"
LOGO_PATH = ASSETS / "tfml_logo.png"

EOIS.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)

# Theme
ACCENT = "#E60F18"
CARD = "#F5F5F5"
TEXT = "#000000"
MUTED = "#555555"

st.set_page_config(
    page_title="TFML Agentic AI — Luxe Console",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# CSS
st.markdown(f"""
<style>
.stApp {{ background: #FFFFFF; }}
.block-container {{ padding-top: 1rem; }}
.header {{ display:flex; align-items:center; gap:14px; padding: 6px 0 14px 0; border-bottom:1px solid #ddd; }}
.header .title {{ font-weight:900; font-size:26px; color:{TEXT}; letter-spacing:.2px; }}
.kpi {{ background: linear-gradient(180deg, #FFFFFF 0%, {CARD} 100%); border: 1px solid #ddd; border-radius: 14px; padding: 16px; color: {TEXT}; cursor: pointer; }}
.kpi .label {{ color:{MUTED}; font-size:.78rem; text-transform:uppercase; letter-spacing:1px; }}
.kpi .value {{ font-size:1.8rem; font-weight:800; }}
.card {{ background: {CARD}; border:1px solid #ddd; border-radius: 14px; padding: 16px; }}
.pill {{ display:inline-block; padding: 2px 10px; border-radius: 999px; font-size: .75rem; font-weight: 700; background: #eee; color: #333; border: 1px solid #ccc; }}
.pill.red {{ background: rgba(230,15,24,.12); color: {ACCENT}; border-color: {ACCENT}; }}
.btn {{ background:{ACCENT}; color:#fff; padding:9px 14px; border-radius:10px; border:none; font-weight:700; }}
.btn.ghost {{ background:transparent; border:1px solid #ccc; color:{TEXT}; }}
@media (max-width: 600px) {{ 
    .kpi {{ padding: 10px; }} 
    .kpi .value {{ font-size: 1.4rem; }} 
    .header .title {{ font-size: 20px; }} 
}}
</style>
""", unsafe_allow_html=True)

# ======================================
# DATABASE LAYER
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
                "score": r[7], "assignee": r[8], "drafts": json.loads(r[9]) if r[9] else []
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

# Initialize database
init_db()

# ======================================
# DOCUMENT GENERATION
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
            recipient=tender.get("recipient", "Procurement Team"),
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
# AI FEATURES (PLACEHOLDER)
# ======================================
def ai_summarize(description):
    # Placeholder for xAI API call (see https://x.ai/api for details)
    return f"Summary: {description[:100]}..."  # Replace with real AI summary

def process_natural_language_query(query, rows):
    if "due this week" in query.lower():
        return [r for r in rows if r.get("deadline") and
                datetime.strptime(r["deadline"], "%Y-%m-%d").date() <= (datetime.today().date() + timedelta(days=7))]
    return rows

# ======================================
# EMAIL INTEGRATION (PLACEHOLDER)
# ======================================
def send_email(recipient, subject, body, attachment_path):
    # Placeholder for email logic (configure SMTP settings)
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
        st.caption("It’s all about you… • one-click drafting • faster BD • higher win rate")

# Load Data
rows = load_rows()

# Notifications for Upcoming Deadlines
for r in rows:
    if r.get("deadline"):
        try:
            deadline = datetime.strptime(r["deadline"], "%Y-%m-%d").date()
            if deadline <= (datetime.today().date() + timedelta(days=3)):
                st.warning(f"Tender '{r['title']}' is due on {r['deadline']}!", key=f"warn_{r['id']}")
        except ValueError:
            st.error(f"Invalid deadline format for tender '{r['title']}'")

# Tabs
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
           datetime.strptime(r["deadline"], "%Y-%m-%d").date() <= (datetime.today().date() + timedelta(days=7))
    )
    drafts = sum(1 for r in rows if r.get("status") == "Draft")
    submitted = sum(1 for r in rows if r.get("status") in ("Submitted", "Pending"))

    # Interactive KPIs
    c1, c2, c3, c4 = st.columns(4)
    for c, label, val, sub, key, filter_key in (
        (c1, "Open tenders", total, "All active notices", "total_kpi", "all"),
        (c2, "Due in 7 days", due7, "Deadline pressure", "due7_kpi", "due7"),
        (c3, "Drafts ready", drafts, "Awaiting review", "drafts_kpi", "drafts"),
        (c4, "In flight", submitted, "Submitted or pending", "submitted_kpi", "submitted"),
    ):
        with c:
            if st.button(f"{val}\n{label}", key=key, help=f"Click to filter {label.lower()}"):
                if filter_key == "due7":
                    st.session_state["filtered_tenders"] = [
                        r for r in rows if r.get("deadline") and
                        datetime.strptime(r["deadline"], "%Y-%m-%d").date() <= (datetime.today().date() + timedelta(days=7))
                    ]
                elif filter_key == "drafts":
                    st.session_state["filtered_tenders"] = [r for r in rows if r.get("status") == "Draft"]
                elif filter_key == "submitted":
                    st.session_state["filtered_tenders"] = [r for r in rows if r.get("status") in ("Submitted", "Pending")]
                else:
                    st.session_state["filtered_tenders"] = rows
            st.markdown(f"<div class='kpi'><div class='label'>{label}</div><div class='value'>{val}</div><div class='sub'>{sub}</div></div>", unsafe_allow_html=True)

    if rows:
        df = pd.DataFrame(rows)
        # Sector Bar Chart
        st.markdown("##### Tenders by Sector")
        chart = alt.Chart(df).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
            x=alt.X('sector:N', sort='-y', axis=alt.Axis(labelColor='black', title='')),
            y=alt.Y('count():Q', axis=alt.Axis(labelColor='black', title='Tenders')),
            color=alt.Color('sector:N', scale=alt.Scale(scheme='category10'))
        ).properties(height=260, background='transparent')
        st.altair_chart(chart, use_container_width=True)

        # Status Pie Chart
        st.markdown("##### Tender Status Distribution")
        pie_chart = alt.Chart(df).mark_arc().encode(
            theta=alt.Theta("count():Q", stack=True),
            color=alt.Color("status:N", scale=alt.Scale(scheme='category10')),
            tooltip=["status", "count()"]
        ).properties(height=260)
        st.altair_chart(pie_chart, use_container_width=True)

        # Deadline Timeline
        st.markdown("##### Tender Deadlines")
        df["deadline"] = pd.to_datetime(df["deadline"], errors='coerce')
        timeline = alt.Chart(df).mark_circle(size=100).encode(
            x=alt.X("deadline:T", title="Deadline"),
            y=alt.Y("title:N", title="Tender"),
            color=alt.Color("status:N", scale=alt.Scale(scheme="category10")),
            tooltip=["title", "deadline", "status"]
        ).properties(height=300)
        st.altair_chart(timeline, use_container_width=True)

        # Trend Analysis (Placeholder)
        st.markdown("##### Tender Trends")
        trend_data = pd.DataFrame({
            "Month": ["2025-01", "2025-02", "2025-03"],
            "Tenders": [10, 15, 12],
            "Wins": [3, 5, 4]
        })
        trend_chart = alt.Chart(trend_data).mark_line().encode(
            x="Month", y="Tenders", color=alt.value(ACCENT)
        ).properties(height=200)
        st.altair_chart(trend_chart, use_container_width=True)
    else:
        st.info("No tenders yet.")

# ======================================
# TENDERS
# ======================================
with tab_tenders:
    st.markdown("### Manage Tenders")
    # Natural Language Query
    query = st.text_input("Ask about tenders (e.g., 'Show tenders due this week')", help="Enter a query to filter tenders")
    filtered_rows = process_natural_language_query(query, rows) if query else rows

    # Search and Filter
    search = st.text_input("Search Tenders", help="Search by tender title")
    status_filter = st.multiselect("Filter by Status", ["Draft", "Submitted", "Pending"], default=["Draft", "Submitted", "Pending"])
    sector_filter = st.multiselect("Filter by Sector", list(set(r.get("sector", "") for r in rows)), default=list(set(r.get("sector", "") for r in rows)))
    filtered_rows = [
        r for r in filtered_rows
        if search.lower() in r.get("title", "").lower() and
           r.get("status") in status_filter and
           r.get("sector") in sector_filter
    ]

    # Add Tender Form
    with st.form("add_tender_form"):
        title = st.text_input("Tender Title")
        org = st.text_input("Organization")
        sector = st.selectbox("Sector", ["Facilities Management", "Construction", "Energy", "Other"])
        deadline = st.date_input("Deadline")
        description = st.text_area("Description")
        status = st.selectbox("Status", ["Draft", "Submitted", "Pending"])
        assignee = st.text_input("Assignee Email")
        if st.form_submit_button("Add Tender", help="Add a new tender"):
            new_id = max([r.get("id", 0) for r in rows], default=0) + 1
            tender = {
                "id": new_id, "title": title, "org": org, "sector": sector,
                "deadline": deadline.strftime("%Y-%m-%d"), "description": description,
                "status": status, "score": 0.0, "assignee": assignee, "drafts": []
            }
            rows.append(tender)
            save_row(tender)
            st.success("Tender added!")

    # Tenders Table
    if filtered_rows:
        df_view = pd.DataFrame(filtered_rows)
        required_cols = ["id", "title", "org", "sector", "deadline", "status", "score", "assignee"]
        for c in required_cols:
            if c not in df_view.columns:
                df_view[c] = ""
        st.dataframe(
            df_view[required_cols],
            use_container_width=True,
            hide_index=True,
            column_config={"score": st.column_config.NumberColumn(format="%.2f")}
        )

        # Detailed View with Expander
        for r in filtered_rows:
            with st.expander(f"{r['title']} (ID: {r['id']})"):
                st.write(f"**Organization**: {r['org']}")
                st.write(f"**Sector**: {r['sector']}")
                st.write(f"**Deadline**: {r['deadline']}")
                st.write(f"**Status**: {r['status']}")
                st.write(f"**Assignee**: {r['assignee']}")
                st.write(f"**AI Summary**: {ai_summarize(r['description'])}")
                if st.button("Generate EOI", key=f"eoi_{r['id']}", help="Generate EOI for this tender"):
                    with st.spinner("Generating EOI..."):
                        path = write_docx(r, "EOI", version=len(r.get("drafts", [])) + 1)
                        if path:
                            r["drafts"] = r.get("drafts", []) + [{"type": "EOI", "file": path, "version": len(r.get("drafts", [])) + 1}]
                            save_row(r)
                            st.success(f"Generated draft: {os.path.basename(path)}")
                            with open(path, "rb") as f:
                                st.download_button("📥 Download", f, file_name=os.path.basename(path), key=f"dl_{r['id']}")
                if st.button("Delete Tender", key=f"del_{r['id']}", help="Delete this tender"):
                    delete_row(r["id"])
                    st.success(f"Tender {r['title']} deleted!")
                    st.experimental_rerun()
    else:
        st.info("No tenders match the filters.")

    # Fetch Tenders from API (Placeholder)
    if st.button("Fetch Tenders from API", help="Fetch tenders from external procurement API"):
        try:
            response = requests.get("https://api.publictenders.com")  # Replace with real API
            if response.status_code == 200:
                new_tenders = response.json()  # Process API response
                for t in new_tenders:
                    tender = {
                        "id": max([r.get("id", 0) for r in rows], default=0) + 1,
                        "title": t.get("title", "Untitled"),
                        "org": t.get("org", "Unknown"),
                        "sector": t.get("sector", "Other"),
                        "deadline": t.get("deadline", datetime.today().strftime("%Y-%m-%d")),
                        "description": t.get("description", ""),
                        "status": "Draft",
                        "score": 0.0,
                        "assignee": "",
                        "drafts": []
                    }
                    rows.append(tender)
                    save_row(tender)
                st.success("Tenders fetched from API!")
        except Exception as e:
            st.error(f"Error fetching tenders: {e}")

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
            if st.button(f"Email {draft['File']}", key=f"email_{draft['File']}", help="Send draft via email"):
                send_email("bids@tfml.ng", f"EOI: {draft['Tender']}", "Please review the attached EOI.", draft["File"])
                st.success(f"Email sent for {draft['File']}")

# ======================================
# SETTINGS
# ======================================
with tab_settings:
    st.markdown("### Settings")
    recipient = st.text_input("Default Recipient", value="Procurement Team", help="Default recipient for EOI drafts")
    email = st.text_input("Bid Office Email", value="bids@tfml.ng", help="Email for bid office communications")
    phone = st.text_input("Bid Office Phone", value="+234-XXX-XXXX", help="Phone number for bid office")
    theme = st.selectbox("Theme", ["Light", "Dark"], help="Switch between light and dark themes")
    if theme == "Dark":
        st.markdown("""
        <style>
        .stApp { background: #1E1E1E; color: #FFFFFF; }
        .kpi { background: #2A2A2A; border-color: #444; }
        .card { background: #2A2A2A; border-color: #444; }
        </style>
        """, unsafe_allow_html=True)
    st.caption("Changes save automatically when generating drafts.")

# Initial Header
logo_header()
