"""
app.py
Streamlit UI for the AI Financial Report Analyzer.

Flow:
  1. User uploads a financial PDF (annual report / balance sheet / income statement)
  2. extractor.py pulls text + computes KPIs
  3. vectorstore.py indexes the text for later Q&A
  4. agents.py (CrewAI) turns the KPIs into an executive summary
  5. database.py persists everything so past reports can be revisited
"""

import os
import tempfile
import streamlit as st

from extractor import extract_text_and_tables, extract_financial_figures, compute_ratios
from vectorstore import build_or_update_index, search
from agents import run_financial_analysis
from database import init_db, save_report, get_all_reports, get_kpis_for_report, get_report_summary

st.set_page_config(page_title="AI Financial Report Analyzer", layout="wide")
init_db()

st.title("📊 AI Financial Report Analyzer")
st.caption("Upload annual reports, income statements, or balance sheets to extract KPIs and generate an executive summary.")

tab_analyze, tab_history, tab_chat = st.tabs(["Analyze Report", "Past Reports", "Ask Questions"])

# ---------------------- TAB 1: Analyze ----------------------
with tab_analyze:
    company_name = st.text_input("Company name", placeholder="e.g. Acme Corp")
    year = st.text_input("Report year", placeholder="e.g. 2025")
    uploaded_file = st.file_uploader("Upload financial report (PDF)", type=["pdf"])

    if uploaded_file and company_name and st.button("Run Analysis"):
        with st.spinner("Extracting data from PDF..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:    
                # we also have tempfile.temperorayfile : this just reads adn writes , doesnt provide location of file stored.
                #  but we we open pdf with pdfplumber etc , we need to give path not the binary file , so we use NamedTempFile
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

            text, tables = extract_text_and_tables(tmp_path)
            figures = extract_financial_figures(text)
            kpis = compute_ratios(figures)
            os.remove(tmp_path)

        if not kpis:
            st.warning("Could not extract recognizable financial figures. Try a different report.")
        else:
            st.subheader("Extracted KPIs")
            st.json(kpis)    
            # we can also use st.write(kpis) but it will put it in a string , so instead we use st.json() to make like a dictionary format better readable

            with st.spinner("Indexing document for future Q&A..."):
                build_or_update_index(text, source_name=f"{company_name}_{year}")

            with st.spinner("Running multi-agent financial analysis (this may take a minute)..."):
                summary = run_financial_analysis(company_name, kpis)

            st.subheader("Executive Summary")
            st.write(summary)

            report_id = save_report(company_name, uploaded_file.name, year, summary, kpis)
            st.success(f"Report saved (ID: {report_id})")



# ---------------------- TAB 2: History ----------------------
with tab_history:
    st.subheader("Previously Analyzed Reports")
    reports = get_all_reports()

    if not reports:
        st.info("No reports analyzed yet.")
    else:
        for report_id, name, file_name, yr, created_at in reports:
            with st.expander(f"{name} ({yr}) - {file_name}"):
                st.json(get_kpis_for_report(report_id))
                st.write(get_report_summary(report_id))

# ---------------------- TAB 3: Q&A over indexed reports ----------------------
with tab_chat:
    st.subheader("Ask Questions Across Uploaded Reports")
    query = st.text_input("Your question", placeholder="e.g. ask your query...")

    if query and st.button("Search"):
        results = search(query, k=4)
        if not results:
            st.info("No indexed reports yet. Analyze a report first.")
        else:
            for doc in results:
                st.markdown(f"**Source:** {doc.metadata.get('source', 'unknown')}")
                st.write(doc.page_content)
                st.divider()
