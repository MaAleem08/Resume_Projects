import os
import json
import faiss
import numpy as np
from langchain_community.embeddings import HuggingFaceEmbeddings


embeddings_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

# distance below this value is considered "same requirement, just reworded"
SIMILARITY_DISTANCE_THRESHOLD = 0.6

# where the FAISS index and the matching text list are saved on disk
INDEX_FILE = "faiss_index.bin"
TEXTS_FILE = "faiss_texts.json"


class RequirementVectorStore:
    def __init__(self):
        self.texts = []
        self.index = None
        self._load_from_disk()

    def _embed(self, text):
        vector = embeddings_model.embed_query(text)
        return np.array(vector, dtype="float32")

    def add(self, text):
        vector = self._embed(text)
        if self.index is None:
            self.index = faiss.IndexFlatL2(len(vector))
        self.index.add(np.array([vector]))
        self.texts.append(text)
        self._save_to_disk()

    def find_similar(self, text):
        if self.index is None or self.index.ntotal == 0:
            return None

        vector = self._embed(text)
        distances, indices = self.index.search(np.array([vector]), 1)

        if distances[0][0] < SIMILARITY_DISTANCE_THRESHOLD:
            return self.texts[indices[0][0]]
        return None

    def _save_to_disk(self):
        faiss.write_index(self.index, INDEX_FILE)
        with open(TEXTS_FILE, "w") as f:
            json.dump(self.texts, f)

    def _load_from_disk(self):
        if os.path.exists(INDEX_FILE) and os.path.exists(TEXTS_FILE):
            self.index = faiss.read_index(INDEX_FILE)
            with open(TEXTS_FILE, "r") as f:
                self.texts = json.load(f)


# single shared instance used across the app
vector_store = RequirementVectorStore()
