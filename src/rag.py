import os
from typing import List
import numpy as np
try:
    from sentence_transformers import SentenceTransformer
    import faiss
except Exception:
    # If dependencies are not installed yet, provide fallbacks; actual usage requires packages
    SentenceTransformer = None
    faiss = None

_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_model = None
_index = None
_documents: List[str] = []


def _ensure_model():
    global _model
    if _model is None:
        if SentenceTransformer is None:
            raise RuntimeError("SentenceTransformer not available (install sentence-transformers)")
        _model = SentenceTransformer(_MODEL_NAME)


def build_index(doc_texts: List[str]):
    """Build an in-memory FAISS index from a list of document texts (demo use)."""
    global _index, _documents
    _ensure_model()
    embeddings = _model.encode(doc_texts, convert_to_numpy=True)
    dim = embeddings.shape[1]
    if faiss is None:
        raise RuntimeError("faiss not available (install faiss-cpu)")
    _index = faiss.IndexFlatL2(dim)
    _index.add(embeddings)
    _documents = doc_texts


def retrieve(query: str, k: int = 5) -> List[str]:
    """Retrieve top-k documents similar to the query."""
    _ensure_model()
    if _index is None:
        return []
    q_emb = _model.encode([query], convert_to_numpy=True)
    D, I = _index.search(q_emb, k)
    results = []
    for idx in I[0]:
        if idx < len(_documents):
            results.append(_documents[idx])
    return results
