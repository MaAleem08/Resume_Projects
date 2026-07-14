import streamlit as st
import requests

API_URL = "http://localhost:8000"

st.title("AI Requirement Engineering Assistant")
st.write(
    "Paste raw client/meeting notes below. The multi-agent pipeline will extract "
    "requirements, classify them, flag issues, and generate an SRS document."
)

project_name = st.text_input("Project name")
raw_text = st.text_area("Raw requirement notes", height=200)

if st.button("Generate Documentation"):
    if not project_name or not raw_text:
        st.warning("Please fill in both fields.")
    else:
        with st.spinner("Running multi-agent pipeline..."):
            try:
                res = requests.post(f"{API_URL}/process", json={
                    "project_name": project_name,
                    "raw_text": raw_text
                })
            except requests.exceptions.ConnectionError:
                res = None

        if res is None:
            st.error("Could not reach the API. Is the FastAPI server running?")
        elif res.status_code == 200:
            data = res.json()
            st.success(f"Done. Project ID: {data['project_id']}")

            st.subheader("Extracted Requirements")
            for r in data["requirements"]:
                st.write(f"**[{r['req_type']}]** {r['text']}")
                if r["issues"]:
                    st.caption(f"Flag: {r['issues']}")

            st.subheader("Generated SRS Document")
            st.markdown(data["document"])
        else:
            st.error("Something went wrong while processing the request.")

st.divider()
st.subheader("Past Projects")


if st.button("Click to see past projects"):
    with st.spinner("fetching past projects"):
        try:
            projects = requests.get(f"{API_URL}/projects").json()
            for p in projects:
                st.write(f"{p['id']} - {p['name']} ({p['created_at']})")
        except requests.exceptions.ConnectionError:
            st.info("Start the FastAPI server to view past projects.")
