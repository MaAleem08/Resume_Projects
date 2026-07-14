# AI-Powered Requirement Engineering and Documentation Automation Platform

Turns raw client/meeting notes into structured, classified requirements and an
auto-generated SRS document, using a small multi-agent pipeline built with
LangGraph and a local Ollama model.

## How it works

1. **Extractor agent** – splits raw notes into individual requirement statements.
2. **Classifier agent** – labels each requirement as Functional / Non-Functional,
   and checks it against a FAISS index of past requirements to flag likely duplicates.
3. **Reviewer agent** – flags requirements that are vague or ambiguous.
4. **Doc generator agent** – writes a short SRS document in markdown from the
   reviewed requirement list.

Everything is stored in a local SQLite database (`requirements.db`), so past
projects, requirements, and documents can be looked up later.

## Tech stack

- LangGraph – orchestrates the 4-agent pipeline
- Ollama (llama3.2) – local LLM used by every agent
- FAISS – vector similarity search for duplicate detection
- FastAPI – backend API
- Streamlit – frontend UI
- SQLite3 – persistence

## Setup

1. Install and start Ollama, then pull the model:
   ```
   ollama pull llama3.2
   ```

2. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Start the backend (from the `backend/` folder):
   ```
   uvicorn main:app --reload
   ```

4. Start the frontend (from the `frontend/` folder, in a separate terminal):
   ```
   streamlit run app.py
   ```

5. Open the Streamlit URL shown in the terminal, enter a project name and
   paste some raw requirement notes, then click "Generate Documentation".

## Project structure

```
req-doc-platform/
├── backend/
│   ├── main.py          # FastAPI app and routes
│   ├── agents.py        # LangGraph multi-agent pipeline
│   ├── vector_store.py  # FAISS similarity search
│   └── database.py      # SQLite persistence
├── frontend/
│   └── app.py           # Streamlit UI
├── requirements.txt
└── README.md
```
