import streamlit as st
import requests
from typing import List, Dict
import pandas as pd
import random
import json
from pathlib import Path

# Demo data directory
DATA_DIR = Path(__file__).parent / "demo_data"

def load_demo_file(name: str, default=None):
	try:
		p = DATA_DIR / name
		if p.exists():
			with open(p, "r", encoding="utf-8") as f:
				return json.load(f)
	except Exception:
		pass
	return default


st.set_page_config(page_title="BuildPulse Demo", layout="wide")
st.title("BuildPulse AI — Demo Dashboard")

st.markdown("Demo UI: Ingest documents, run RAG, SME lookup, and security scans. Use `Demo data` toggle to visualize without a backend.")

# Sidebar controls
demo_mode = st.sidebar.checkbox("Use Demo Data", value=True)
page = st.sidebar.selectbox("Page", ["Home", "Ingest", "SME Lookup", "RAG Query", "AI Chat", "Security Scan", "Agents Dashboard"])

# Sample demo data (used when demo_mode=True)
SAMPLE_SMES = load_demo_file("smes.json", [])
SAMPLE_RAG = load_demo_file("rag.json", {"answer": "", "sources": []})
SAMPLE_SECURITY = load_demo_file("security.json", {"issues": [], "summary": {"total_issues": 0}})
SAMPLE_AGENTS_STATUS = load_demo_file("agents.json", [])
SAMPLE_DOCUMENTS = load_demo_file("documents.json", [])


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


if page == "Home":
	st.header("Home — BuildPulse Dashboard")
	st.write("Use the sidebar to navigate pages. Toggle `Use Demo Data` to see sample results without a running backend.")
	col1, col2 = st.columns(2)
	with col1:
		st.subheader("Agents Overview")
		df_agents = pd.DataFrame(SAMPLE_AGENTS_STATUS)
		st.table(df_agents)
	with col2:
		st.subheader("Ingestion Metrics")
		ingested = random.randint(5, 120) if demo_mode else 0
		st.metric("Documents ingested (last run)", ingested)

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

elif page == "AI Chat":
	st.header("AI Chat (RAG + LLM)")
	q3 = st.text_input("Ask a question", value="What does BuildPulse do?")
	use_db2 = st.checkbox("Use ingested DB docs for context", value=True, key="ai_use_db")
	if st.button("Ask AI"):
		if demo_mode:
			out = SAMPLE_RAG
			st.subheader("Answer")
			st.write(out.get("answer"))
			st.subheader("Sources")
			for s in out.get("sources", []):
				st.write(s.get("id"))
				st.write(s.get("content"))
				st.markdown("---")
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

elif page == "Agents Dashboard":
	st.header("Agents Dashboard")
	st.write("Overview and demo visualizations for each backend agent.")
	df_agents = pd.DataFrame(SAMPLE_AGENTS_STATUS)
	st.table(df_agents)
	st.subheader("Agent Status Breakdown")
	status_counts = df_agents['status'].value_counts()
	st.bar_chart(status_counts)

st.caption("Backend should run at http://localhost:8000 for full functionality; toggle `Use Demo Data` to avoid backend calls.")

