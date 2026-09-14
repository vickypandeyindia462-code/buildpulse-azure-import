import streamlit as st
import requests
from typing import List, Dict
import pandas as pd
import random
import json
from pathlib import Path

# Demo data directory
DATA_DIR = Path(__file__).parent / "demo_data"

# load custom styles
CSS_PATH = Path(__file__).parent / "static" / "styles.css"
def load_css():
	try:
		with open(CSS_PATH, "r", encoding="utf-8") as f:
			st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
	except Exception:
		pass

load_css()

def load_demo_file(name: str, default=None):
	try:
		p = DATA_DIR / name
		if p.exists():
			with open(p, "r", encoding="utf-8") as f:
				return json.load(f)
	except Exception:
		pass
	return default


st.set_page_config(page_title="BuildPulse", layout="wide")
st.title("BuildPulse AI")

# Demo mode: use embedded demo data for this dev build
demo_mode = True
pages = [
	"Executive Dashboard",
	"AI Copilot Chat",
	"Risk Radar",
	"Knowledge Discovery",
	"Contribute Knowledge",
	"Incident Intelligence",
	"SME Directory",
	"Security & Trust Center",
	"Ingest",
	"SME Lookup",
	"RAG Query",
	"Security Scan",
	"Agents Dashboard",
]

# Navigation: left navy sidebar + topbar shell
if 'page' not in st.session_state:
	st.session_state['page'] = 'Executive Dashboard'

left_col, right_col = st.columns([0.18, 0.82])

with left_col:
	st.markdown('<div class="bp-sidebar">', unsafe_allow_html=True)
	st.markdown('<div class="brand">✦ BuildPulse<br><span style="font-size:12px;font-weight:400">AI OPS COMMAND CENTER</span></div>', unsafe_allow_html=True)
	nav = st.radio('', options=pages, index=pages.index(st.session_state['page']))
	# render nav items as list (we will style via CSS)
	st.markdown('</div>', unsafe_allow_html=True)
	if nav != st.session_state['page']:
		st.session_state['page'] = nav

page = st.session_state['page']

# Sample demo data (used when demo_mode=True)
SAMPLE_SMES = load_demo_file("smes.json", [])
SAMPLE_RAG = load_demo_file("rag.json", {"answer": "", "sources": []})
SAMPLE_SECURITY = load_demo_file("security.json", {"issues": [], "summary": {"total_issues": 0}})
SAMPLE_AGENTS_STATUS = load_demo_file("agents.json", [])
SAMPLE_DOCUMENTS = load_demo_file("documents.json", [])


# Simple UI styling and small reusable components
def evidence_card(title: str, summary: str, meta: dict = None):
	"""Render a compact evidence card (uses expander for tidy display)."""
	with st.expander(title):
		st.write(summary)
		if meta:
			md = " | ".join(f"**{k}:** {v}" for k, v in meta.items())
			st.markdown(md)


def call_backend_post(path: str, json_data: dict, timeout: int = 15):
	try:
		r = requests.post(f"http://localhost:8000{path}", json=json_data, timeout=timeout)
		r.raise_for_status()
		return r.json()
	except Exception as e:
		st.error(f"Backend call failed: {e}")
		return None


def call_backend_get(path: str, params: dict = None, timeout: int = 10):
	try:
		r = requests.get(f"http://localhost:8000{path}", params=params, timeout=timeout)
		r.raise_for_status()
		return r.json()
	except Exception as e:
		st.error(f"Backend call failed: {e}")
		return None


if page == "Executive Dashboard":
	st.header("Executive Dashboard")
	st.write("Good morning — operational pulse and release readiness.")
	# Top metrics
	cols = st.columns(4)
	metrics = {
		"Release readiness": "82%",
		"Open incidents": 7,
		"Knowledge health": "94%",
		"SME coverage": "88%",
	}
	demo_trend = [random.randint(60, 90) for _ in range(7)]
	for c, (k, v) in zip(cols, metrics.items()):
		c.metric(k, v, delta="+6%" if k == "Release readiness" else None)

	st.markdown("---")
	left, right = st.columns([2, 1])
	with left:
		st.subheader("Release 24.3 — Readiness")
		st.info("At risk — 2 blockers")
		st.line_chart(demo_trend)
		st.subheader("Attention feed")
		feed = load_demo_file("attention_feed.json", [
			{"title": "Loan Service P1 outage", "time": "10:17"},
			{"title": "Release-risk increase", "time": "09:50"},
			{"title": "API Gateway runbook review", "time": "08:10"},
		])
		for f in feed:
			st.write(f"- {f['title']} — {f['time']}")
	with right:
		st.subheader("Critical system owners")
		owners = load_demo_file("critical_owners.json", [])
		if not owners:
			st.write("Meera Kulkarni — Loan Service (Covered)")
			st.write("Dev Shah — Payments API (No backup)")
		else:
			st.table(pd.DataFrame(owners))

	st.markdown("---")
	st.button("✦ Ask BuildPulse AI")

elif page == "Contribute Knowledge":
	st.header("Contribute knowledge")
	st.write("Share documents to improve team knowledge. Files are scanned for PII and secrets before indexing.")
	with st.form(key="upload_form"):
		uploaded = st.file_uploader("Upload files (PDF, DOCX, MD, TXT, CSV)", accept_multiple_files=True)
		title = st.text_input("Document title")
		doc_type = st.selectbox("Document type", ["Runbook", "Postmortem", "Architecture", "Other"])
		team = st.text_input("Owning team")
		system = st.text_input("Relevant system")
		desc = st.text_area("Short description")
		access = st.radio("Access", ["Organization", "My team only"], index=0)
		reviewers_txt = st.text_input("Request reviewers (comma-separated GitHub usernames)")
		submitted = st.form_submit_button("Submit for indexing →")
	if submitted:
		if not uploaded:
			st.error("Please select at least one file to upload.")
		else:
			docs = []
			for f in uploaded:
				content = f.read().decode("utf-8", errors="ignore")
				docs.append({"title": title or f.name, "content": content, "type": doc_type, "team": team, "system": system, "access": access})
			if demo_mode:
				st.success("Document submitted for indexing. We’ll notify you if validation needs your attention.")
			else:
				reviewers = [r.strip() for r in reviewers_txt.split(",") if r.strip()]
				payload = {"docs": docs}
				if reviewers:
					payload["reviewers"] = reviewers
				res = call_backend_post("/submit/pr", payload, timeout=30)
				if res and res.get("pr_url"):
					st.success(f"PR created: {res.get('pr_url')}")
				else:
					st.error("Failed to create PR")

	st.markdown("\nRecent submissions:\n")
	recent = load_demo_file("recent_submissions.json", [])
	st.table(pd.DataFrame(recent))

elif page == "Ingest":
	st.header("Ingest Documents")
	txt = st.text_area("Paste documents (one per line)")
	if st.button("Ingest"):
		lines = [l.strip() for l in txt.splitlines() if l.strip()]
		docs = [{"content": l} for l in lines]
		if demo_mode:
			st.success(f"(Demo) Ingested {len(docs)} documents")
			st.write(pd.DataFrame(docs).head())
		else:
			out = call_backend_post("/ingest/", docs)
			if out:
				st.success(f"Ingested {out.get('processed_count')} documents")

	# Submit as contribution -> create PR
	if st.button("Submit as Contribution (create PR)"):
		lines = [l.strip() for l in txt.splitlines() if l.strip()]
		docs = [{"content": l} for l in lines]
		if demo_mode:
			st.info("Demo mode: would create a PR with the submission.")
		else:
			res = call_backend_post("/submit/pr", docs, timeout=30)
			if res and res.get("pr_url"):
				st.success(f"PR created: {res.get('pr_url')}")
			else:
				st.error("Failed to create PR")

elif page == "SME Lookup":
	st.header("SME Lookup")
	q = st.text_input("System name or tag", value="Loan")
	if st.button("Lookup SME"):
		if demo_mode:
			results = [s for s in SAMPLE_SMES if q.lower() in s["system_name"].lower() or any(q.lower() in t.lower() for t in s["expertise_tags"]) ]
		else:
			resp = call_backend_get("/orchestrator/sme", params={"query": q})
			results = resp.get("results", []) if resp else []

		if not results:
			st.info("No SMEs found")
		else:
			for r in results:
				st.subheader(r.get("system_name"))
				st.write(f"**Owner:** {r.get('owner_name')} — {r.get('owner_team')}")
				st.write(f"**Email:** {r.get('owner_email')}")
				tags = r.get('expertise_tags') or []
				if tags:
					st.write("**Tags:** " + ", ".join(tags))
				st.markdown("---")

elif page == "RAG Query":
	st.header("RAG Query")
	q2 = st.text_input("Query for RAG", value="Loan")
	use_db = st.checkbox("Query ingested DB documents", value=True)
	if st.button("Run RAG"):
		if demo_mode:
			st.write(SAMPLE_RAG)
		else:
			payload = {"query": q2, "use_db": use_db}
			out = call_backend_post("/rag/query", payload)
			if out:
				st.write(out)

elif page == "AI Copilot Chat":
	st.header("BuildPulse AI Copilot")
	st.write("Protected by PII & secret scanning · Answers are logged for audit")
	suggested = ["Why did the loan service fail?", "Can release 24.3 go live tomorrow?", "Who owns the Payments API?"]
	cols = st.columns(len(suggested))
	for c, s in zip(cols, suggested):
		if c.button(s):
			st.session_state['query'] = s
	q3 = st.text_input("Ask a question", value=st.session_state.get('query', ""))
	use_db2 = st.checkbox("Use ingested DB docs for context", value=True, key="ai_use_db")
	if st.button("Ask BuildPulse"):
		if demo_mode:
			out = SAMPLE_RAG
			st.subheader("Answer — Release 24.3: High Risk (72 / 100)")
			st.write("Release 24.3 is High Risk. The active Loan Service P1 is the largest factor. Payments API lacks backup owner.")
			st.subheader("Evidence")
			for s in out.get("sources", []):
				evidence_card(f"Source: {s.get('id')}", s.get('content'), meta={"source_id": s.get('id')})
		else:
			payload = {"query": q3, "use_db": use_db2}
			r = call_backend_post("/ai/chat", payload, timeout=20)
			if r:
				st.subheader("Answer")
				st.write(r.get("answer"))
				st.subheader("Sources")
				for s in r.get("sources", []):
					st.write(s.get("id"))
					st.write(s.get("content"))
					st.markdown("---")

elif page == "Risk Radar":
	st.header("Risk Radar — Release 24.3 · 15 Sep")
	st.metric("Risk score", "72 / 100")
	st.success("High risk — Recommend resolving Loan Service outage before go-live")
	drivers = [
		("Open P1 incident", 35, "Loan Service outage affects release dependency"),
		("Coverage gap", 22, "Payments API has no confirmed backup owner"),
		("Recent change volume", 15, "14 production changes in 7 days"),
	]
	for d in drivers:
		st.write(f"**{d[0]}** — +{d[1]} points — {d[2]}")
	st.button("Create mitigation plan")

elif page == "Knowledge Discovery":
	st.header("Knowledge Discovery")
	q = st.text_input("Search", value="loan service timeout mitigation")
	st.button("Search")
	left, right = st.columns([1, 3])
	with left:
		st.subheader("Filters")
		st.multiselect("Document types", ["Runbook", "Postmortem", "Architecture"], default=["Runbook"])
		st.multiselect("Service", ["All services", "Loan Service", "Payments API"], default=["All services"])
	with right:
		results = SAMPLE_DOCUMENTS if demo_mode else []
		st.subheader(f"Results ({len(results)})")
		for r in results:
			title = f"{r.get('title','Untitled')} — {r.get('type','doc')} — {r.get('score', '—')}%"
			evidence_card(title, r.get('summary',''), meta={"type": r.get('type'), "score": r.get('score')})

elif page == "Security Scan":
	st.header("Security / PII Scan")
	text = st.text_area("Text to scan for PII")
	if st.button("Scan"):
		if demo_mode:
			st.json(SAMPLE_SECURITY)
		else:
			r = call_backend_post("/security/scan", {"text": text})
			if r:
				st.json(r)

elif page == "Incident Intelligence":
	st.header("Incident Intelligence")
	incidents = load_demo_file("incidents.json", [])
	left, right = st.columns([1, 2])
	with left:
		st.subheader("Active incidents")
		if incidents:
			for inc in incidents:
				st.button(f"{inc.get('id')} — {inc.get('title')}")
		else:
			st.write("INC-2091 — Loan Service unavailable (P1)")
	with right:
		st.subheader("INC-2091 — Loan Service unavailable")
		st.write("P1 — Active — Lending Platform")
		timeline = [
			("09:34", "Alert triggered"),
			("10:04", "Mitigation started"),
			("10:17", "Root cause identified"),
		]
		for t, e in timeline:
			st.write(f"{t} — {e}")

elif page == "SME Directory":
	st.header("SME Directory")
	df = pd.DataFrame(SAMPLE_SMES)
	if not df.empty:
		df_display = df[['system_name','owner_name','backup_owner','status']] if 'backup_owner' in df.columns else df
		st.table(df_display)
	else:
		st.write("Loan Service — Meera Kulkarni — Arjun Rao — Covered")

elif page == "Security & Trust Center":
	st.header("Security & Trust Center")
	sec = SAMPLE_SECURITY
	st.metric("Queries scanned today", sec.get('summary', {}).get('scanned_today', 1284))
	st.metric("Sensitive items redacted (30d)", sec.get('summary', {}).get('redacted_30d', 23))
	st.subheader("Active controls")
	st.write("PII detection, secret scanning, immutable audit logging")

elif page == "Agents Dashboard":
	st.header("Agents Dashboard")
	st.write("Overview and demo visualizations for each backend agent.")
	df_agents = pd.DataFrame(SAMPLE_AGENTS_STATUS)
	st.table(df_agents)
	st.subheader("Agent Status Breakdown")
	status_counts = df_agents['status'].value_counts()
	st.bar_chart(status_counts)

st.caption("Backend should run at http://localhost:8000 for full functionality.")

