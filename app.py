from __future__ import annotations
import os, re
from pathlib import Path
import streamlit as st
from config import MODEL, PROFILE_DIR
from scraper import extract, setup_browser
from analyzer import analyze
from pdf_builder import build_pdf

st.set_page_config(page_title="Trailhead Study Assistant", page_icon="📘", layout="wide")
def slug(value: str) -> str: return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")[:80] or "trailhead_module"
st.title("📘 Salesforce Trailhead Study Assistant")
st.caption("Read-only assistant: extract Trailhead content, explain it with Gemini, and create a PDF study guide.")
with st.sidebar:
    st.header("Browser setup")
    st.write(f"Persistent profile: `{PROFILE_DIR}`")
    st.info("Use once to log in to Trailhead. Brave opens in a separate window.")
    if st.button("Open Brave Login", width="stretch"):
        try:
            with st.spinner("Log in to Trailhead, then close Brave..."): setup_browser()
            st.success("Browser profile saved.")
        except Exception as exc: st.error(str(exc))
    st.divider(); st.header("Settings")
    st.subheader("Gemini API key")
    st.caption("Stored only in this browser session; it is not written to disk.")
    api_key = st.text_input("Gemini API key", type="password", value=st.session_state.get("gemini_api_key", ""), key="gemini_api_key_input")
    if api_key:
        st.session_state["gemini_api_key"] = api_key
    elif "gemini_api_key" not in st.session_state:
        st.session_state["gemini_api_key"] = os.getenv("GEMINI_API_KEY", "")
    model = st.text_input("Gemini model", value=MODEL)
    st.write("Gemini API key: " + ("✅ configured" if st.session_state.get("gemini_api_key") else "⚠️ missing"))
url = st.text_input("Trailhead module URL", placeholder="https://trailhead.salesforce.com/content/learn/modules/...")
out_dir = st.text_input("Export folder", value="exports")
if st.button("Generate Study Guide", type="primary", use_container_width=True):
    if not url.strip(): st.warning("Enter a Trailhead module URL first.")
    elif not st.session_state.get("gemini_api_key"): st.error("Enter your Gemini API key in the sidebar first.")
    else:
        try:
            progress = st.progress(0, text="Opening Brave and extracting module content...")
            data = extract(url.strip()); progress.progress(45, text="Module extracted. Sending content to Gemini...")
            old_model = os.getenv("GEMINI_MODEL"); old_key = os.getenv("GEMINI_API_KEY")
            os.environ["GEMINI_MODEL"] = model.strip() or MODEL; os.environ["GEMINI_API_KEY"] = st.session_state["gemini_api_key"]
            report = analyze(data)
            if old_model is None: os.environ.pop("GEMINI_MODEL", None)
            else: os.environ["GEMINI_MODEL"] = old_model
            if old_key is None: os.environ.pop("GEMINI_API_KEY", None)
            else: os.environ["GEMINI_API_KEY"] = old_key
            progress.progress(75, text="Gemini report validated. Rendering PDF...")
            pdf_path = build_pdf(data, report, Path(out_dir) / f"{slug(report.module_title)}.pdf")
            progress.progress(100, text="Study guide ready")
            st.session_state.update(data=data, report=report, pdf_path=str(pdf_path)); st.success(f"Created {pdf_path.name}")
        except Exception as exc: st.error(f"Generation failed: {exc}")
report = st.session_state.get("report"); data = st.session_state.get("data"); pdf_path = st.session_state.get("pdf_path")
if report and data and pdf_path:
    st.divider(); st.header(report.module_title); st.subheader("What This Module Is For"); st.write(report.executive_summary)
    c1, c2 = st.columns(2)
    with c1: st.subheader("Target roles"); st.write(", ".join(report.target_role) or "Not specified")
    with c2: st.subheader("Estimated time"); st.write(data.get("estimated_time", "Not stated"))
    st.subheader("Key learnings")
    for item in report.key_learnings: st.markdown(f"- {item}")
    st.subheader("Best practices and gotchas")
    for item in report.limits_and_best_practices: st.info(item)
    st.subheader("Knowledge-check concepts")
    for item in report.concept_qa:
        with st.expander(item.question): st.write(item.explanation)
    with open(pdf_path, "rb") as handle: st.download_button("⬇️ Download PDF Study Guide", handle.read(), file_name=Path(pdf_path).name, mime="application/pdf", width="stretch")


