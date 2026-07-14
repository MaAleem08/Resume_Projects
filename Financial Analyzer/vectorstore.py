"""
vectorstore.py
Wraps a FAISS index so financial report text can be chunked, embedded,
and later retrieved for Q&A or year-over-year comparison.
"""

import os
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

INDEX_DIR = "faiss_index"
embeddings = OllamaEmbeddings(model="nomic-embed-text")


def build_or_update_index(text: str, source_name: str):
    """Split text into chunks, embed them, and add to (or create) the FAISS index."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.create_documents([text], metadatas=[{"source": source_name}])

    if os.path.exists(INDEX_DIR):
        store = FAISS.load_local(INDEX_DIR, embeddings, allow_dangerous_deserialization=True)
        store.add_documents(chunks)
    else:
        store = FAISS.from_documents(chunks, embeddings)

    store.save_local(INDEX_DIR)
    return store


def load_index():
    if not os.path.exists(INDEX_DIR):
        return None
    return FAISS.load_local(INDEX_DIR, embeddings, allow_dangerous_deserialization=True)


def search(query: str, k: int = 4):
    store = load_index()
    if store is None:
        return []
    results = store.similarity_search(query, k=k)
    return results
