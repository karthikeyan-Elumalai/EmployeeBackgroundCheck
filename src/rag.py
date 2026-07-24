import os
from typing import List

SentenceTransformer = None
faiss = None

try:
    from sentence_transformers import SentenceTransformer as _SentenceTransformer
    import faiss as _faiss
except Exception:
    _SentenceTransformer = None
    _faiss = None

SentenceTransformer = _SentenceTransformer
faiss = _faiss

_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_model = None
_index = None
_documents: List[str] = []


def _ensure_model():
    global _model
    if _model is None:
        if SentenceTransformer is None:
            return None
        _model = SentenceTransformer(_MODEL_NAME)
    return _model


def build_index(doc_texts: List[str]):
    """Build an in-memory index from a list of document texts (demo use)."""
    global _index, _documents
    _documents = doc_texts

    model = _ensure_model()
    if model is None or faiss is None:
        _index = None
        return

    embeddings = model.encode(doc_texts, convert_to_numpy=True)
    dim = embeddings.shape[1]
    _index = faiss.IndexFlatL2(dim)
    _index.add(embeddings)


def retrieve(query: str, k: int = 5) -> List[str]:
    """Retrieve top-k documents similar to the query."""
    if not _documents:
        return []

    model = _ensure_model()
    if model is None or faiss is None or _index is None:
        return _documents[:k]

    q_emb = model.encode([query], convert_to_numpy=True)
    _, I = _index.search(q_emb, k)
    results = []
    for idx in I[0]:
        if idx < len(_documents):
            results.append(_documents[idx])
    return results
